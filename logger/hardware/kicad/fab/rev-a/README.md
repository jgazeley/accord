# Rev A fab package

Upload `accord-logger-rev-a-gerbers.zip` to the fab. It holds the
gerbers (copper, mask, silkscreen and paste for both sides, and the
Edge.Cuts outline), separate Excellon drill files for plated (PTH) and
non-plated (NPTH) holes in mm, the drill maps and the gerber job file.

- Board: 120 x 83 mm, 2 layers, 1.6 mm, 1 oz.
- Minimums used: 0.2 mm track and clearance, 0.3 mm drill, 0.13 mm
  annular ring, 0.5 mm hole-to-hole and copper-to-edge, 1.0 mm text.
- J1 overhangs the right-hand edge on purpose (DECISIONS D-CONN-23); only
  its silkscreen crosses the edge.
- Hand assembly: the paste layers are included but no stencil is needed.

Plotted October 31, 2026 with KiCad 9.0.2 from the board at commit
67e5f21, with its 11 accepted DRC exclusions (D-DRC-24) and the ground
pour as saved:

    kicad-cli pcb export gerbers --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,F.Paste,B.Paste,Edge.Cuts --subtract-soldermask -o fab/ accord-logger.kicad_pcb
    kicad-cli pcb export drill --format excellon --excellon-separate-th --excellon-units mm --generate-map --map-format gerberx2 -o fab/ accord-logger.kicad_pcb

Run them on a copy of the project. Regenerate this package if the board
changes, and say so in its commit. The parts order is
`../../order/digikey_rev_a.csv`.
