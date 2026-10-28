#!/usr/bin/env python3
"""accord-bridge -- receive raw card rows over WiFi and turn them into trips.

    ACCORD_STATE_DIR=/var/lib/accord-bridge \
    ACCORD_UPSTREAM=/opt/accord-bridge/upstream \
    ACCORD_UPLOAD_TOKEN=... ./accord_bridge.py

The fifth service in a house pattern (`carport-bridge`, `ir-bridge`,
`rftx-bridge`, `heater-sense`): /opt install, own venv, own service user,
EnvironmentFile, StateDirectory, Restart=always. See tools/accord-bridge.service.

Two threads and no cleverness:

  * the HTTP server answers `accord-upload/1` and does nothing else. An append
    is an fsync and a reply; it never waits for trip building, because the
    Pico's first duty is to log and a POST must cost it one bounded step.
  * a worker converts what has arrived, feeds `tripd`, spools packets and calls
    `tripload.py`. It runs on a timer AND after a quiet period following the
    last append, so a drive's upload is processed promptly without re-running
    over a file that is still being written.

Both are idempotent. The process can be killed at any instant: the raw bytes
are fsynced prefixes of the card file, the spool is write-rename, and every
derived step is recomputed from the bytes on the next pass.

CONFIGURATION (all via environment, so one unit file suits any host)

    ACCORD_STATE_DIR     state root; raw/ spool/ processed/ complete/ work/
    ACCORD_UPSTREAM      directory holding `tripd` and `cardconv.py`, verbatim
    ACCORD_UPLOAD_TOKEN  shared bearer token (UPLOAD_PROTOCOL §4)
    ACCORD_BIND, ACCORD_PORT         default 0.0.0.0:8086
    ACCORD_TZ            zone `wall` is rendered in (default America/Los_Angeles)
    ACCORD_TRIPLOAD      path to honda/service/tripload.py   } both or neither
    ACCORD_DATABASE      path to accord_maintenance.db        }
    ACCORD_LOADER_PYTHON interpreter for tripload, if not this venv's
    ACCORD_PASS_SECONDS  pass interval, default 60
    ACCORD_QUIET_SECONDS settle time after the last append, default 15
    MQTT_HOST/USERNAME/PASSWORD      optional events; absent = no broker, no events

With ACCORD_TRIPLOAD unset the bridge receives, builds and spools trips and
loads nothing -- which is the right configuration on a host where
`accord_maintenance.db` does not live yet. The spool is durable and tripload is
idempotent, so pointing it at the database later loads everything held.
"""
import json
import logging
import os
from pathlib import Path
import signal
import sys
import threading
import time

# sys.path bootstrap, before the sibling imports below. `python3 -I` (and
# `-P`) do NOT put the script's own directory on sys.path, so `import storage`
# fails under the isolated interpreter that tests/run.sh and anything
# security-minded will reach for. An explicit path is one line and removes a
# whole class of "works here, not there".
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from events import Events, broker_from_env
from pipeline import Pipeline
from server import serve
from storage import Store

LOG = logging.getLogger("accord-bridge")


class Worker(threading.Thread):
    """Runs pipeline passes. One at a time, never on the HTTP thread."""

    def __init__(self, pipeline, events, interval=60.0, quiet=15.0):
        super().__init__(name="pipeline", daemon=True)
        self.pipeline, self.events = pipeline, events
        self.interval, self.quiet = interval, quiet
        self.wake = threading.Event()
        self.halt = threading.Event()
        self.touched_at = 0.0
        self.last = {"ok": None, "note": "no pass yet"}

    def touch(self):
        """Called from the HTTP thread after a successful append."""
        self.touched_at = time.monotonic()
        self.wake.set()

    def run(self):
        while not self.halt.is_set():
            woken = self.wake.wait(self.interval)
            if self.halt.is_set():
                break
            self.wake.clear()
            if woken:
                # Let a burst of 4 KiB chunks land before converting the file.
                # Without this every chunk of a 4 MB upload would start a
                # replay of everything received so far.
                while time.monotonic() - self.touched_at < self.quiet:
                    if self.halt.wait(0.5):
                        return
            self.once()

    def once(self):
        started = time.time()
        try:
            summary, fresh = self.pipeline.once()
        except Exception as exc:                        # noqa: BLE001
            # A pass must never kill the receiver: the bytes are the record and
            # the next pass recomputes everything from them.
            LOG.exception("pipeline pass failed")
            self.last = {"ok": False, "note": f"pass failed: {exc}",
                         "at": int(started)}
            return
        for packet in fresh:
            self.events.trip(packet)
        self.events.status(summary)
        self.last = {"ok": not summary["errors"], "at": int(started),
                     "seconds": round(time.time() - started, 2), **summary}
        if fresh:
            LOG.info("%d new trip(s), %.3f mi", len(fresh),
                     sum(p["vss"]["miles"] for p in fresh))

    def stop(self):
        self.halt.set()
        self.wake.set()


def configure(env=os.environ):
    state = Path(env.get("ACCORD_STATE_DIR") or "/var/lib/accord-bridge")
    upstream = env.get("ACCORD_UPSTREAM")
    if not upstream:
        # Running from a checkout: tools/stage-upstream.sh fills ./upstream/.
        guess = Path(__file__).resolve().parent.parent / "upstream"
        if not (guess / "tripd").exists():
            raise SystemExit(
                "set ACCORD_UPSTREAM to a directory holding `tripd` and "
                "`cardconv.py` (tools/stage-upstream.sh makes one from a "
                "checkout; tools/pack.sh ships one in the tarball)")
        upstream = guess
    store = Store(state / "raw")
    pipeline = Pipeline(
        store, state, upstream,
        timezone=env.get("ACCORD_TZ") or "America/Los_Angeles",
        tripload=env.get("ACCORD_TRIPLOAD") or None,
        database=env.get("ACCORD_DATABASE") or None,
        loader_python=env.get("ACCORD_LOADER_PYTHON") or None)
    return state, store, pipeline


def main(env=os.environ):
    logging.basicConfig(
        level=logging.INFO, stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(message)s" if not env.get("INVOCATION_ID")
        else "%(levelname)s %(message)s")      # journald stamps its own lines
    try:
        state, store, pipeline = configure(env)
    except ValueError as exc:
        # A bad EnvironmentFile is not a crash to debug from a traceback.
        # `Restart=always` will keep trying, so what lands in the journal every
        # five seconds should be one readable line saying what to fix.
        raise SystemExit(f"configuration error: {exc}") from None
    token = env.get("ACCORD_UPLOAD_TOKEN")
    if not token:
        LOG.warning("no ACCORD_UPLOAD_TOKEN: every client is accepted")
    events = Events(broker_from_env(env), env.get("ACCORD_TOPIC_PREFIX", "accord"))
    worker = Worker(pipeline, events,
                    interval=float(env.get("ACCORD_PASS_SECONDS") or 60),
                    quiet=float(env.get("ACCORD_QUIET_SECONDS") or 15))

    def health():
        held = [f"{u}/{n}" for u, n in store.files()]
        return {"ok": worker.last.get("ok") is not False,
                "protocol": "accord-upload/1", "held": held,
                "database_loading": pipeline.tripload is not None,
                "last_pass": worker.last}

    server = serve(store.root, token,
                   int(env.get("ACCORD_PORT") or 8086),
                   env.get("ACCORD_BIND") or "0.0.0.0",
                   on_append=worker.touch, health=health)

    def shutdown(signum, _frame):
        LOG.info("stopping on signal %d", signum)
        # From a signal handler: shutdown() must not run on this thread, it
        # would deadlock against serve_forever.
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    worker.start()
    worker.touch()           # one pass at startup: recover anything held
    events.online()
    LOG.info("accord-upload/1 on %s:%d -> %s  (upstream %s, tools %s%s)",
             server.server_address[0], server.server_address[1], state,
             pipeline.upstream, pipeline.version[:12],
             "" if pipeline.tripload else ", DB loading off")
    try:
        server.serve_forever()
    finally:
        worker.stop()
        worker.join(timeout=30)
        server.server_close()
        events.stop()
        LOG.info("stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
