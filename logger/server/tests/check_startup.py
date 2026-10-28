"""Check the standalone entry point without contacting deployed services."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
env={k:v for k,v in os.environ.items() if not k.startswith(("ACCORD_","MQTT_"))}
def rejected(extra):
    result=subprocess.run([sys.executable,"-B",str(ROOT/"run.py")],env={**env,**extra},capture_output=True,timeout=5)
    assert result.returncode!=0
rejected({})
rejected({"ACCORD_UPLOAD_TOKEN":"synthetic-token","ACCORD_STATE_DIR":str(ROOT/"state")})
rejected({"ACCORD_UPLOAD_TOKEN":"synthetic-token","ACCORD_STATE_DIR":"/tmp/test-state","ACCORD_DATABASE":"unused.db"})
with tempfile.TemporaryDirectory() as tmp:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1",0));port=sock.getsockname()[1]
    with open(Path(tmp)/"service.log","w") as log:
        proc=subprocess.Popen([sys.executable,"-B",str(ROOT/"run.py")],env={**env,"ACCORD_UPLOAD_TOKEN":"synthetic-token","ACCORD_STATE_DIR":tmp,"ACCORD_PORT":str(port)},stdout=log,stderr=log)
        try:
            for _ in range(50):
                assert proc.poll() is None
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/health",timeout=1) as response:
                        status=json.load(response)
                    assert status["database_loading"] is False
                    break
                except OSError: time.sleep(.1)
            else: raise AssertionError("Receiver did not start")
        finally:
            proc.terminate();proc.wait(timeout=10)
print("PASS: startup guards, standalone health and graceful termination")
