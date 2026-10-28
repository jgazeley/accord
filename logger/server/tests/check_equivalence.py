"""Synthetic interrupted HTTP upload must equal direct SD-file replay."""
import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "host"))
sys.path.insert(0, str(ROOT / "tests"))
from check_wifi_contract import fixture, name, UNIT
from server import Server
from storage import Store
from pipeline import Pipeline, measurement
from replay import replay

def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = fixture()
        card = root / name(1)
        card.write_bytes(data)
        expected = replay(card, ROOT / "upstream", UNIT, "America/Los_Angeles", complete=True)["packets"]
        assert len(expected) == 2
        store = Store(root / "received" / "raw")
        server = Server(("127.0.0.1", 0), store, "synthetic-test-token")
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        def request(method, endpoint, body=None, token="synthetic-test-token"):
            conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            conn.request(method, f"/v1/{endpoint}", body=body,
                         headers={"Authorization": "Bearer " + token})
            response = conn.getresponse(); status=response.status; result=response.read();conn.close()
            return status,json.loads(result)
        try:
            query = f"unit={UNIT}&file={name(1)}"
            assert request("POST", "append?"+query+"&from=0", data[:317], token="wrong")[0] == 401
            offset=0
            while offset < len(data):
                chunk=data[offset:offset+317]
                assert request("POST", "append?"+query+f"&from={offset}", chunk)[0] == 200
                offset+=len(chunk)
                # Each request uses a fresh connection, like a reconnect/resume.
            assert store.snapshot(UNIT,name(1)) == data
            store.complete(UNIT,name(1),len(data))
            engine=Pipeline(store,root/"received",ROOT/"upstream",timezone="America/Los_Angeles")
            record,actual=engine.process(UNIT,name(1))
            assert len(actual)==2
            assert [measurement(p) for p in actual] == [measurement(p) for p in expected]
            assert [p["trip_id"] for p in actual] == [p["trip_id"] for p in expected]
            assert not engine.process(UNIT,name(1))[1]
            print("PASS: synthetic HTTP/card equivalence, stable IDs, authentication and idempotence")
        finally:
            server.shutdown();worker.join();server.server_close()
if __name__ == "__main__": main()
