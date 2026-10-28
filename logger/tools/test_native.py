#!/usr/bin/env python3
"""Run the firmware's portable tests without hardware or a receiver."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    tests = sorted((ROOT / "tests").glob("*_test.cpp"))
    if len(tests) != 8:
        raise SystemExit(f"Expected 8 native tests, found {len(tests)}")
    with tempfile.TemporaryDirectory(prefix="accord-logger-tests-") as scratch:
        for source in tests:
            binary = Path(scratch) / source.stem
            subprocess.run([
                "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                str(source), "-o", str(binary),
            ], check=True)
            subprocess.run([str(binary)], check=True)
            print(f"PASS {source.name}", flush=True)


if __name__ == "__main__":
    main()
