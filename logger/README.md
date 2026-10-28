# Accord trip logger

Pico W firmware that records vehicle measurements to an SD card and uploads
them over Wi-Fi during ignition-off windows. It captures speed/tachometer
pulses, ignition and brake-warning states, and analog readings, with clock
synchronization for timestamped records.

The current firmware is **v0.8.1-dev**. The sketch is
[accord-logger.ino](firmware/accord-logger/accord-logger.ino); firmware messages
retain the `picow-logger` name. Receiver, trip-processing and database software
are not included in this directory.

## Build and test

Use Arduino CLI 1.4.1, Arduino-Pico core 6.1.0, and the core's bundled
SdFat 2.3.1. The build helper selects that library explicitly and targets
`rp2040:rp2040:rpipicow`. From `logger/`:

```sh
python3 tools/test_native.py
python3 tools/build_candidate.py --build-dir /tmp/build-accord-logger-dummy
```

All eight native tests pass, and the firmware builds with zero warnings on this
toolchain. The tests cover sampling helpers, card records, time parsing, the
upload protocol and Wi-Fi scheduling; they do not replace device or receiver
integration testing.

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

The firmware does not yet implement automatic board power-off or SD retention
and deletion. A full SD card does not overwrite the oldest recordings. The
current arrangement keeps the Pico powered between journeys; Wi-Fi scheduling
controls connection attempts separately.

Source provenance and validation are recorded in
[SOURCE_MANIFEST.json](SOURCE_MANIFEST.json).
