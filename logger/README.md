# Accord trip logger

Pico W firmware that records vehicle measurements to an SD card and uploads
them over Wi-Fi during ignition-off windows. It captures speed/tachometer
pulses, ignition and brake-warning states, and analog readings, with clock
synchronization for timestamped records.

The current source is the **v0.8.1-lra05-dev** firmware candidate. The sketch is
[accord-logger.ino](firmware/accord-logger/accord-logger.ino); firmware messages
retain the `picow-logger` name. The [server](server/README.md) receives uploads and converts them to trip JSON.
Database and dashboard applications are separate consumers.

## Build and test

Use Arduino CLI 1.4.1, Arduino-Pico core 6.1.0, and the core's bundled
SdFat 2.3.1. The build helper selects that library explicitly and targets
`rp2040:rp2040:rpipicow`. From `logger/`:

```sh
python3 tools/test_native.py
python3 tools/build_candidate.py --build-dir /tmp/build-accord-logger-dummy
```

The native runner contains nine suites, including the power supervisor. The
LRA-05 integration review recorded passing native tests and both dummy build
modes on this toolchain; see [configuration and validation](NEXT_AGENT.md).
Tests cover sampling helpers, card records, time parsing, uploads, Wi-Fi and
power-state logic; they do not replace device or receiver integration testing.

The default build uses dummy credentials and is marked
**DUMMY-CREDENTIALS-DO-NOT-FLASH**. The helper never flashes a board.

## Configure an upload build

Create a private `secrets.h` from
[secrets.h.example](firmware/accord-logger/secrets.h.example). Set `WIFI_SSID`,
`WIFI_PASS`, `API_TOKEN`, `UPLOAD_HOST` and `UPLOAD_PORT` for your network and
compatible receiver. `UPLOAD_HOST` must be a literal IPv4 address without a
scheme or path; an empty or omitted host disables uploads.

Supply the private header explicitly:

```sh
python3 tools/build_candidate.py --secrets /absolute/private/path/secrets.h --build-dir /absolute/private/path/build-accord-logger
```

Without `--secrets`, the helper uses dummy credentials even if a local header
exists. Keep the header and configured build output private: firmware binaries
and generated source can contain credentials.

## Current limits

Manual power remains the default (`LOGGER_POWER_QUALIFIED=0`). An opt-in
qualified-ignition/HOLD shutdown implementation exists, but its hardware and
fault-timing acceptance remain open. It is not enabled for the existing manual
wiring. See [configuration notes](NEXT_AGENT.md).

SD retention/deletion is not implemented: a full card does not overwrite the
oldest recordings. Wi-Fi scheduling controls connection attempts separately
from board power.

Source provenance and validation are recorded in
[SOURCE_MANIFEST.json](SOURCE_MANIFEST.json).

Hardware interfaces and remaining documentation: [logger hardware](hardware/README.md).
Record and transfer contracts: [card format](protocols/CARD_FORMAT.md) and
[upload protocol](protocols/UPLOAD_PROTOCOL.md).
