# Status

Rewritten, not appended to, whenever the state changes. Owner statements
go in [DECISIONS.md](DECISIONS.md). Last updated October 29, 2026.

## Goal now

A **Rev A logger PCB** to replace the breadboard wiring: autonomous power
with the car, the keyless RS-485 circuit, 80 × 120 mm. Then order, assemble,
bench test and vehicle test.

## Where it stands

**Electrical design is nearly ready for owner layout. It is not on `main`
yet.**

- The KiCad project is `logger/hardware/kicad/accord-logger.kicad_pro`.
  `main` still carries the older LRA-06 capture. The current design is on
  the `task/LRA-12-b690946d` branch, with corrections on
  `task/LRA-12R-01a18a47` (`50d93c8`, plus RS-485 work being finished).
- The schematic and `BOM.csv` are **generated** by
  `logger/hardware/kicad/tools/gen_logger_sch.py`. Make electrical changes
  there, not in the KiCad GUI, or the next run overwrites them. Generation
  is deterministic, so regenerating doesn't break schematic-to-PCB links.
- Last verified (`50d93c8`): ERC 0 at all severities, 652/652 capture
  checks, 63/63 power-closure checks, 141 parts all with footprints, 1.52×
  courtyard allowance on 80 × 120 mm.
- Engineering record: `logger/hardware/power/LAYOUT_CLOSURE.md` (clamp,
  A5 supply, isolation, grounding, fit) and `logger/hardware/LRA12_HANDOFF.md`
  (risks, bring-up tests, firmware follow-up).

## Next, in order

1. **Finish RS-485** (D-RS485-05). Codex is completing the keyless MAX3485
   circuit on `task/LRA-12R-01a18a47`, with an interim 4-pin bus connector.
2. **Merge to `main`**: LRA-12, LRA-12R and RS-485 together, then rerun all
   checks on `main`.
3. **Single connector** (D-CONN-06): waiting for the owner to choose between
   the in-stock 10-pin Molex-style connector (confirm its part number) and
   JAE IL-AG5-14P-D3L2-A. Replace J1, J2 and the interim bus connector.
   Then update `logger/hardware/README.md` and `REV_A_CONTEXT.md`.
4. **Owner opens the schematic in KiCad once.** This host cannot render it,
   so no one has looked at it.
5. **Owner places and routes** the board.
6. Pre-order review, then order (owner approval), then bring-up and
   vehicle tests.

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
