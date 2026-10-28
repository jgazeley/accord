# Accord

Raspberry Pi Pico W firmware and keyless-entry hardware for a 2001 Honda Accord.

Two separate Pico W modules handle vehicle access and trip recording:

- **[Keyless entry](keyless/README.md)** — BLE commands, proximity-based
  lock/unlock, automatic relocking, and control of the trunk, lights and horn.
  Includes the KiCad schematic and PCB.
- **[Trip logger](logger/README.md)** — records speed/tachometer pulses,
  ignition, brake-warning and analog readings to an SD card, then uploads
  recordings over Wi-Fi during ignition-off windows.

Both run on the Pico W without an always-on in-car Linux computer. A Raspberry
Pi 4 serves as a portable development bench.

This is an ongoing vehicle-specific project. Build instructions, tests and
current limitations are documented with each module. The [logger server](logger/server/README.md) receives raw uploads and produces
trip JSON. Personal databases and dashboards are outside this repository.

## Development

This is the active home for Accord firmware, hardware and coordination.
See [current milestones and tasks](coordination/PROJECT_MILESTONES.md) and
[task handoffs](coordination/HANDOFF_INDEX.md). Earlier experiments remain in
`accord-logger` as historical reference; useful missing material is migrated
selectively. Installed services and private data are separate from this source tree.

## License

Created by **Jayson Gazeley (jgazeley)**. Software and documentation use
[Apache 2.0](LICENSE); original hardware designs use
[CERN-OHL-P 2.0](keyless/hardware/LICENSE). Reuse, including commercial use,
is welcome with the notices required by those licenses preserved.
See [licensing and credit](LICENSING.md) for attribution and third-party terms.
