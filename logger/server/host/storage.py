"""Durable raw bytes, one append-only file per (unit, file). No trip logic.

The layout is the reference receiver's, deliberately: `<root>/<unit>/<name>`,
so a received tree and the reference's inbox are the same thing on disk and
`tests/check_protocol.py` can run the reference's suite against this store.
Locks live in `<root>/.locks/`, which `files()` skips for free because a unit
directory has to match UNIT_RE and a dot-directory never will.

Everything here is written so that losing power at any instant leaves a true
prefix of the card file and nothing else: append, flush, fsync, and fsync the
directory when its contents changed. The upload protocol's whole promise --
"an interrupted upload must cost nothing" -- is only as good as this file.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

# A unit is an RP2040 chip id and a file is a card file name. Both come off the
# wire and both are used to build a path, so both are validated rather than
# trusted. Identical to the reference receiver's pair.
UNIT_RE = re.compile(r"[0-9A-Fa-f]{16}")
FILE_RE = re.compile(r"[0-9A-Za-z_.-]{1,64}")
MAX_CHUNK = 1 << 20          # a chunk much larger than the Pico's is a mistake


def validate(unit, name):
    if not UNIT_RE.fullmatch(unit):
        raise ValueError("unit must be 16 hex digits")
    # `.` and `..` match FILE_RE -- a dot is a legal name character -- and then
    # name a directory rather than a file. The reference receiver accepts them
    # and breaks on `open("ab")`; we refuse them here, once, for both paths.
    if not FILE_RE.fullmatch(name) or name in (".", ".."):
        raise ValueError("file name rejected")


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_json(path, value):
    """Write-rename-fsync. A reader never sees a half-written record."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
        sync_dir(path.parent)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


@contextmanager
def lock(path, blocking=True):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        yield


def digest(data):
    return hashlib.sha256(data).hexdigest()


class Store:
    def __init__(self, root):
        self.root = Path(root)
        self.locks = self.root / ".locks"
        self.locks.mkdir(parents=True, exist_ok=True)
        sync_dir(self.root)

    def path(self, unit, name):
        validate(unit, name)
        return self.root / unit / name

    def locked(self, unit, name):
        validate(unit, name)
        # Readable on purpose: an operator who finds a stuck lock should be able
        # to see which file it belongs to without hashing anything.
        return lock(self.locks / f"{unit}-{name}.lock")

    def size(self, unit, name):
        return self.status(unit, name)[0]

    def status(self, unit, name):
        """Offset and seal from one locked observation."""
        with self.locked(unit, name):
            target = self.path(unit, name)
            return (target.stat().st_size if target.is_file() else 0,
                    self.completion(unit, name) is not None)

    def completion_path(self, unit, name):
        validate(unit, name)
        return self.root / ".completion" / unit / (name + ".json")

    def completion(self, unit, name):
        """Read under the file lock when coupled with bytes or append.

        Recognize old operator seals so upgrading cannot reopen a file.
        New seals use the reference receiver's schema and raw/.completion path.
        """
        path = self.completion_path(unit, name)
        if path.exists():
            seal = json.loads(path.read_text())
            if seal.get("unit") != unit or seal.get("file") != name:
                raise ValueError("completion identity mismatch")
        else:
            legacy = self.root.parent / "complete" / f"{unit}-{name}.json"
            if not legacy.exists():
                return None
            seal = json.loads(legacy.read_text())
        if (not isinstance(seal, dict) or not isinstance(seal.get("bytes"), int) or seal["bytes"] < 0
                or not re.fullmatch(r"[0-9a-f]{64}", str(seal.get("sha256", "")))):
            raise ValueError("invalid completion marker")
        return seal

    def complete(self, unit, name, size, sha256=None, basis="client-create-only"):
        """Seal bytes under the SAME lock as append; retry durability too."""
        with self.locked(unit, name):
            target = self.path(unit, name)
            held = target.stat().st_size if target.is_file() else 0
            if size != held or not target.is_file():
                return False, held
            prior = self.completion(unit, name)
            with target.open("rb") as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
                os.fsync(stream.fileno())
            if sha256 is not None and sha256 != actual:
                raise ValueError("completion SHA-256 does not match received bytes")
            if prior and (prior["bytes"] != held or prior["sha256"] != actual):
                raise ValueError("file changed after completion")
            sync_dir(target.parent)
            sync_dir(self.root)
            marker = self.completion_path(unit, name)
            if not marker.exists():
                atomic_json(marker, {"unit": unit, "file": name, "bytes": held,
                                     "sha256": actual, "basis": basis})
            # Retry these if the marker rename succeeded but a barrier failed.
            sync_dir(marker.parent)
            sync_dir(marker.parent.parent)
            sync_dir(self.root)
            return True, held

    def append(self, unit, name, start, body):
        """Append iff `start` is exactly what we hold. (new_size, held) or (None, held).

        The one piece of real logic in the protocol: a disagreement writes
        nothing and reports the true size, so it self-corrects on the next
        attempt instead of leaving a gap or a double write.
        """
        with self.locked(unit, name):
            target = self.path(unit, name)
            held = target.stat().st_size if target.is_file() else 0
            if start != held or self.completion(unit, name) is not None:
                return None, held
            if not target.parent.exists():
                target.parent.mkdir()
                sync_dir(self.root)
            with target.open("ab") as stream:
                stream.write(body)
                stream.flush()
                os.fsync(stream.fileno())
            sync_dir(target.parent)
            sync_dir(self.root)
            return held + len(body), held + len(body)

    def snapshot(self, unit, name):
        """The bytes held right now, read under the lock so it is a prefix."""
        return self.snapshot_status(unit, name)[0]

    def snapshot_status(self, unit, name):
        """Read bytes and completion together; HTTP completion can race replay."""
        with self.locked(unit, name):
            return self.path(unit, name).read_bytes(), self.completion(unit, name)

    def files(self):
        if not self.root.exists():
            return
        for unit in sorted(self.root.iterdir()):
            if unit.is_dir() and UNIT_RE.fullmatch(unit.name):
                for path in sorted(unit.iterdir()):
                    if path.is_file() and FILE_RE.fullmatch(path.name):
                        yield unit.name, path.name
