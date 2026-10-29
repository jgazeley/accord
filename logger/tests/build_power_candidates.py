#!/usr/bin/env python3
"""Compile both LRA-05 profiles with the existing helper; no secrets or flash.

Use an isolated source copy for the opt-in config; never change the checkout's
manual default. Build manifests record every effective source/config hash.
"""
from pathlib import Path
import argparse
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    for mode in ("manual", "qualified"):
        with tempfile.TemporaryDirectory(prefix="lra05-profile-") as scratch:
            root = Path(scratch) / "logger"
            (root / "tools").mkdir(parents=True)
            helper = root / "tools/build_candidate.py"
            shutil.copy2(ROOT / "tools/build_candidate.py", helper)
            firmware = root / "firmware/accord-logger"
            firmware.mkdir(parents=True)
            for source in (ROOT / "firmware/accord-logger").iterdir():
                if source.suffix in (".ino", ".cpp", ".h") and source.name != "secrets.h":
                    shutil.copy2(source, firmware / source.name)
            config = firmware / "power_config.h"
            if mode == "qualified":
                text = config.read_text()
                assert text.count("#define LOGGER_POWER_QUALIFIED 0") == 1
                config.write_text(text.replace("#define LOGGER_POWER_QUALIFIED 0", "#define LOGGER_POWER_QUALIFIED 1"))
            print(f"Building {mode}: LOGGER_POWER_QUALIFIED={int(mode == 'qualified')}", flush=True)
            subprocess.run([sys.executable, str(helper), "--build-dir", str(output / f"build-lra05-{mode}")], check=True)


if __name__ == "__main__":
    main()
