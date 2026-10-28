"""Replay raw prefixes, spool immutable packets, call the existing DB writer.

The data path, and it is deliberately dull (UPLOAD_PROTOCOL §6):

    raw bytes -> cardconv.py -> tripd (UNCHANGED) -> tripload.py -> the DB

Two boundaries from the seed are structural here rather than remembered:

  * `tripd` is never modified and never reimplemented. It runs as itself, in a
    subprocess, over a file `cardconv.py` produced (see replay.py).
  * `accord_maintenance.db` is never written by us. `tripload.py` writes it --
    the database session is its sole writer, every write there carries a
    pre-write backup and an append-only audit row, and that stays true because
    we call it instead of opening sqlite3 ourselves.

A pass over a file that has not changed since the last pass does one sha256 and
stops, so running this every minute from a timer costs nothing.
"""
import copy
import json
import logging
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zoneinfo

from storage import atomic_json, digest, lock

LOG = logging.getLogger("accord-bridge")

# `# log.unit chip=E6614C311B3A3231 vehicle=accord-1 fw=0.6.0` (CARD_FORMAT §3).
LOG_UNIT = re.compile(rb"(?m)^#\s*log\.unit\s+chip=(\S+)\s+vehicle=(\S+)")
# tripload loads trips for ONE vehicle (VEHICLE_ID = 1). `accord-1` is what the
# real v0.6.0 cards carry; `accord01` is what tripd stamps into the packet.
ACCORD = (b"accord-1", b"accord01")


def measurement(packet):
    """A packet stripped of the facts that describe the REPLAY, not the drive.

    `clock_state()` reads the HOST's NTP state and uptime at the moment of
    close, so a second replay of identical bytes legitimately differs there.
    Everything else -- segmentation, timestamps, pulses, miles, warnings, raw
    rows -- must be identical or something has changed underneath us, which is
    what `process` refuses to publish silently.
    """
    value = copy.deepcopy(packet)
    for key in ("trusted", "ntp", "uptime_s", "source"):
        value.get("clock", {}).pop(key, None)
    return value


def packet_name(packet):
    stamp = packet["started_at"][:19].replace(":", "").replace("-", "")
    return f"trip-{stamp}-{packet['trip_id']}.json"


class Pipeline:
    def __init__(self, store, state, upstream, timezone="America/Los_Angeles",
                 tripload=None, database=None, loader_python=None):
        self.store = store
        self.state = Path(state)
        self.upstream = Path(upstream).resolve()
        self.timezone = timezone
        self.tripload = Path(tripload).resolve() if tripload else None
        self.database = Path(database).resolve() if database else None
        self.loader_python = loader_python or sys.executable
        # Half a configuration is the dangerous one: a spool that silently
        # never reaches a database looks exactly like a working bridge.
        if bool(self.tripload) != bool(self.database):
            raise ValueError("set both ACCORD_TRIPLOAD and ACCORD_DATABASE, or neither")
        # Checked once, here, rather than discovered per file. `cardconv.py`
        # resolves the zone itself, so a host without tzdata (a minimal Debian
        # install has none) would otherwise fail every pass with the same error
        # forever, one file at a time, long after startup looked healthy.
        try:
            zoneinfo.ZoneInfo(timezone)
        except (zoneinfo.ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"ACCORD_TZ={timezone!r} is not a zone this host "
                             f"knows ({exc}); on Debian: apt install tzdata") from exc
        for name in ("spool", "processed", "complete", "work"):
            (self.state / name).mkdir(parents=True, exist_ok=True)
        self.spool = self.state / "spool"
        # The tools' own bytes are part of the identity of a result. A tripd or
        # cardconv upgrade therefore re-replays every file, and any CHANGE in a
        # trip already published is reported rather than written (see process).
        self.version = digest(b"".join((self.upstream / name).read_bytes()
                                       for name in ("tripd", "cardconv.py"))
                              + timezone.encode()
                              + Path(__file__).read_bytes()
                              + Path(__file__).with_name("replay.py").read_bytes())

    def record_path(self, kind, unit, name):
        return self.state / kind / f"{unit}-{name}.json"

    # ---- completion is stated, never inferred --------------------------
    def mark_complete(self, unit, name, size, sha256=None):
        """Operator completion for legacy files; shares HTTP's locked seal.

        Byte count and optional source checksum prevent sealing a stale prefix.
        Automatic create-only completion arrives through the HTTP endpoint.
        """
        with lock(self.state / "pipeline.lock"):
            accepted, held = self.store.complete(unit, name, size, sha256, basis="operator")
            if not accepted:
                raise ValueError(f"completion says {size} bytes, file holds {held}")
            return self.store.completion(unit, name)

    # ---- one file -------------------------------------------------------
    def process(self, unit, name):
        if name.upper().startswith("BOOT_"):
            # UPLOAD_PROTOCOL rule 6. The firmware renames a pre-clock file
            # within seconds and uploads the dated name; the same rows under
            # two names would load as two sets of trips, and a BOOT_ file has
            # no trustworthy date anyway (`clock=none`). Bytes are kept.
            raise ValueError("provisional BOOT_ name: retained, not processed "
                             "(the renamed file carries these rows)")
        raw, seal = self.store.snapshot_status(unit, name)
        sha = digest(raw)
        complete = seal is not None
        if complete:
            if seal["bytes"] != len(raw) or seal["sha256"] != sha:
                raise ValueError("file grew after it was marked complete; review required")
        signature = [sha, self.version, complete]
        record_path = self.record_path("processed", unit, name)
        previous = json.loads(record_path.read_text()) if record_path.exists() else {}
        if previous.get("signature") == signature:
            return previous, []

        # Preserve all raw bytes, but derive trips only from complete LF-ended
        # rows, even on sealed files. Report any held tail for explicit recovery.
        prefix = raw[:raw.rfind(b"\n") + 1]
        if not prefix:
            return {"pending": "waiting for a complete line"}, []
        lines = prefix.splitlines()
        if lines[0].startswith(b"# accord-log/"):
            if lines[0] != b"# accord-log/1":
                # CARD_FORMAT rule 2: a reader that does not recognise the
                # token stops rather than guesses. The bytes are still here
                # when this bridge learns the new version.
                raise ValueError(f"unsupported card format {lines[0]!r}; bytes retained")
            if b"# log.end" not in lines:
                # A truncated header is detectable precisely because rule 5
                # gives the block a terminator. Wait for the rest.
                return {"pending": "waiting for the rest of the card header"}, []
        identity = LOG_UNIT.search(prefix)
        if identity:
            if identity[1].decode().lower() != unit.lower():
                raise ValueError(f"card says chip={identity[1].decode()} but it "
                                 f"arrived as unit {unit}")
            if identity[2] not in ACCORD:
                raise ValueError(f"vehicle {identity[2].decode()} is not the "
                                 f"Accord tripload loads; bytes retained")

        if name.startswith("U_"):
            upload = re.search(rb"(?m)^# log.upload id=([0-9a-f]{32}) policy=create-only$",
                               prefix.split(b"# log.end\n", 1)[0])
            if not upload or name != f"U_{upload[1].decode()}.CSV" or not identity:
                raise ValueError("upload identity does not match card header; bytes retained")

        with tempfile.TemporaryDirectory(dir=self.state / "work") as work:
            card = Path(work) / name
            card.write_bytes(prefix)
            out = Path(work) / "result.json"
            cmd = [sys.executable, "-I", "-B", str(Path(__file__).with_name("replay.py")),
                   str(card), "--upstream", str(self.upstream), "--unit", unit,
                   "--tz", self.timezone, "--out", str(out)]
            if complete:
                cmd.append("--complete")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode:
                raise ValueError((result.stderr or result.stdout).strip()[-3000:])
            replayed = json.loads(out.read_text())
        packets = replayed.pop("packets")
        if replayed.get("held"):
            # Preserve already-published packets, but publish no new ones from
            # disputed evidence. Do not cache a successful processing signature.
            return {"bytes": len(raw), "trips": previous.get("trips", []),
                    "trailing_bytes_held": len(raw) - len(prefix), **replayed}, []

        def published(trip_id):
            """The spooled packet for this trip, whatever stamp its name holds."""
            return next(iter(self.spool.glob(f"trip-*-{trip_id}.json")), None)

        # Validate the WHOLE batch before publishing any of it. A new anchor or
        # a new tripd must not quietly rewrite a trip that is already in the
        # database -- the DB session owns that decision, and a refit is its job
        # to run. Nothing is written in the loop below.
        identities = [p["trip_id"] for p in packets]
        for packet in packets:
            # Matched on the TRIP ID, not on the file name. The name carries
            # `started_at`, so a replay that moved a trip's start would miss
            # itself here and write a second file for one trip -- which
            # tripload would dedupe on trip_uuid, hiding exactly the change
            # this guard exists to report.
            old = published(packet["trip_id"])
            if old and measurement(json.loads(old.read_text())) != measurement(packet):
                raise ValueError(f"replay changes already-published trip "
                                 f"{packet['trip_id']}; DB-owner review required")
        missing = set(previous.get("trips", [])) - set(identities)
        if missing:
            raise ValueError(f"replay drops {len(missing)} already-published "
                             f"trip(s); DB-owner review required")

        fresh = []
        for packet in packets:
            if published(packet["trip_id"]) is None:
                atomic_json(self.spool / packet_name(packet), packet)
                fresh.append(packet)
        record = {"signature": signature, "bytes": len(raw),
                  "trailing_bytes_held": len(raw) - len(prefix),
                  "trips": identities, "complete": complete, **replayed}
        atomic_json(record_path, record)
        LOG.info("%s/%s: %d bytes, %d trip(s), %d new%s", unit, name, len(raw),
                 len(packets), len(fresh),
                 f", pending: {record['pending']}" if record.get("pending") else "")
        return record, fresh

    # ---- the database, through its own writer ---------------------------
    def load(self):
        if self.tripload is None or not any(self.spool.glob("trip-*.json")):
            return None
        result = subprocess.run(
            [self.loader_python, str(self.tripload), "--db", str(self.database),
             "--spool", str(self.spool), "--quiet"],
            capture_output=True, text=True, timeout=600)
        if result.returncode:
            raise ValueError(f"tripload failed ({result.returncode}): "
                             + (result.stderr or result.stdout).strip()[-3000:])
        out = result.stdout.strip()
        if out:
            LOG.info("tripload: %s", out)
        return out

    # ---- one pass -------------------------------------------------------
    def once(self):
        """Every held file, then the database. Idempotent; safe on a timer."""
        errors, files, fresh = [], {}, []
        with lock(self.state / "pipeline.lock"):
            for unit, name in self.store.files():
                try:
                    record, new = self.process(unit, name)
                    files[f"{unit}/{name}"] = {
                        "bytes": record.get("bytes"),
                        "trailing_bytes_held": record.get("trailing_bytes_held", 0),
                        "trips": len(record.get("trips", [])),
                        "pending": record.get("pending")}
                    fresh.extend(new)
                except (ValueError, OSError, subprocess.SubprocessError) as exc:
                    message = f"{unit}/{name}: {exc}"
                    errors.append(message)
                    files[f"{unit}/{name}"] = {"error": str(exc)}
                    LOG.error("deferred: %s", message)
            loaded = None
            try:
                loaded = self.load()
            except (ValueError, OSError, subprocess.SubprocessError) as exc:
                # The spool is durable and tripload is idempotent, so a failed
                # load costs a retry and never a trip.
                errors.append(f"tripload: {exc}")
                LOG.error("database load deferred: %s", exc)
        summary = {"errors": errors, "files": files,
                   "spooled": len(list(self.spool.glob("trip-*.json"))),
                   "database_loading": self.tripload is not None,
                   "tripload": loaded, "tools_version": self.version[:12]}
        atomic_json(self.state / "status.json", summary)
        return summary, fresh
