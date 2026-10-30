#!/usr/bin/env python3
"""Create the starting Rev A board: outline and corner mounting holes only.

usage: python3 tools/gen_board_outline.py accord-logger.kicad_pcb

Run once. It REFUSES to overwrite an existing board, because after this the
owner places and routes by hand and the .kicad_pcb is theirs. Parts arrive
with KiCad's "Update PCB from Schematic"; the holes are marked board-only
(not in the schematic), so that update leaves them alone.

Envelope (DECISIONS D-ENVELOPE-01): generic rectangle 80 x 120 mm, no
enclosure, no mounting method chosen, so the holes commit to nothing:

  * Edge.Cuts 80 x 120 mm with 2 mm corner radii, as on the keyless board.
  * Four M3 holes, KiCad MountingHole_3.2mm_M3: 3.2 mm unplated, so no
    ground is tied to whatever the board is mounted on. Centres 4 mm in from
    each edge; the 6.4 mm courtyard then clears the edge by 0.8 mm.

The board origin sits at (100, 50) mm on the sheet, like keyless.
"""
import os
import sys

import pcbnew

W, H = 80.0, 120.0
X0, Y0 = 100.0, 50.0
R = 2.0
INSET = 4.0
HOLE_LIB = '/usr/share/kicad/footprints/MountingHole.pretty'
HOLE_FP = 'MountingHole_3.2mm_M3'

out = sys.argv[1]
if os.path.exists(out):
    sys.exit(f'{out} exists; refusing to overwrite the owner\'s board')

mm = pcbnew.FromMM
board = pcbnew.CreateEmptyBoard()
tb = board.GetTitleBlock()
tb.SetTitle('accord-logger Rev A')
tb.SetComment(0, 'Outline and mounting holes: tools/gen_board_outline.py')
board.SetTitleBlock(tb)
edge = board.GetLayerID('Edge.Cuts')


def seg(x1, y1, x2, y2):
    s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
    s.SetLayer(edge)
    s.SetWidth(mm(0.05))
    s.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    s.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    board.Add(s)


def arc(cx, cy, sx, sy, ex, ey):
    s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
    s.SetLayer(edge)
    s.SetWidth(mm(0.05))
    s.SetCenter(pcbnew.VECTOR2I(mm(cx), mm(cy)))
    s.SetStart(pcbnew.VECTOR2I(mm(sx), mm(sy)))
    s.SetEnd(pcbnew.VECTOR2I(mm(ex), mm(ey)))
    board.Add(s)


x1, y1, x2, y2 = X0, Y0, X0 + W, Y0 + H
seg(x1 + R, y1, x2 - R, y1)
seg(x2, y1 + R, x2, y2 - R)
seg(x2 - R, y2, x1 + R, y2)
seg(x1, y2 - R, x1, y1 + R)
# corners, each drawn clockwise from the straight edge before it
arc(x2 - R, y1 + R, x2 - R, y1, x2, y1 + R)
arc(x2 - R, y2 - R, x2, y2 - R, x2 - R, y2)
arc(x1 + R, y2 - R, x1 + R, y2, x1, y2 - R)
arc(x1 + R, y1 + R, x1, y1 + R, x1 + R, y1)

holes = [(x1 + INSET, y1 + INSET), (x2 - INSET, y1 + INSET),
         (x1 + INSET, y2 - INSET), (x2 - INSET, y2 - INSET)]
for n, (x, y) in enumerate(holes, 1):
    fp = pcbnew.FootprintLoad(HOLE_LIB, HOLE_FP)
    fp.SetFPID(pcbnew.LIB_ID('MountingHole', HOLE_FP))
    fp.SetReference(f'H{n}')
    fp.SetValue('M3 mounting hole')
    fp.Reference().SetVisible(False)   # no silk label needed on a hole
    fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_BOARD_ONLY
                     | pcbnew.FP_EXCLUDE_FROM_BOM
                     | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    board.Add(fp)

pcbnew.SaveBoard(out, board)
print('wrote', out, f'{W:g} x {H:g} mm, {len(holes)} M3 holes')
