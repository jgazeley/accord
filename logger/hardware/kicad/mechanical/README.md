# Logger PCB reference for enclosure modelling

Extracted November 11, 2026 from `../accord-logger.kicad_pcb` using KiCad
9.0.2. Source SHA-256 is recorded in `accord-logger-mechanical.json`.
The outline and four mounting holes agree with the October 31 Rev A
fabrication Gerber and NPTH drill file.

Based on Accord by Jayson Gazeley — https://github.com/jgazeley/accord.
Generated hardware representations use CERN-OHL-P-2.0; see [LICENSE](../LICENSE)
and [NOTICE](../NOTICE). This README and the export script use Apache-2.0.

## Files and import

- **`accord-logger-board.step`**: bare PCB solid, including component and
  mounting drills; no component models. Import as a reference body in CAD.
- **`accord-logger-outline.dxf`**: exact outline lines/arcs on `BOARD_OUTLINE`
  and four circles on `MOUNTING_HOLES`. Import into a sketch in **millimetres**
  at **1:1 scale**. Use this simpler file for the case interior and standoffs.
  Join the eight outline entities if your CAD requires a closed wire.
- **`accord-logger-reference.svg`**: annotated top view for checking orientation
  and hole coordinates; use the DXF for modelling.
- **`accord-logger-mechanical.json`**: dimensions, exact outline primitives,
  hole positions and source hash for scripted CAD.

All exports use the same XY frame: viewed from the component/front side,
origin at the lower-left corner of the bounding rectangle, X right, Y up.
The origin is the theoretical sharp corner, outside the rounded profile.
Transform from KiCad coordinates: `X = x - 88.59`, `Y = 139.70 - y` (mm).

## Dimensions

The board is **120 × 83 mm**, with **2 mm corner radii**, and a **nominal
finished thickness of 1.6 mm** according to the project.

KiCad's board-only STEP exports the dielectric body from **Z = 0 to 1.51 mm**;
it omits the outer copper and soldermask in the 1.6 mm stackup. Use **1.6 mm**
for nominal finished-board clearance, and measure the physical board before
choosing a tight slot or clamp fit. Positive Z points toward front components.

| Hole | X (mm) | Y (mm) | Drill diameter (mm) |
|---|---:|---:|---:|
| H1, upper right | 115.880 | 78.740 | 3.2 |
| H2, lower right | 115.880 | 4.445 | 3.2 |
| H3, upper left | 4.120 | 78.740 | 3.2 |
| H4, lower left | 4.120 | 5.080 | 3.2 |

Do not make a symmetric four-hole pattern: H2 is **0.635 mm lower than H4**.
Horizontal pitch is 111.760 mm; vertical pitch is 74.295 mm on the right and
73.660 mm on the left. These are non-plated M3 clearance holes, not dimensions
for printed screw threads or inserts.

## What remains for the case

This is a board reference, with no enclosure fit allowance added. Offset the
board outline for the intended fit and printing process before adding walls.
Choose standoff outer diameters against nearby parts and copper, not just
the hole diameter. Existing assembly notes call for a nylon screw and washer
at H4 in the Pico antenna keep-clear strip.

J1 intentionally overhangs the right edge. J5 is on the back; the SD module
and its wiring require space below the PCB. The current assembly uses
transferred components and modified SD wiring (DECISIONS D-BUILD-25 and
D-FW-26), so the CAD footprints are not a measured assembly envelope.
Measure fitted component heights above/below the board and the actual SD,
USB and harness connector positions, including mating/unplugging space,
before setting case height or cutting access openings. The exports do not
claim those dimensions.

## Regenerate

From the repository root:

```sh
/usr/bin/python3 logger/hardware/kicad/tools/export_case_reference.py
```

Requires KiCad's `pcbnew` Python module and `kicad-cli`. The script reads the
source board without saving it, writes only these generated exports, and
checks that the source hash remains unchanged. It expects the current
four-line/four-arc outline and four round NPTH mounting holes; review the
reference drawing and measurements after any board revision.
