# Status

Rewritten, not appended to, whenever the state changes. Owner statements
go in [DECISIONS.md](DECISIONS.md). Last updated October 29, 2026.

## Goal now

A **Rev A logger PCB** to replace the breadboard wiring: autonomous power
with the car, the keyless RS-485 circuit, 80 × 120 mm. Then order, assemble,
bench test and vehicle test.

## Where it stands

**The electrical design is on `main` and ready for owner layout.**

- KiCad project: `logger/hardware/kicad/accord-logger.kicad_pro`. Summary of
  what's on the board: `logger/hardware/REV_A_CONTEXT.md`.
- The schematic and `BOM.csv` are **generated** by
  `logger/hardware/kicad/tools/gen_logger_sch.py`. Make electrical changes
  there, not in the KiCad GUI, or the next run overwrites them. Generation
  is deterministic, so regenerating doesn't break schematic-to-PCB links.
- Includes the keyless RS-485 circuit (D-RS485-05), the single 14-way
  JAE IL-AG5-14P-D3L2-A board connector J1 (D-CONN-06), and mostly
  surface-mount parts (D-SMD-09: 114 SMD, 34 through-hole).
- Verified on `main`: ERC 0 at all severities, 738/738 capture checks, 67
  power-closure checks with no overruns, 148 BOM rows all footprinted, 1.90×
  courtyard allowance on 80 × 120 mm, byte-identical regeneration
  (`logger/hardware/kicad/validation/COMMANDS.txt`).
- Engineering record: `logger/hardware/power/LAYOUT_CLOSURE.md`; risks,
  bring-up tests and firmware follow-up: `logger/hardware/LRA12_HANDOFF.md`.

## Next, in order

1. **Owner opens the schematic in KiCad once.** This host can't render it, so
   no one has looked at it.
2. **Owner places and routes** the board. `accord-logger.kicad_pcb` already
   has the 80 × 120 mm outline and four M3 corner holes; open it and use
   "Update PCB from Schematic" to bring in the parts.
3. Pre-order review of the routed board, then order (owner approval), then
   bring-up, bench and vehicle tests (`LRA12_HANDOFF.md` §5).
4. Firmware for the board: GP7 isolation enable and the shutdown order
   (`LRA12_HANDOFF.md` §5.4), before running it autonomously.

## Known risks carried forward (not layout blockers)

- **Sustained overvoltage above 17.1 V on P12** (24 V jump start,
  alternator overcharge) overheats the 1.5KE20A entry clamp. Deferred as a
  vehicle-test risk (D-OVERVOLT-04). Load dump is not covered.
- **RS-485 while the logger is off:** another node driving or biasing the
  bus can push current into the unpowered transceiver and through the bias
  resistor. Bias jumpers open by default; quantify on the bench.
- The power stage is bench-rated until tested: parked current, A5 regulator
  low-load behaviour, hot leakage, clock startup, cutoff timing. The test list
  is in `LRA12_HANDOFF.md` §5.
- Firmware: the opt-in power mode exists (`0.8.1-lra05-dev`, manual mode by
  default). The GP7 isolation enable and the shutdown sequence in
  `LRA12_HANDOFF.md` §5.4 need implementing before the board is used
  autonomously. Nothing has been flashed.

## Working now, outside Rev A

Logger v0.8.1-dev records to SD and uploads over Wi-Fi with the ignition off.
The VM receiver and guarded database intake were running at the last check
(October 28). The Pi 4 is a bench only. Open items not gating Rev A: storage
rotation, time/drift policy, historical data corrections, fuel calibration,
keyless proximity tuning, production-host cutover.

## Milestones

| | |
|---|---|
| M1 capture and trip records | Working; some fault cases open |
| M2 autonomous logger power | Designed (Rev A), not built or tested |
| M3 automatic upload without the Pi | Delivered on the VM |
| M4a road trial without the Pi, manual power | Demonstrated |
| M4 unattended, Pi retired | Open; needs M2 on a real board |
| M5 design ready to order | In progress (this page) |
| M6 assembled board accepted | Future |
