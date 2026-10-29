#!/usr/bin/env python3
"""Synthetic power metadata compatibility against the unchanged public converter."""
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ROWS = ["1004,0,0.00,0,0.00,0,1,1850,1844,1861,160,2714,0,0",
        "2004,1,1.00,1,1.00,30,0,1851,1843,1860,160,2713,0,1"]


def main():
    with tempfile.TemporaryDirectory(prefix="lra05-converter-") as scratch:
        directory = Path(scratch)
        emitter = directory / "header"
        subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                        str(ROOT / "tests/card_header_test.cpp"), "-o", str(emitter)], check=True)
        for mode in ("legacy", "manual", "qualified"):
            for situation in ("dated", "boot", "renamed", "reinserted"):
                name = "/BOOT_540.CSV" if situation in ("boot", "renamed") else "/20261029_120000.CSV"
                header = subprocess.check_output([str(emitter), "--emit", name, mode], text=True)
                if mode == "legacy":
                    header = "\n".join(line for line in header.splitlines() if not line.startswith("# log.power")) + "\n"
                if situation == "renamed":
                    header += "# log.rename from=/BOOT_540.CSV to=/20261029_120000.CSV at_ms=6042\n"
                # Reinserted file has its own newly rendered full header; the
                # converter must not rely on metadata from a previous file.
                source = directory / f"{mode}-{situation}.CSV"
                output = directory / f"{mode}-{situation}.csv"
                source.write_text(header + "\n".join(ROWS) + "\n")
                command = [sys.executable, "-B", str(ROOT / "server/upstream/cardconv.py"),
                           str(source), "--out", str(output), "--tz", "UTC"]
                if situation == "boot":
                    command += ["--no-wall"]
                subprocess.run(command, check=True, capture_output=True, text=True)
                lines = output.read_text().splitlines()
                data = [line.split(",", 1)[1] for line in lines[1:] if ",#" not in line]
                assert data == ROWS, (mode, situation, data)
                power = [line.split(",", 1)[1] for line in lines if ",# log.power" in line]
                expected = [line for line in header.splitlines() if line.startswith("# log.power")]
                assert power == expected, (mode, situation, power)
                if situation == "renamed":
                    assert any(",# log.rename" in line for line in lines)
                print(f"PASS converter {mode}/{situation}: metadata and 14-column rows preserved")


if __name__ == "__main__":
    main()
