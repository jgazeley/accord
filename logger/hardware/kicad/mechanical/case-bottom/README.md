# Simple logger case bottom

An open tray with four stepped locating studs, based on the 120 × 83 mm,
R2 PCB outline and its actual mounting-hole centers.
The owner requested rounded corners and some clearance around the PCB,
revising the walls from 4 mm to 2 mm (DECISIONS D-CASE-31 and D-CASE-33).
The starting clearance, floor thickness and
depth below are adjustable modelling choices. The owner subsequently
requested wider supports raising the PCB about a quarter inch, narrowing
to pins that fit through its mounting holes (D-CASE-32).

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
| PCB underside height above inside floor | 6.35 mm (¼ inch) |
| Support shoulder diameter | 6 mm |
| Locating pin diameter / PCB hole diameter | 3.0 / 3.2 mm |
| Pin height above shoulder | 3 mm |
| Lead-in tip | Last 0.5 mm tapers to Ø2.4 mm |

The concentric corner offsets preserve the 1 mm PCB gap and 2 mm wall
thickness around the curves. These are rounded corners in plan; the floor
and rim edges are square. The interior floor is Z=4 and the rim is Z=16.
XY uses the same datum as the PCB reference, so the case spans X=-3..123
and Y=-3..86 mm.

## PCB supports

The PCB rests on the four Ø6 mm shoulders at **Z=10.35 mm**, 6.35 mm above
the inside floor. The narrower pins enter the board holes. A nominal 1.6 mm
PCB has its upper surface at Z=11.95 mm; pin tips reach Z=13.35 mm, leaving
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

## Files

- **`accord-logger-case-bottom.stl`**: closed, oriented mesh for a slicer or
  CAD mesh import. Interpret its coordinates as millimetres.
- **`accord-logger-case-bottom.scad`**: editable parametric OpenSCAD model.
  Change the case and support parameters at the top,
  then render/export in OpenSCAD. OpenSCAD is not installed on the generation
  host; the supplied STL was built directly from the same profile parameters.
- **`preview.png`**: illustration of the supplied STL geometry.
- **`dimensions.json`**: source PCB hash, dimensions and mesh check results.

The walls remain continuous; fixing holes, a lid interface and connector
openings have not been added. The fitted SD module sits below the board and
J1 overhangs its right edge. Check that the assembly clears the floor at the
requested 6.35 mm support height and add connector openings before treating
this as an assembly-fit case. Cavity dimensions describe PCB clearance.

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
Options `--wall`, `--clearance`, `--floor`, `--depth`, `--support-height`,
`--support-diameter`, `--pin-clearance`, `--pin-height` and `--output-dir`
produce variants. Pin clearance is **diametral**, subtracted from each PCB
hole diameter. Generated files in the output directory are
overwritten; keep custom OpenSCAD edits separately if rerunning the generator.

The generator checks float32 STL coordinates for paired, oppositely directed
edges, Euler characteristic 2, nondegenerate faces, positive volume, bounding
dimensions and agreement with the analytic tray-plus-supports volume. It also
requires a single connected solid after joining the studs. The default mesh
has 6,176 triangles and a volume within 0.002% of the analytic solid.
Its 32 segments per quarter-circle approximate the R5 exterior within 0.002 mm.
Independent slices of the exported STL at Z=7, 10.34, 10.36, 11.95 and
13.1 mm verified four support/pin cross-sections on the exact PCB hole
centers, with the expected diameters (6, 6, 3, 3 and 2.7 mm respectively).
No physical fit or print test has been performed.

Based on Accord by Jayson Gazeley — https://github.com/jgazeley/accord.
The case design and its generated representations use CERN-OHL-P-2.0;
see [LICENSE](../../LICENSE) and [NOTICE](../../NOTICE). This README and the
Python generator use Apache-2.0.
