# Raw recordings to trips

The receiver accepts resumable Pico W uploads, retains the original bytes,
and converts them into deterministic trip JSON packets. It runs on Linux with
Python 3.10+ and timezone data (`tzdata` on Debian). No Python packages or
database are required. Optional MQTT events require `paho-mqtt==2.1.0`.

```text
Pico SD records -> HTTP receiver -> durable raw files
                                -> cardconv.py -> tripd -> trip JSON spool
```

`upstream/` contains the single canonical copies of the converter and trip
engine in this repository. `host/replay.py` invokes them, assigns stable trip
identities, and holds incomplete or ambiguous input. `host/pipeline.py`
tracks processing versions and refuses changes to already published packets.
The source bytes match the historical working pipeline; see SOURCE_MANIFEST.json.
The core retains its optional legacy database adapter for source parity, but
`run.py` explicitly rejects database configuration.

## Run locally

From this directory, set a private token (also used by the Pico), an external
state directory, and a timezone:

```sh
export ACCORD_STATE_DIR="$HOME/.local/state/accord-receiver"
export ACCORD_TZ=America/Los_Angeles
read -r -s -p 'Upload token: ' ACCORD_UPLOAD_TOKEN; echo
export ACCORD_UPLOAD_TOKEN
python3 -B run.py
```

The shell example uses Bash. The default bind address is loopback. For actual
Pico uploads, explicitly set `ACCORD_BIND` to an appropriate LAN interface
and configure the Pico's private upload host/port/token. HTTP bearer tokens
are not encrypted: use a trusted, restricted network, not public Internet
exposure. The Pico client currently speaks HTTP, not HTTPS.

`GET /health` reports processing status. `database_loading:false` is expected.
The state directory contains `raw/`, `processed/`, `complete/`, `work/`, and
`spool/trip-*.json`. Back up raw data and state. Completion seals and stable
identities must survive service restarts; do not empty state to retry uploads.
Open files may publish closed trips while retaining an unfinished last trip.
The receiver does not delete SD files or implement storage retention.

## Service installation

The template in `deploy/accord-receiver.service` assumes this repository is
installed at `/opt/accord`, a system user/group `accord-receiver` exists, and
private configuration is at `/etc/accord-receiver.env`. Copy the example there,
replace its token, set the bind address and restrict the file to root (0600).
Systemd creates `/var/lib/accord-receiver`. Install and enable the unit only
when deliberately deploying a new instance. No installation or cutover is
performed by this repository. Use a separate endpoint and empty private state
for parallel evaluation; do not run two writers against the same state tree.

## Validation and scope

```sh
python3 -B tests/run.py
```

Tests use invented records and loopback HTTP: resumed delivery versus direct
card replay, packet identity, authentication, completion, clock ambiguity,
torn tails, repeat processing, append/seal races and durability failures.
They also verify the copied core hashes. Real vehicle histories and database
integration tests remain in the private development project.

This is an Accord-specific baseline, not yet a universal vehicle framework:
the vehicle identity is `accord-1`, and the trip engine uses 4104.3 pulses per
mile. Preserve those semantics when comparing to the original installation.
Changing calibration or processing bytes requires replay review; it must not
silently reinterpret existing published trips.

Record and upload specifications are in `../protocols/`. The JSON output is
`accord.trip/1`; it contains timing, distance/pulses, RPM and available signal
summaries, provenance and closure information. It does not assign a vehicle's
absolute odometer or render a maintenance dashboard.
