"""An adapter around UNMODIFIED `cardconv.py` and `tripd`. No trip rules here.

ARCHITECTURE.md: "One trip builder, two delivery paths, no drift." So this file
converts and feeds, and every decision about what a trip IS stays in `tripd`,
which has three regression suites and a 64-log replay behind it. If something
here looks like it is making a trip decision, it is a bug.

Run as a subprocess (see pipeline.py) for two reasons: `cardconv.py` reports
errors with `sys.exit`, and a conversion failure must not be able to stop HTTP
ingestion. The card bytes are the record; a trip is a re-derivable opinion
about them.

WHY A PREFIX IS SAFE TO REPLAY
------------------------------
A received file grows, so this runs again on a longer prefix of the same bytes.
Measured on the real 3-trip card of 2026-10-19 (`tests/check_equivalence.py`
re-measures it): feeding 30/50/75/90/100% of the lines emits a stable PREFIX of
the final trip list, and the final `close("log_end")` adds nothing when the
file ends after the last trip closed. tripd's own close rules -- engine_off and
the rest -- close a finished trip from the data, without needing EOF. So a
growing file publishes finished trips and leaves the open one open, which is
the behaviour the upload protocol needs and did not have to be invented.

The one thing that is NOT stable under growth is the wall-clock anchor when it
comes from `# TIME` notes: cardconv picks the LAST note, so a later note moves
every timestamp in the file. A file with no `log.file`/filename anchor is
therefore left pending until it is explicitly complete. v0.6.0 cards carry the
anchor in their first bytes, so this is the old-format path only.
"""
import argparse
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import uuid

# sys.path bootstrap, before the sibling imports below. `python3 -I` (and
# `-P`) do NOT put the script's own directory on sys.path, so `import storage`
# fails under the isolated interpreter that tests/run.sh and anything
# security-minded will reach for. An explicit path is one line and removes a
# whole class of "works here, not there".
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from storage import atomic_json

# Stable per-(unit, file, position) trip identity. Fixed constant: it is part of
# the identity function, so changing it would re-identify every trip ever
# loaded. See `stabilise` below for why identities have to be ours at all.
NAMESPACE = uuid.UUID("8a41ad36-eeb5-4b6b-94d9-4662a38c9be7")


def load(path, name):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def convert(card, upstream, timezone):
    """Run cardconv exactly as a hand-pulled card is run. Returns the CSV path.

    The output NAME is cardconv's own choice (`card_<local date>_<time>.csv`)
    and is not overridden, because `tripd.file_date()` takes a log's date from
    its name: an --out of our own invention would re-date every trip. The card
    is alone in a work directory so the new file is unambiguous.
    """
    result = subprocess.run(
        [sys.executable, "-I", str(upstream / "cardconv.py"), str(card),
         "--tz", timezone], capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise ValueError((result.stderr or result.stdout).strip())
    made = [p for p in card.parent.glob("card_*.csv") if p != card]
    if len(made) != 1:
        raise ValueError(f"cardconv produced {len(made)} dated CSVs, expected 1")
    return made[0], result


def stabilise(packets, unit, name):
    """Give every packet an identity derived from its position, not from luck.

    `tripd` mints a fresh uuid4 per trip per run, which is right for a live
    recorder and wrong for a replay: the same trip replayed on a longer prefix
    would arrive at `tripload` as a second trip and the miles would be counted
    twice. tripload is idempotent on `trip.trip_uuid`, so the fix is to make
    the uuid a function of (unit, file, index) -- stable across retries,
    restarts and redeliveries.

    Nothing else is touched. Segmentation, timestamps, counts, calibration and
    miles are all still exactly what tripd said.
    """
    epochs = {}
    for index, packet in enumerate(packets):
        epoch = packet["counter_epoch"]
        if epoch not in epochs:
            epochs[epoch] = str(uuid.uuid5(
                NAMESPACE, f"{unit}/{name}/epoch/{len(epochs)}"))
        packet["counter_epoch"] = epochs[epoch]
        packet["trip_id"] = str(uuid.uuid5(NAMESPACE, f"{unit}/{name}/trip/{index}"))
    return packets


def replay(card, upstream, unit, timezone, complete=False):
    converter = load(upstream / "cardconv.py", "cardconv")
    kinds = converter.scan(card)
    anchor, notes = converter.anchors_from(kinds, card.name)
    if anchor is None and not notes:
        return {"packets": [], "pending": "no absolute time anchor; raw evidence held",
                "held": True}
    if anchor is None and not complete:
        # See the module docstring: a TIME-note anchor still moves.
        return {"packets": [], "pending": "no stable time anchor yet; "
                "waiting for more bytes or an explicit completion"}
    converted, conversion = convert(card, upstream, timezone)
    if "WARNING:" in conversion.stderr:
        return {"packets": [], "pending": "clock conflict; owner review required",
                "warnings": conversion.stderr.strip(),
                "conversion": conversion.stdout.strip(), "held": True}

    tripd = load(upstream / "tripd", "tripd")
    packets = []
    tracker = tripd.Tracker(unit, "pico-card", {}, packets.append)
    tracker.set_source(str(converted))
    with converted.open() as stream:
        for line in stream:
            tracker.feed(line.rstrip("\n"))
    pending = "open trip at the end of the received bytes" if tracker.trip else None
    if complete:
        # Only an explicitly complete file gets tripd's EOF close, for the same
        # reason `tripd --once` gets it: the file has ended, so the trip has.
        tracker.close("log_end")
        pending = None
    return {"packets": stabilise(packets, unit, card.name),
            "pending": pending,
            "conversion": conversion.stdout.strip(),
            "warnings": conversion.stderr.strip()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("card", type=Path)
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--unit", required=True)
    parser.add_argument("--tz", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--complete", action="store_true")
    args = parser.parse_args()
    atomic_json(args.out, replay(args.card, args.upstream, args.unit,
                                 args.tz, args.complete))


if __name__ == "__main__":
    main()
