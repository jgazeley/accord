#!/usr/bin/env python3
"""Build the logger with pinned Arduino-Pico/SdFat; never flash.

Default credentials are dummy and enable the upload code for compilation.
--secrets supplies a private header for the external bench build. Neither the
header contents nor firmware binaries belong in Git. Build directories contain
private generated source/logs as well as firmware when real credentials are used.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "firmware" / "accord-logger"
DUMMY = '''#pragma once
#define WIFI_SSID "compile-test-only"
#define WIFI_PASS "not-a-real-password"
#define API_TOKEN "test-token-not-a-real-one"
#define UPLOAD_HOST "192.0.2.10"
#define UPLOAD_PORT 8086
'''


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--secrets", type=Path, help="private header; omitted means DUMMY build")
    ap.add_argument("--build-dir", type=Path)
    args = ap.parse_args()
    out = (args.build_dir or ROOT / ("build-wifi-private" if args.secrets else "build-wifi-dummy")).resolve()
    if not out.name.startswith("build-") or out == ROOT or out in ROOT.parents:
        ap.error("use a dedicated build-* directory; Arduino CLI cleans its build directory")
    library = Path.home() / ".arduino15/packages/rp2040/hardware/rp2040/6.1.0/libraries/SdFat"
    if not library.is_dir():
        ap.error("install Arduino-Pico 6.1.0 for this user first")
    sources = sorted(p for p in FIRMWARE.iterdir()
                     if p.suffix in (".ino", ".h", ".cpp") and p.name != "secrets.h")
    out.mkdir(parents=True, exist_ok=True, mode=0o700)
    if args.secrets:
        out.chmod(0o700)
    with tempfile.TemporaryDirectory(prefix="accord-build-") as scratch:
        stage = Path(scratch) / "accord-logger"
        stage.mkdir()
        for p in sources:
            shutil.copy2(p, stage / p.name)
        source_hashes = {p.name: digest(stage / p.name) for p in sources}
        if args.secrets:
            shutil.copyfile(args.secrets, stage / "secrets.h")
        else:
            (stage / "secrets.h").write_text(DUMMY)
        command = ["arduino-cli", "compile", "--fqbn", "rp2040:rp2040:rpipicow",
                   "--build-path", str(out), "--warnings", "all", "--library", str(library), str(stage)]
        # Keep log outside the directory Arduino may clean during compilation.
        with tempfile.TemporaryFile(mode="w+") as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
            log.seek(0)
            output = log.read()
        (out / "build.log").write_text(output)
        if result.returncode:
            raise SystemExit(f"Build failed; inspect private log {out / 'build.log'}")
    metadata = {
        "profile": "private-bench" if args.secrets else "DUMMY-CREDENTIALS-DO-NOT-FLASH",
        "fqbn": "rp2040:rp2040:rpipicow", "core": "6.1.0", "sdfat": "2.3.1",
        "cli": subprocess.check_output(["arduino-cli", "version"], text=True).strip(),
        "sources": source_hashes,
        "artifacts": {p.name: digest(p) for p in sorted(out.glob("*.uf2"))},
        "build_summary": [s for s in output.splitlines() if s.startswith(("Sketch uses", "Global variables"))],
        "warnings": output.count("warning:"),
    }
    (out / "manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(metadata["profile"])
    for line in metadata["build_summary"]:
        print(line)
    print(f"Warnings: {metadata['warnings']}")
    print(f"Manifest: {out / 'manifest.json'}")
    for name, sha in metadata["artifacts"].items():
        print(f"{sha}  {out / name}")


if __name__ == "__main__":
    main()
