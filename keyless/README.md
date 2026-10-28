# Accord keyless

Pico W firmware and hardware for the keyless-entry module in a 2001 Honda
Accord. It provides BLE commands, proximity-based lock/unlock, automatic
relocking, and control of the trunk, lights and horn. It runs locally on the
board and retains USB/serial interfaces for diagnostics and control.

## Hardware

Open [hardware/hondaPico.kicad_pro](hardware/hondaPico.kicad_pro) in KiCad 9.
Install KiCad's standard symbol, footprint and 3D-model libraries. Project-local
custom symbols and footprints are included. The hardware project retains its
original `hondaPico` filename.

KiCad CLI 9.0.2 loads and exports the schematic and PCB. Checks report no errors,
but there are two schematic warnings, three board warnings and eight
PCB/schematic parity warnings. These include a missing J2 footprint and differing
R14/R15 values. See the [validation report](validation/kicad-20261027/README.md)
before using the design for fabrication. The 3D appearance has not been verified.

## Build

Use Arduino CLI 1.4.1 with Earle Philhower's Arduino-Pico core 6.1.0.
From `keyless/`:

```sh
arduino-cli compile --fqbn rp2040:rp2040:rpipicow:ipbtstack=ipv4btcble --build-path /tmp/accord-keyless-build firmware/accord-keyless
```

The board option enables BLE. The sketch is
[accord-keyless.ino](firmware/accord-keyless/accord-keyless.ino); it does not
require a Wi-Fi credential header. The existing BLE advertised name and
protocol names are unchanged.

## Tests

From `keyless/`, compile and run each native test:

```sh
for test in interlock relock proximity_act; do
  cc -std=c11 -Wall -Wextra -Werror "tests/${test}_test.c" -o "/tmp/accord-keyless-${test}" || exit
  "/tmp/accord-keyless-${test}" || exit
done
```

All three tests pass. The interlock and relock tests exercise copies of firmware
logic; they do not replace board testing or in-car proximity calibration.

Source provenance and validation are recorded in
[SOURCE_MANIFEST.json](SOURCE_MANIFEST.json).
