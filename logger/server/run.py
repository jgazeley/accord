#!/usr/bin/env python3
"""Standalone raw-upload -> trip-JSON service; no database integration."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent

def main():
    env = dict(os.environ)
    token = env.get("ACCORD_UPLOAD_TOKEN", "")
    if not token or token == "REPLACE_WITH_PRIVATE_RANDOM_TOKEN":
        raise SystemExit("Set a private ACCORD_UPLOAD_TOKEN before starting the receiver")
    if any(env.get(k) for k in ("ACCORD_TRIPLOAD", "ACCORD_DATABASE", "ACCORD_LOADER_PYTHON")):
        raise SystemExit("Database loading is not supported by this standalone entry point")
    if not env.get("ACCORD_STATE_DIR"):
        raise SystemExit("Set ACCORD_STATE_DIR to private persistent storage outside the checkout")
    state = Path(env["ACCORD_STATE_DIR"]).resolve()
    repo = ROOT.parents[1]
    if state == repo or repo in state.parents:
        raise SystemExit("Runtime state must be outside the source repository")
    env.setdefault("ACCORD_BIND", "127.0.0.1")
    env["ACCORD_UPSTREAM"] = str(ROOT / "upstream")
    sys.path.insert(0, str(ROOT / "host"))
    from accord_bridge import main as serve
    serve(env)

if __name__ == "__main__":
    main()
