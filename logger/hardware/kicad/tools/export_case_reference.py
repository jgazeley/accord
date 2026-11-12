#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Jayson Gazeley
"""Extract mechanical references without saving or modifying the source PCB.

Run with /usr/bin/python3 (KiCad's pcbnew module), from any directory.
The DXF contains exact lines/arcs and mounting holes only; STEP is bare PCB.
"""
import hashlib
import json
import math
from pathlib import Path
import subprocess

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'accord-logger.kicad_pcb'
OUT = ROOT / 'mechanical'


def main():
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    board = pcbnew.LoadBoard(str(SOURCE))
    edges = [d for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
    # This exporter handles the current rounded rectangle. Fail explicitly if
    # a future board introduces circles, splines or a different outline.
    if (len(edges) != 8 or
            sum(d.GetShape() == pcbnew.SHAPE_T_SEGMENT for d in edges) != 4 or
            sum(d.GetShape() == pcbnew.SHAPE_T_ARC for d in edges) != 4):
        raise ValueError('Expected four straight edges and four corner arcs')
    ends = [pcbnew.ToMM(p) for d in edges for p in (d.GetStart(), d.GetEnd())]
    x0, x1 = min(x for x, y in ends), max(x for x, y in ends)
    y0, y1 = min(y for x, y in ends), max(y for x, y in ends)
    width, height = round(x1 - x0, 6), round(y1 - y0, 6)

    def xy(p):
        x, y = pcbnew.ToMM(p)
        return [round(x - x0, 6), round(y1 - y, 6)]

    geometry = []
    for edge in edges:
        item = dict(start=xy(edge.GetStart()), end=xy(edge.GetEnd()))
        if edge.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            item['type'] = 'line'
        else:
            center = xy(edge.GetCenter())

            def angle(p):
                return math.degrees(math.atan2(p[1]-center[1], p[0]-center[0])) % 360

            start, end = angle(item['start']), angle(item['end'])
            mid = angle(xy(edge.GetArcMid()))
            if (mid-start) % 360 > (end-start) % 360:
                start, end = end, start
                item['start'], item['end'] = item['end'], item['start']
            sweep = (end-start) % 360
            if abs(sweep - 90) > 0.001:
                raise ValueError('Expected quarter-circle corners')
            item.update(type='arc', center=center,
                        radius=pcbnew.ToMM(edge.GetRadius()),
                        start_angle_deg=start, end_angle_deg=end)
        geometry.append(item)
    holes = []
    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        if not fp.GetReference().startswith('H'):
            continue
        pads = list(fp.Pads())
        if len(pads) != 1:
            raise ValueError(f'Unexpected mounting footprint: {fp.GetReference()}')
        pad = pads[0]
        dx, dy = pcbnew.ToMM(pad.GetDrillSize())
        if dx != dy or dx <= 0 or pad.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
            raise ValueError('Expected round, non-plated mounting holes')
        holes.append(dict(reference=fp.GetReference(), center=xy(pad.GetPosition()),
                          diameter=dx))
    if len(holes) != 4:
        raise ValueError('Expected four mounting holes')

    OUT.mkdir(exist_ok=True)
    data = dict(source=SOURCE.name, source_sha256=source_hash,
                license='CERN-OHL-P-2.0', units='mm',
                coordinates='Top view; origin lower-left; +X right, +Y up',
                kicad_origin_mm=[x0, y1], width=width, height=height,
                thickness=pcbnew.ToMM(board.GetDesignSettings().GetBoardThickness()),
                edges=geometry, mounting_holes=holes)
    (OUT / 'accord-logger-mechanical.json').write_text(json.dumps(data, indent=2) + '\n')

    dxf = []

    def emit(*pairs):
        for code, value in pairs:
            dxf.extend((str(code), str(value)))

    emit((999, 'Accord by Jayson Gazeley; CERN-OHL-P-2.0'),
         (0, 'SECTION'), (2, 'HEADER'), (9, '$ACADVER'), (1, 'AC1015'),
         (9, '$INSUNITS'), (70, 4), (9, '$MEASUREMENT'), (70, 1),
         (0, 'ENDSEC'), (0, 'SECTION'), (2, 'ENTITIES'))
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="150mm" height="112mm" '
           f'viewBox="-15 -15 150 112">',
           '<!-- Accord by Jayson Gazeley; CERN-OHL-P-2.0; units mm -->',
           '<rect x="-15" y="-15" width="150" height="112" fill="white"/>',
           f'<g transform="translate(0 {height}) scale(1 -1)" fill="none" '
           'stroke="#263238" stroke-width="0.25">']
    for edge in geometry:
        sx, sy = edge['start']
        ex, ey = edge['end']
        if edge['type'] == 'line':
            emit((0, 'LINE'), (100, 'AcDbEntity'), (8, 'BOARD_OUTLINE'),
                 (100, 'AcDbLine'), (10, sx), (20, sy), (30, 0),
                 (11, ex), (21, ey), (31, 0))
            svg.append(f'<path d="M {sx} {sy} L {ex} {ey}"/>')
        else:
            cx, cy = edge['center']
            r = edge['radius']
            emit((0, 'ARC'), (100, 'AcDbEntity'), (8, 'BOARD_OUTLINE'),
                 (100, 'AcDbCircle'), (10, cx), (20, cy), (30, 0), (40, r),
                 (100, 'AcDbArc'), (50, edge['start_angle_deg']), (51, edge['end_angle_deg']))
            svg.append(f'<path d="M {sx} {sy} A {r} {r} 0 0 1 {ex} {ey}"/>')
    for hole in holes:
        x, y = hole['center']
        r = hole['diameter'] / 2
        emit((0, 'CIRCLE'), (100, 'AcDbEntity'), (8, 'MOUNTING_HOLES'),
             (100, 'AcDbCircle'), (10, x), (20, y), (30, 0), (40, r))
        svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" stroke="#1565c0"/>')
    emit((0, 'ENDSEC'), (0, 'EOF'))
    (OUT / 'accord-logger-outline.dxf').write_text('\n'.join(dxf) + '\n')
    svg.extend(['</g>', '<g font-family="sans-serif" font-size="3" fill="#263238">',
                f'<text x="0" y="-8">Accord logger: {width:g} × {height:g} mm — top view</text>',
                '<text x="0" y="-3">R2 corners · 1.6 mm nominal PCB · four Ø3.2 holes</text>',
                f'<text x="0" y="{height+7}">Origin (0, 0): lower left; X right, Y up. All coordinates in mm.</text>'])
    for hole in holes:
        x, y = hole['center']
        right = x > width / 2
        anchor = 'end' if right else 'start'
        tx = x - 4 if right else x + 4
        svg.append(f'<text x="{tx}" y="{height-y+1}" text-anchor="{anchor}">'
                   f'{hole["reference"]} ({x:g}, {y:g})</text>')
    svg.extend(['</g>', '</svg>'])
    (OUT / 'accord-logger-reference.svg').write_text('\n'.join(svg) + '\n')
    subprocess.run(['kicad-cli', 'pcb', 'export', 'step', '--force', '--board-only',
                    '--user-origin', f'{x0:g}x{y1:g}mm', '-o',
                    str(OUT / 'accord-logger-board.step'), str(SOURCE)], check=True)
    step = OUT / 'accord-logger-board.step'
    step.write_text('\n'.join(line.rstrip() for line in step.read_text().splitlines()) + '\n')
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError('Source PCB changed during export; rerun on a stable file')
    print(f'Exported {width:g} × {height:g} mm board and {len(holes)} mounting holes to {OUT}')


if __name__ == '__main__':
    main()
