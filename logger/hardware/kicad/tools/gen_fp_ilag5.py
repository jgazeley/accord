#!/usr/bin/env python3
"""Generate JAE IL-AG5 double-row right-angle pin header footprints.

usage: python3 tools/gen_fp_ilag5.py 14 accord-logger.pretty/JAE_IL-AG5-14P-D3L2-A.kicad_mod

Generalised from the keyless project's 22P generator
(/srv/agent_share/pcb/hondaPico-kicad/gen_fp_ilag5.py, which produced
keyless/hardware/hondaPico.pretty/JAE_IL-AG5-22P-D3L2.kicad_mod). With 22 it
reproduces that footprint's pads, guide holes and outlines; check_capture.py
asserts so.

Source: JAE "IL-AG5 SERIES AUTOMOTIVE CONNECTORS, 025 Crimp Contacts"
catalogue, page 10, RIGHT ANGLE PIN HEADER, "PCB Hole Pattern (Ref.) - 14, 18,
22, 30 Contacts", and the double-row table (JAE catalogue "IL-AG5 Series Automotive Connectors"; a local copy is at docs/IL-AG5_Series.pdf, not committed):

  contacts  part               A     B     C1    C2
  14        IL-AG5-14P-D3L2-A  20.0  26.5  12.5  6.25
  18        IL-AG5-18P-D3L2    25.0  31.5  17.5  8.75
  22        IL-AG5-22P-D3L2    30.0  36.5  22.5  11.25
  30        IL-AG5-30P-D3L2    40.0  46.5  30.0  15.00

Hole pattern as drawn (16 contacts has its own drawing and is not covered):
  * Columns on a 2.5 mm pitch, A end to end, so A/2.5 + 1 columns.
  * The row nearer the body omits the centre column (the drawing's 5.0 mm
    gap). The outer row omits the centre column and one either side (a 10 mm
    gap). That gives 14 = 6 + 8, 18 = 8 + 10, 22 = 10 + 12, 30 = 14 + 16.
  * Rows 6.0 mm apart on the PCB (3.0 mm at the mating face).
  * Two 2.2 mm board-guide holes, C1 apart, centred, 8.6 mm beyond the near
    row, under the body; they take moulded posts, so NPTH.
  * Contact holes 1.1 mm (0.64 mm square pins).
  * Body B wide x 18.2 deep, back face 7.0 mm from the guide-hole line.

NUMBERING ASSUMPTION, as in the keyless 22P (verify against the housing's
moulded cavity numbers before crimping a harness): pin 1 is the outer row,
left end seen from the mating face; the outer row is numbered first, left to
right, then the near row from the same end.
"""
import sys

TABLE = {14: (20.0, 26.5, 12.5, 'IL-AG5-14P-D3L2-A'),
         18: (25.0, 31.5, 17.5, 'IL-AG5-18P-D3L2'),
         22: (30.0, 36.5, 22.5, 'IL-AG5-22P-D3L2'),
         30: (40.0, 46.5, 30.0, 'IL-AG5-30P-D3L2')}

PITCH = 2.5
ROW_DY = 6.0
GUIDE_DY = 8.6
BODY_DEEP = 18.2
BODY_BACK = 7.0
DRILL = 1.1
PAD = 2.0
GUIDE_DRILL = 2.2


def geometry(n):
    """Pads [(number, x, y)], guide holes, body and courtyard boxes."""
    a, b, c1, part = TABLE[n]
    ncol = round(a / PITCH) + 1
    mid = ncol // 2
    cols = [i * PITCH for i in range(ncol)]
    outer = [cols[i] for i in range(ncol) if abs(i - mid) > 1]
    inner = [cols[i] for i in range(ncol) if i != mid]
    pads = ([(k + 1, x, 0.0) for k, x in enumerate(outer)]
            + [(k + 1 + len(outer), x, -ROW_DY) for k, x in enumerate(inner)])
    assert len(pads) == n, (n, len(pads))
    cx = a / 2
    gy = -ROW_DY - GUIDE_DY
    guides = [(cx - c1 / 2, gy), (cx + c1 / 2, gy)]
    body = dict(x1=cx - b / 2, x2=cx + b / 2,
                y1=gy - (BODY_DEEP - BODY_BACK), y2=gy + BODY_BACK)
    court = dict(x1=body['x1'] - 0.5, x2=body['x2'] + 0.5,
                 y1=body['y1'] - 0.5, y2=PAD / 2 + 0.25)
    return part, len(outer), len(inner), pads, guides, body, court


def f(v):
    return f'{v:.4f}'.rstrip('0').rstrip('.') or '0'


def line(x1, y1, x2, y2, layer, width):
    return (f'\t(fp_line\n\t\t(start {f(x1)} {f(y1)})\n\t\t(end {f(x2)} {f(y2)})\n'
            f'\t\t(stroke\n\t\t\t(width {width})\n\t\t\t(type solid)\n\t\t)\n'
            f'\t\t(layer "{layer}")\n\t)')


def box(d, layer, width):
    return [line(d['x1'], d['y1'], d['x2'], d['y1'], layer, width),
            line(d['x2'], d['y1'], d['x2'], d['y2'], layer, width),
            line(d['x2'], d['y2'], d['x1'], d['y2'], layer, width),
            line(d['x1'], d['y2'], d['x1'], d['y1'], layer, width)]


def prop(name, value, x, y, layer, hide=False):
    h = '\n\t\t(hide yes)' if hide else ''
    return (f'\t(property "{name}" "{value}"\n\t\t(at {f(x)} {f(y)} 0)\n'
            f'\t\t(layer "{layer}"){h}\n\t\t(effects\n\t\t\t(font\n'
            f'\t\t\t\t(size 1 1)\n\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t)\n\t)')


def footprint(n):
    part, no, ni, pads, guides, body, court = geometry(n)
    name = 'JAE_' + part
    cx = TABLE[n][0] / 2
    out = [f'(footprint "{name}"',
           '\t(version 20241229)',
           '\t(generator "gen_fp_ilag5.py")',
           '\t(layer "F.Cu")',
           f'\t(descr "JAE {part}, {n} contacts ({no} + {ni}), 2.5 mm pitch, '
           'right-angle through-hole shrouded pin header, board guides. Hole '
           'pattern from the JAE IL-AG5 catalogue, RIGHT ANGLE PIN HEADER page'
           '. Pin 1 = outer row, left end from the '
           'mating face -- verify against the housing cavity numbers.")',
           f'\t(tags "connector JAE IL-AG5 automotive 2.5mm right_angle {n}P")',
           prop('Reference', 'REF**', cx, body['y1'] - 1.5, 'F.SilkS'),
           prop('Value', name, cx, court['y2'] + 1.5, 'F.Fab'),
           prop('Datasheet', '', cx, 0, 'F.Fab', hide=True),
           prop('Description', '', cx, 0, 'F.Fab', hide=True),
           '\t(attr through_hole)']
    # silkscreen body, mating face drawn thicker, pin-1 marker outside the pads
    out += box(body, 'F.SilkS', 0.12)
    out.append(line(body['x1'], body['y1'], body['x2'], body['y1'], 'F.SilkS', 0.3))
    out.append(line(-1.4, -1.4, -1.4, 1.4, 'F.SilkS', 0.3))
    out.append(line(-1.4, 1.4, 0.6, 1.4, 'F.SilkS', 0.3))
    out += box(body, 'F.Fab', 0.1)
    out += box(court, 'F.CrtYd', 0.05)
    for k, x, y in pads:
        shape = 'rect' if k == 1 else 'circle'
        out.append(f'\t(pad "{k}" thru_hole {shape}\n\t\t(at {f(x)} {f(y)})\n'
                   f'\t\t(size {f(PAD)} {f(PAD)})\n\t\t(drill {f(DRILL)})\n'
                   '\t\t(layers "*.Cu" "*.Mask")\n\t\t(remove_unused_layers no)\n\t)')
    for x, y in guides:
        out.append(f'\t(pad "" np_thru_hole circle\n\t\t(at {f(x)} {f(y)})\n'
                   f'\t\t(size {f(GUIDE_DRILL)} {f(GUIDE_DRILL)})\n'
                   f'\t\t(drill {f(GUIDE_DRILL)})\n\t\t(layers "*.Cu" "*.Mask")\n\t)')
    out.append('\t(embedded_fonts no)')
    out.append(')')
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    n = int(sys.argv[1])
    path = sys.argv[2]
    open(path, 'w').write(footprint(n))
    print('wrote', path, 'pads:', n, '+ 2 NPTH')
