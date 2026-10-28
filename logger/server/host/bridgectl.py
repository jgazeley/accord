#!/usr/bin/env python3
"""bridgectl -- look at what the bridge holds, and state when a file is done.

    ./bridgectl.py status
    ./bridgectl.py complete E6614C311B3A3231 20261024_183345.CSV --bytes 36976
    ./bridgectl.py pass

Reads the same environment as the service (ACCORD_STATE_DIR, ACCORD_UPSTREAM,
...), so on the host it is run as the service user:

    sudo -u accord-bridge env $(cat /etc/accord-bridge.env | grep -v '^#') \
        /opt/accord-bridge/.venv/bin/python /opt/accord-bridge/host/bridgectl.py status

New create-only recordings complete automatically over HTTP. `complete` remains
an operator assertion for legacy files with no immutable upload ID, after their
original byte count/checksum is known. Network silence is never completion.
Both paths use the same durable seal and forbid subsequent append.
"""
import argparse
import json
import os
from pathlib import Path
import sys

# sys.path bootstrap, before the sibling imports below. `python3 -I` (and
# `-P`) do NOT put the script's own directory on sys.path, so `import storage`
# fails under the isolated interpreter that tests/run.sh and anything
# security-minded will reach for. An explicit path is one line and removes a
# whole class of "works here, not there".
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from accord_bridge import configure
from storage import digest


def status(state, store, pipeline, _args):
    held = []
    for unit, name in store.files():
        path = store.path(unit, name)
        record = pipeline.record_path("processed", unit, name)
        seal = store.completion(unit, name)
        row = {"unit": unit, "file": name, "bytes": path.stat().st_size,
               "complete": seal is not None}
        if record.exists():
            done = json.loads(record.read_text())
            row["trips"] = len(done.get("trips", []))
            row["pending"] = done.get("pending")
            row["processed_bytes"] = done.get("bytes")
        held.append(row)
    out = {"state": str(state), "upstream": str(pipeline.upstream),
           "tools_version": pipeline.version[:12],
           "database_loading": pipeline.tripload is not None,
           "spooled": len(list(pipeline.spool.glob("trip-*.json"))),
           "held": held}
    path = state / "status.json"
    if path.exists():
        out["last_pass"] = json.loads(path.read_text())
    print(json.dumps(out, indent=2))
    return 0


def complete(state, store, pipeline, args):
    raw = store.snapshot(args.unit, args.file)
    if args.bytes != len(raw):
        print(f"refusing: you said {args.bytes} bytes, the file holds {len(raw)}."
              f"\nIt is still growing, or you read an older number. Current "
              f"sha256 {digest(raw)}.", file=sys.stderr)
        return 1
    receipt = pipeline.mark_complete(args.unit, args.file, args.bytes, args.sha256)
    print(f"{args.unit}/{args.file} marked complete: "
          f"{receipt['bytes']} bytes, sha256 {receipt['sha256']}")
    print("run `bridgectl.py pass` or wait for the next pass to close the "
          "trailing trip")
    return 0


def run_pass(_state, _store, pipeline, _args):
    summary, fresh = pipeline.once()
    print(json.dumps(summary, indent=2))
    for packet in fresh:
        print(f"new trip {packet['started_at']} {packet['vss']['miles']:.3f} mi "
              f"{packet['close_reason']}")
    return 1 if summary["errors"] else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--state", help="override ACCORD_STATE_DIR")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="what is held, processed and spooled")
    done = sub.add_parser("complete", help="state that a file is the whole card file")
    done.add_argument("unit")
    done.add_argument("file")
    done.add_argument("--bytes", type=int, required=True,
                      help="the byte count you are asserting is final")
    done.add_argument("--sha256", help="optional: must match, if given")
    sub.add_parser("pass", help="run one pipeline pass now")
    args = parser.parse_args(argv)

    env = dict(os.environ)
    if args.state:
        env["ACCORD_STATE_DIR"] = args.state
    state, store, pipeline = configure(env)
    return {"status": status, "complete": complete,
            "pass": run_pass}[args.command](state, store, pipeline, args)


if __name__ == "__main__":
    sys.exit(main())
