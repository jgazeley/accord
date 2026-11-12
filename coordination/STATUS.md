# Status

Rewritten, not appended to, whenever the state changes. Owner statements
go in [DECISIONS.md](DECISIONS.md). Last updated November 11, 2026.

## Goal now

A **Rev A logger PCB**, 120 × 83 mm, is replacing the breadboard logger.
The partially populated board has logged car trips; autonomous power remains
future work. A first simple case bottom has been modelled for the owner.

## Where it stands

**The electrical design and completed layout are on `main`. Bare boards have
arrived, and the owner has transferred the working circuit onto one.**

- Physical build and firmware: DECISIONS D-BUILD-25 through D-DB-28. The
  DigiKey parts order was not placed; USB/external-buck power and manual
  shutdown continue. The Rev A Pico runs the tailored Wi-Fi/SD build with
  MOSI on GP7 and SCK on GP6 by wire. Do not infer fitted parts from the BOM.
- **Case reference extracted** (November 11, D-CASE-30):
  `logger/hardware/kicad/mechanical/` contains a bare-board STEP, exact
  outline/mounting-hole DXF, annotated SVG and coordinates JSON. Outline and
  mounting holes match the Rev A fabrication files: 120 × 83 mm, R2 corners,
  four Ø3.2 holes; H2 is 0.635 mm below H4. Fitted component heights and
  connector/SD access still need physical measurements for a complete case.
- **Simple case bottom modelled** (November 11, D-CASE-31):
  `logger/hardware/kicad/mechanical/case-bottom/` contains STL, editable
  OpenSCAD source and a preview. Walls are 2 mm (revised in D-CASE-33); starting
  defaults are 1 mm PCB clearance per side, 4 mm floor and 12 mm internal
  depth (126 × 89 × 16 mm overall). **Four stepped locating studs added**
  (D-CASE-32, height halved in D-CASE-34): Ø6 mm shoulders support the PCB
  3.175 mm above the inside floor; Ø3 mm pins enter its Ø3.2 mm holes, extending 3 mm above the
  shoulders with tapered tips. Exported-STL slice checks confirm the actual
  hole positions, support/pin diameters and one joined solid. Connector
  openings and physical assembly fit remain to be checked.
  The exterior bottom perimeter has a 1 mm × 1 mm, 45° chamfer (D-CASE-35);
  underside preview and STL section checks confirm the bevel.

Design and fabrication record:

- KiCad project: `logger/hardware/kicad/accord-logger.kicad_pro`. Summary of
  what's on the board: `logger/hardware/REV_A_CONTEXT.md`.
- **The hand-edited schematic is the master** (since October 30). The
  owner edits it in KiCad; the generator that first produced it now refuses
  to overwrite it. After each edit: ERC, netlist export, `check_capture.py`
  (commands in `logger/hardware/kicad/validation/COMMANDS.txt`). A part
  change also needs `BOM.csv` updated.
- Includes the keyless RS-485 circuit (D-RS485-05), the single 14-way
  JAE IL-AG5-14P-D3L2-A board connector J1 (D-CONN-06), and mostly
  surface-mount parts (D-SMD-09: 114 SMD, 34 through-hole).
- Verified on `main`: ERC 0 at all severities, 779/779 capture checks, 67
  power-closure checks with no overruns, 145 BOM rows all footprinted, 1.64×
  courtyard allowance on 80 × 120 mm
  (`logger/hardware/kicad/validation/COMMANDS.txt`).
- **DS3231 RTC on the board** (D-RTC-14, October 30): DS3231SN on I2C0
  (GP20 SDA, GP21 SCL, GP22 INT/SQW), pull-ups on switched 3V3, BR2032 in a
  Keystone 3034 holder, placed. The DS3231SN#, holder and cell need
  ordering; firmware needs an RTC driver.
- **J3 is a 2x03** (D-HDR-16, October 31): B5, PGND, GP13, switched 3V3,
  GP12, GP11. TP24/TP25 (GP11/GP12 pads) are gone.
- **No more test points; remaining resistors 0805** (D-SMD-17, October 31):
  TP10, TP13-TP16, TP18 removed (probe at part pads, REV_A_INTERFACES
  §5.3); R39-R43, R45, R46 on 0805.
- Engineering record: `logger/hardware/power/LAYOUT_CLOSURE.md`; risks,
  bring-up tests and firmware follow-up: `logger/hardware/LRA12_HANDOFF.md`.

- **Rev A fabrication release** (October 31). Every part placed and routed;
  board 120 × 83 mm (D-ENVELOPE-02). Silkscreen pass done; DRC 0 active
  with 11 accepted exclusions (D-DRC-24); schematic parity 0; ERC 0;
  capture 780/780; closure 67/67. Fab package:
  `logger/hardware/kicad/fab/rev-a/` (gerber zip, separate PTH/NPTH
  drill, README with the plot commands). Parts: `order/digikey_rev_a.csv`
  (D-ORDER-19, regenerate with `tools/gen_digikey_order.py`). Review
  loop: ERC, full netlist (`board_chunks.py full-netlist`), capture,
  closure, and DRC with parity on a copy of the project (never
  `kicad-cli pcb drc` in the shared checkout; it rewrites the
  .kicad_pro). Assembly notes: nylon screw and washer at H4 (Pico RF
  keep-clear strip); J5 on the back and J1 overhanging are intentional.

## Next, in order

1. Review the case bottom with locating studs; check printed pin fit and
   underside assembly clearance, then establish connector openings and final height.
2. Continue validating the partially populated board in the car; November 11
   SD-card dislodgement and trip recovery are recorded in D-DB-29.
3. For future autonomous operation, finish parts procurement, assembly and
   bring-up (`LRA12_HANDOFF.md` §5), with owner authorization at each stage.
4. Reconcile the current GP7/GP6 SD wiring with the designed GP7 isolation
   enable before implementing autonomous shutdown (`LRA12_HANDOFF.md` §5.4).
   The DS3231 driver and on-board power-mode work remain outstanding.

## Known risks carried forward (not layout blockers)

- **No fuse on the board** (D-FUSE-10): the harness needs a 1 A inline fuse
  at the feed end. It protects the wire and is what clears a sustained
  overvoltage before the clamp fails.
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
| M5 design ready to order | Fabrication released; bare boards received |
| M6 assembled board accepted | Partial assembly logging trips; full Rev A acceptance open |
