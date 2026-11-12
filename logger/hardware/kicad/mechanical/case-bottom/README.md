# Simple logger case bottom

An open, flat-bottomed tray based on the 120 × 83 mm, R2 PCB outline.
The owner requested 4 mm walls, rounded corners and some clearance around
the PCB (DECISIONS D-CASE-31). The starting clearance, floor thickness and
depth below are adjustable modelling choices.

| Dimension | Value |
|---|---:|
| Wall thickness | 4 mm |
| Clearance from PCB edge to inside wall, each side | 1 mm |
| Inside width × length | 122 × 85 mm |
| Floor thickness | 4 mm |
| Internal depth above floor | 12 mm |
| Outside width × length × height | 130 × 93 × 16 mm |
| Inside corner radius | 3 mm |
| Outside corner radius | 7 mm |

The concentric corner offsets preserve the 1 mm PCB gap and 4 mm wall
thickness around the curves. These are rounded corners in plan; the floor
and rim edges are square. The interior floor is Z=4 and the rim is Z=16.
XY uses the same datum as the PCB reference, so the case spans X=-5..125
and Y=-5..88 mm.

- **`accord-logger-case-bottom.stl`**: closed, oriented mesh for a slicer or
  CAD mesh import. Interpret its coordinates as millimetres.
- **`accord-logger-case-bottom.scad`**: editable parametric OpenSCAD model.
  Change `clearance`, `wall`, `floor_thickness` and `internal_depth` at the top,
  then render/export in OpenSCAD. OpenSCAD is not installed on the generation
  host; the supplied STL was built directly from the same profile parameters.
- **`preview.png`**: illustration of the supplied STL geometry.
- **`dimensions.json`**: source PCB hash, dimensions and mesh check results.

This first tray has a plain floor and continuous walls. It does not yet have
PCB standoffs, fixing holes, a lid interface or connector openings. The fitted
SD module sits below the board and J1 overhangs its right edge; mounting
height and openings must accommodate those before this is an assembly-fit
case. The cavity dimensions describe bare PCB perimeter clearance only.

## Regenerate

From the repository root, using Python 3:

```sh
python3 logger/hardware/kicad/tools/build_case_bottom.py --preview
```

Pillow and NumPy are needed only for `--preview`. The mesh generator otherwise uses the
Python standard library and checks the current PCB hash against the extracted
reference. Options `--wall`, `--clearance`, `--floor`, `--depth` and
`--output-dir` produce variants. Generated files in the output directory are
overwritten; keep custom OpenSCAD edits separately if rerunning the generator.

The generator checks float32 STL coordinates for paired, oppositely directed
edges, Euler characteristic 2, nondegenerate faces, positive volume, bounding
dimensions and agreement with the analytic rounded-tray volume. The default
mesh has 1,056 triangles and a volume within 0.002% of the analytic solid.
Its 32 segments per quarter-circle approximate the R7 exterior within 0.003 mm.
No physical fit or print test has been performed.

Based on Accord by Jayson Gazeley — https://github.com/jgazeley/accord.
The case design and its generated representations use CERN-OHL-P-2.0;
see [LICENSE](../../LICENSE) and [NOTICE](../../NOTICE). This README and the
Python generator use Apache-2.0.
