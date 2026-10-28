from pathlib import Path
import hashlib
import json
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
repo=ROOT.parents[1]
manifest=json.loads((ROOT/"SOURCE_MANIFEST.json").read_text())
for item in manifest["files"]:
    assert hashlib.sha256((repo/item["destination"]).read_bytes()).hexdigest()==item["sha256"], item["destination"]
print("PASS: imported source hashes",flush=True)
for test in ("check_wifi_contract.py","check_equivalence.py","check_startup.py"):
    subprocess.run([sys.executable,"-B",str(ROOT/"tests"/test)],check=True)
