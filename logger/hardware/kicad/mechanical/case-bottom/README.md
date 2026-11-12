# Simple logger case bottom

For the snap-on lid, use the **[matching pair in case-enclosure](../case-enclosure/README.md)**.
This earlier tray is retained as its input blank; it does not have latch windows.

An open tray with four stepped locating studs, based on the 120 × 83 mm,
R2 PCB outline and its actual mounting-hole centers.
The owner requested rounded corners and some clearance around the PCB,
revising the walls from 4 mm to 2 mm (DECISIONS D-CASE-31 and D-CASE-33).
The starting clearance, floor thickness and
depth below are adjustable modelling choices. The owner subsequently
requested wider supports raising the PCB about a quarter inch, narrowing
to pins that fit through its mounting holes (D-CASE-32), then halved the
thicker support section to 3.175 mm (D-CASE-34).
The exterior bottom edge is chamfered per D-CASE-35; the starting chamfer
size is 1 mm horizontally and vertically (45°).
SD and JAE access openings were added November 12 (D-CASE-36), using the
owner's drawings and PCB coordinates. The SD placement is explicitly
provisional and directly above the main PCB.

| Dimension | Value |
|---|---:|
| Wall thickness | 2 mm |
| Clearance from PCB edge to inside wall, each side | 1 mm |
| Inside width × length | 122 × 85 mm |
| Floor thickness | 4 mm |
| Internal depth above floor | 12 mm |
| Outside width × length × height | 126 × 89 × 16 mm |
| Inside corner radius | 3 mm |
| Outside corner radius | 5 mm |
| Exterior bottom chamfer | 1 × 1 mm at 45° |
| Flat underside contact footprint | 124 × 87 mm, R4 corners |
| PCB underside height above inside floor | 3.175 mm (⅛ inch) |
| Support shoulder diameter | 6 mm |
| Locating pin diameter / PCB hole diameter | 3.0 / 3.2 mm |
| Pin height above shoulder | 3 mm |
| Lead-in tip | Last 0.5 mm tapers to Ø2.4 mm |

The concentric corner offsets preserve the 1 mm PCB gap and 2 mm wall
thickness around the curves. The exterior bottom bevel runs from the inset
underside at Z=0 to the full exterior profile at Z=1, including the rounded
corners. The interior floor and top rim edges are square. The interior floor
is Z=4 and the rim is Z=16; the floor remains 4 mm thick inside the cavity.
XY uses the same datum as the PCB reference, so the case spans X=-3..123
and Y=-3..86 mm.

## PCB supports

The PCB rests on the four Ø6 mm shoulders at **Z=7.175 mm**, 3.175 mm above
the inside floor. The narrower pins enter the board holes. A nominal 1.6 mm
PCB has its upper surface at Z=8.775 mm; pin tips reach Z=10.175 mm, leaving
1.4 mm above the PCB. Pins have **0.2 mm diametral clearance** (0.1 mm per
side); this is a starting slip-fit allowance and may need adjustment for the
printer. The short tapered tips help align all four holes when lowering the
board. These locating pins are unthreaded and do not clamp the board down.

| Support | X (mm) | Y (mm) |
|---|---:|---:|
| H1 | 115.880 | 78.740 |
| H2 | 115.880 | 4.445 |
| H3 | 4.120 | 78.740 |
| H4 | 4.120 | 5.080 |

The lower pair remains asymmetric, as on the PCB. Support bases are joined
to the floor as one solid, with no enclosed interfaces or separate shells.
The Ø6 mm shoulders stay within the PCB boundary; the nearest non-mounting
pad bounding box is 4.149 mm from a hole center, beyond the 3 mm shoulder
radius. This checks the PCB drawing, not solder or other fitted hardware.

## SD and JAE openings

All Z coordinates start at the **outside bottom** of the case. The PCB top is:

`4 mm floor + 3.175 mm support shoulder + 1.6 mm PCB = 8.775 mm`.

Measured from the inside floor, that is 4.775 mm. Both socket bodies are
modelled as seated at the PCB top. A 0.5 mm allowance below their seating
plane puts the opening's lower edge at **Z=8.275 mm**, or 4.275 mm above the
inside floor. The narrow pins do not set this height: the PCB sits on the
wider shoulders and the pins pass through it.

| Opening | Wall | Center along wall | Width | Actual Z range | Actual opening height |
|---|---|---:|---:|---:|---:|
| SD / J5 | Front, Y=-3..-1 | X=41.2675 | 29.8 | 8.275..12.025 | 3.75 |
| JAE / J1 | Right, X=121..123 | Y=40.000 | 28.0 | 8.275..16.000 | 7.725, open at rim |

See **`cutout-layout.svg`** for wall elevations and the height datum.
Both openings cut through the full 2 mm wall. Outside case dimensions,
chamfer, support positions and heights are unchanged.

### SD reference and provisional placement

The supplied [SD-slot drawing](../../../../../docs/SD-slot.jpg) is a Sunrom
7422 **full-size SD socket** drawing, not a drawing of the six-pin reader
module. Its socket envelope is **28.80 mm wide × 2.75 mm high**. The
24.20 mm dimension is a different feature and is not used as the opening
width. Adding 0.5 mm on each side gives a **29.8 × 3.75 mm** rectangular
access window. Its center height is Z=10.150 mm.

J5 pin 1 is at X=47.6175 and pin 6 at X=34.9175 in the extracted PCB frame.
Their midpoint is `(47.6175+34.9175)/2 = 41.2675 mm`. All six pins lie at
Y=15.755, parallel to the nearby front (-Y) edge. Projecting that midpoint
to the front wall gives the window's X limits **26.3675..56.1675 mm**.
This determines lateral alignment, not the reader's reach toward the wall.

The KiCad header is on **B.Cu** and earlier assembly notes described the
reader below the PCB. Asked specifically, the owner chose **"Directly above
PCB — provisional fit"** for this model. No header/breakout stack height is
added. This is a generous socket-envelope opening, not a measured card-only
slit. Verify actual reader width, socket height, facing direction, mouth
distance from the wall and finger access before treating this as a final fit.
`sd_base_offset` / `--sd-base-offset` raises the socket relative to the main
PCB if measurements require it.

### JAE reference and top-open notch

The [JAE IL-AG5 catalogue](../../../../../docs/IL-AG5_Series.pdf), PDF page 3,
printed page **10**, **RIGHT ANGLE PIN HEADER / Double Row**, specifies
**IL-AG5-14P-D3L2-A** with **B=26.5 ±0.5 mm width** and **15 ±0.5 mm body
height**. The **18.2 mm** side-view dimension is its depth, not its height;
the **3.5 mm** dimension is the below-body guide/lead projection, not a
spacer to add above the PCB.

Use the maximum body width, 27.0 mm, plus 0.5 mm each side: **28.0 mm**.
The current J1 F.Fab outline spans Y=26.75..53.25, centered at **Y=40.0**;
the opening spans **Y=26..54**. The connector faces +X. Its nominal front
face is X=122.9425, approximately flush with the X=123 outer wall, as inferred
from the footprint. Seating height assumes the body rests on the PCB top.

The complete height clearance would run from Z=8.275 to
`8.775 + 15.5 maximum body height + 0.5 clearance = 24.775 mm`, a 16.5 mm
envelope. The case rim is only Z=16, so this case bottom correctly has a
**top-open notch**, not a closed 16.5 mm-high window. Its material removal
is 7.725 mm deep down from the rim. A future lid must accommodate the body
and clearance above that rim, plus access to the mating connector's latch.

The source PDF and JPG remain local reference files; the dimensions are
recorded here without redistributing those drawings. This is a CAD fit
calculation, not a measurement of the populated assembly.

## Files

- **`accord-logger-case-bottom.stl`**: closed, oriented mesh for a slicer or
  CAD mesh import. Interpret its coordinates as millimetres.
- **`accord-logger-case-bottom.scad`**: editable parametric OpenSCAD model.
  Change the case and support parameters at the top,
  then render/export in OpenSCAD. OpenSCAD is not installed on the generation
  host; the supplied STL was built directly from the same profile parameters.
- **`preview.png`**: illustration of the supplied STL geometry.
- **`underside-preview.png`**: view from below showing the bottom chamfer.
- **`cutout-layout.svg`**: dimensioned SD and JAE wall elevations, including
  the JAE body height extending above the rim.
- **`dimensions.json`**: source PCB hash, dimensions and mesh check results.

The studs are locating pins; fixing holes and a lid interface have not been
added. Check physical assembly clearance at the requested 3.175 mm support
height and the provisional SD opening before treating this as an assembly-fit
case. Cavity dimensions describe PCB clearance.

## Regenerate

Using Python 3 with NumPy and Manifold3D installed (`manifold3d==3.5.4`
was used for this export), run from the repository root:

```sh
python3 logger/hardware/kicad/tools/build_case_bottom.py --preview
```

Pillow is additionally needed for `--preview`. Install the Python packages
in your preferred virtual environment with
`python3 -m pip install manifold3d==3.5.4 numpy pillow`.
The generator checks the current PCB hash against the extracted reference.
Options `--wall`, `--clearance`, `--floor`, `--depth`, `--bottom-chamfer`, `--support-height`,
`--support-diameter`, `--pin-clearance`, `--pin-height` and `--output-dir`
produce variants. Opening options are `--opening-clearance`, `--sd-body-width`,
`--sd-body-height`, `--sd-base-offset` and `--jae-base-offset`. The matching
OpenSCAD parameters are editable at the top of the model. Opening Z positions
follow the floor, support height and PCB thickness automatically. The positive
chamfer size must not exceed wall thickness
and must be less than floor thickness. Pin clearance is **diametral**, subtracted from each PCB
hole diameter. Generated files in the output directory are
overwritten; keep custom OpenSCAD edits separately if rerunning the generator.

The generator checks float32 STL coordinates for paired, oppositely directed
edges, expected opening topology, nondegenerate faces, positive volume, bounding
dimensions and agreement with the analytic tray-plus-supports-minus-cutouts volume. It also
requires a single connected solid after joining the studs. The default mesh
has 6,476 triangles and a volume within 0.002% of the analytic solid. Its Euler
characteristic is **0**: the closed SD window introduces one through-hole in
the solid's surface; the top-open JAE notch introduces none.
Its 32 segments per quarter-circle approximate the R5 exterior within 0.002 mm.
Independent slices of the exported STL at Z=5, 7.165, 7.185, 8.775 and
9.925 mm verified four support/pin cross-sections on the exact PCB hole
centers, with the expected diameters (6, 6, 3, 3 and 2.7 mm respectively).
Bottom-section checks at Z=0, 0.25, 0.5, 0.75 and 1 mm confirm the exterior
grows from 124 × 87 to 126 × 89 mm linearly through the chamfer; at Z=2
the full exterior size is retained.
For the access-opening revision, independent Boolean checks on the exported
STL confirmed the only removed material is the two specified wall openings
(656.1 mm³ total), that the complete openings contain no residual wall, and
that the rails below both openings and above the SD window remain solid.
The opening centers were checked against the extracted J5 pads and J1 F.Fab
outline, and the earlier case geometry is retained everywhere else.
No physical fit or print test has been performed.

Based on Accord by Jayson Gazeley — https://github.com/jgazeley/accord.
The case design and its generated representations use CERN-OHL-P-2.0;
see [LICENSE](../../LICENSE) and [NOTICE](../../NOTICE). This README and the
Python generator use Apache-2.0.
