#!/usr/bin/env python3
"""HTTP completion, immutability, replay holds, tail policy and durability.

Temporary files only; no database or installed service. These regressions close
B1-B3 in the local manager's cd64ce5 review.
"""
import hashlib
import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading

BRIDGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BRIDGE / 'host'))
import storage
from pipeline import Pipeline
from server import Server

UNIT = '0011223344556677'
TOKEN = 'isolated-contract-test-token'


def fixture(number=1, seconds=421, dated=True):
    header = (f'# accord-log/1\n# log.unit chip={UNIT} vehicle=accord-1 fw=0.8.0-dev\n'
              '# log.columns ms,vss_total,vss_hz,tach_total,tach_hz,rpm,brake,'
              'fuel_counts,fuel_lo,fuel_hi,supply_counts,die_counts,ms_since_ign,ign\n'
              f'# log.file name={"/20261025_120000.CSV" if dated else "/BOOT_540.CSV"}'
              f' opened_ms=540 clock={"sntp" if dated else "none"}\n'
              f'# log.upload id={number:032x} policy=create-only\n# log.end\n')
    v = t = 0
    rows = []
    for i in range(1, seconds + 1):
        on = not 181 <= i <= 220
        if on:
            v += 46
            t += 30
        rows.append(f'{540+i*1000},{v},{46 if on else 0}.00,{t},'
                    f'{30 if on else 0}.00,{900 if on else 0},0,1850,1844,1861,2900,2714,'
                    f'{i*1000 if on else 0},{int(on)}\n')
    return (header + ''.join(rows)).encode()


def name(n):
    return f'U_{n:032x}.CSV'


def main():
    with tempfile.TemporaryDirectory(prefix='bridge-wifi-contract-') as tmp:
        root = Path(tmp)
        store = storage.Store(root/'raw')
        engine = Pipeline(store, root, BRIDGE/'upstream')
        touches = []
        server = Server(('127.0.0.1', 0), store, TOKEN, on_append=lambda: touches.append(1))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        def call(method, endpoint, n=1, suffix='', data=None, token=TOKEN):
            conn = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
            conn.request(method, f'/v1/{endpoint}?unit={UNIT}&file={name(n)}{suffix}',
                         body=data, headers={'Authorization': 'Bearer '+token})
            reply = conn.getresponse()
            result = reply.status, json.loads(reply.read())
            conn.close()
            return result

        try:
            data = fixture().rstrip(b'\n')
            assert call('POST', 'append', suffix='&from=0', data=data)[0] == 200
            before, _ = engine.process(UNIT, name(1))
            assert len(before['trips']) == 1 and not before['complete']
            assert call('POST', 'complete', suffix=f'&bytes={len(data)}', data=b'', token='wrong')[0] == 401
            assert call('POST', 'complete', suffix=f'&bytes={len(data)+1}', data=b'')[0] == 409
            assert call('POST', 'complete', suffix=f'&bytes={len(data)}', data=b'bad')[0] == 400
            assert call('POST', 'complete', suffix=f'&bytes={len(data)}', data=b'')[0] == 200
            assert call('POST', 'complete', suffix=f'&bytes={len(data)}', data=b'')[0] == 200
            assert call('GET', 'offset')[1]['complete']
            assert call('POST', 'append', suffix=f'&from={len(data)}', data=b'extra')[0] == 409
            assert store.snapshot(UNIT, name(1)) == data
            seal = store.completion(UNIT, name(1))
            assert seal['sha256'] == hashlib.sha256(data).hexdigest()
            record, fresh = engine.process(UNIT, name(1))
            assert len(record['trips']) == 2 and len(fresh) == 1
            assert fresh[0]['vss']['pulse_count_trip'] == 9200
            assert record['trailing_bytes_held'] > 0
            assert fresh[0]['close_reason'] == 'log_end'
            # Server and store can restart; repeated replay publishes nothing.
            again = storage.Store(store.root)
            assert again.status(UNIT, name(1)) == (len(data), True)
            assert again.append(UNIT, name(1), len(data), b'extra')[0] is None
            assert not engine.process(UNIT, name(1))[1]
            assert len(touches) >= 3
            print('PASS: authenticated HTTP completion, retries/restart, seal enforcement, final-trip trigger and tail policy')

            disputed = fixture(2).replace(b'300540,', b'# TIME 2026-10-25T13:05:00Z src=sntp synced=1\n300540,', 1)
            store.append(UNIT, name(2), 0, disputed)
            record, fresh = engine.process(UNIT, name(2))
            assert not fresh and record['held'] and 'clock conflict' in record['pending']
            # A later warning cannot modify previously published packets either.
            steady = fixture(3, seconds=300)
            store.append(UNIT, name(3), 0, steady)
            _, fresh = engine.process(UNIT, name(3))
            assert len(fresh) == 1
            snapshots = {p.name:p.read_bytes() for p in engine.spool.iterdir()}
            extra = b'# TIME 2026-10-25T13:05:01Z src=sntp synced=1\n301540,12000,46,9000,30,900,0,1850,1844,1861,2900,2714,301000,1\n'
            store.append(UNIT, name(3), len(steady), extra)
            record, fresh = engine.process(UNIT, name(3))
            assert record['held'] and not fresh
            assert snapshots == {p.name:p.read_bytes() for p in engine.spool.iterdir()}
            unknown = fixture(4, dated=False)
            store.append(UNIT, name(4), 0, unknown)
            store.complete(UNIT, name(4), len(unknown))
            record, fresh = engine.process(UNIT, name(4))
            assert not fresh and record['held'] and 'no absolute time' in record['pending']
            print('PASS: clock conflicts and unknown-time completed files hold; prior packets remain untouched')

            # Identity mismatch is rejected by production replay.
            store.append(UNIT, name(5), 0, fixture(6))
            try:
                engine.process(UNIT, name(5))
                raise AssertionError('mismatched upload ID accepted')
            except ValueError as exc:
                assert 'identity' in str(exc)

            # Read old operator markers without allowing any append after upgrade.
            old = '20261024_120000.CSV'
            store.append(UNIT, old, 0, b'legacy\n')
            storage.atomic_json(root/'complete'/f'{UNIT}-{old}.json',
                                {'bytes':7, 'sha256':hashlib.sha256(b'legacy\n').hexdigest()})
            assert store.status(UNIT, old) == (7, True)
            assert store.append(UNIT, old, 7, b'extra')[0] is None
            assert store.complete(UNIT, old, 7, basis='operator')[0]
            print('PASS: immutable upload ID validation and preservation of legacy operator seals')

            # Race completion against append: either the append wins and size
            # assertion fails, or the seal wins and append is refused.
            for i in range(8):
                race = f'race{i}.CSV'
                store.append(UNIT, race, 0, b'abc')
                gate = threading.Barrier(2)
                results = {}
                def append():
                    gate.wait(); results['append'] = store.append(UNIT, race, 3, b'd')
                def seal_file():
                    gate.wait(); results['complete'] = store.complete(UNIT, race, 3)
                threads = [threading.Thread(target=append), threading.Thread(target=seal_file)]
                for t in threads: t.start()
                for t in threads: t.join()
                assert len(results) == 2
                if results['complete'][0]:
                    assert results['append'][0] is None and store.snapshot(UNIT, race) == b'abc'
                else:
                    assert results['append'][0] == 4 and store.snapshot(UNIT, race) == b'abcd'
            print('PASS: append/complete races never acknowledge a sealed mutable file')

            # Raw and each marker-directory durability barrier must be retried.
            for i, kind in enumerate(('raw', 'marker', 'marker-root', 'root')):
                item = f'fsync{i}.CSV'
                store.append(UNIT, item, 0, b'abc')
                marker = store.completion_path(UNIT, item)
                barrier = {'raw':store.path(UNIT,item).parent, 'marker':marker.parent,
                           'marker-root':marker.parent.parent, 'root':store.root}[kind]
                real = storage.sync_dir
                injected, calls = [], []
                def fail_once(path):
                    calls.append(path)
                    if path == barrier and not injected:
                        injected.append(True)
                        raise OSError('injected fsync failure')
                    return real(path)
                storage.sync_dir = fail_once
                try:
                    try:
                        store.complete(UNIT, item, 3)
                        raise AssertionError('failed fsync acknowledged')
                    except OSError: pass
                    assert injected
                    calls.clear()
                    assert store.complete(UNIT, item, 3)[0] and barrier in calls
                finally:
                    storage.sync_dir = real
            print('PASS: failed completion directory barriers are retried before acknowledgement')
        finally:
            server.shutdown(); thread.join(); server.server_close()
    print('PASS: Wi-Fi bridge contract, no database accessed')


if __name__ == '__main__':
    main()
