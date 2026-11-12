#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Jayson Gazeley
"""Build a plain open tray from the extracted PCB envelope.

STL and editable OpenSCAD output use millimetres. Python's standard library
builds and checks the mesh; Pillow and NumPy render the optional preview.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parents[1]


def sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wall', type=float, default=4)
    parser.add_argument('--clearance', type=float, default=1, help='PCB edge gap per side')
    parser.add_argument('--floor', type=float, default=4)
    parser.add_argument('--depth', type=float, default=12, help='Interior depth above floor')
    parser.add_argument('--preview', action='store_true', help='Render PNG using Pillow and NumPy')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'mechanical/case-bottom')
    args = parser.parse_args()
    if not all(math.isfinite(v) and v > 0 for v in
               (args.wall, args.clearance, args.floor, args.depth)):
        parser.error('All dimensions must be finite and positive')
    data = json.loads((ROOT / 'mechanical/accord-logger-mechanical.json').read_text())
    if hashlib.sha256((ROOT / data['source']).read_bytes()).hexdigest() != data['source_sha256']:
        raise ValueError('PCB changed: rerun export_case_reference.py first')
    w, h = data['width'], data['height']
    arcs = [e for e in data['edges'] if e['type'] == 'arc']
    radii = {e['radius'] for e in arcs}
    if len(arcs) != 4 or len(radii) != 1:
        raise ValueError('Expected a rounded rectangular PCB')
    r = radii.pop()
    centers = [(w-r, r), (w-r, h-r), (r, h-r), (r, r)]
    if {tuple(e['center']) for e in arcs} != set(centers):
        raise ValueError('Unexpected PCB corner centers')
    c, t, f, depth = args.clearance, args.wall, args.floor, args.depth
    height = f + depth
    segments = 32  # per quarter-circle: <0.003 mm chord error at R7

    def ring(radius, z):
        return [(cx+radius*math.cos(math.radians(start+90*j/segments)),
                 cy+radius*math.sin(math.radians(start+90*j/segments)), z)
                for (cx, cy), start in zip(centers, (-90, 0, 90, 180))
                for j in range(segments+1)]

    rings = [ring(r+c+t, 0), ring(r+c+t, height),
             ring(r+c, height), ring(r+c, f)]
    n = len(rings[0])
    vertices = [p for ring_points in rings for p in ring_points]
    vertices += [(w/2, h/2, 0), (w/2, h/2, f)]
    faces = []
    for i in range(n):
        j = (i+1) % n
        # Outer wall, rim, inner wall, bottom, then cavity floor.
        faces.extend([(i, j, n+j), (i, n+j, n+i),
                      (n+i, n+j, 2*n+j), (n+i, 2*n+j, 2*n+i),
                      (3*n+i, 2*n+j, 3*n+j), (3*n+i, 2*n+i, 2*n+j),
                      (4*n, j, i), (4*n+1, 3*n+i, 3*n+j)])

    # Check the actual float32 geometry that will be written to STL.
    vertices = [struct.unpack('<3f', struct.pack('<3f', *p)) for p in vertices]
    directed = Counter((face[i], face[(i+1) % 3]) for face in faces for i in range(3))
    assert all(count == 1 and directed[b, a] == 1 for (a, b), count in directed.items())
    assert len(vertices) - len(directed)//2 + len(faces) == 2
    normals = []
    volume = 0
    for face in faces:
        a, b, q = (vertices[i] for i in face)
        normal = cross(sub(b, a), sub(q, a))
        length = math.sqrt(dot(normal, normal))
        assert length > 1e-10
        normals.append(tuple(v/length for v in normal))
        volume += dot(a, cross(b, q))/6

    def area(gap):
        radius = r+gap
        return (w+2*gap)*(h+2*gap) - (4-math.pi)*radius**2

    exact_volume = area(c+t)*height - area(c)*depth
    assert volume > 0 and abs(volume/exact_volume - 1) < 0.0001
    bounds = [[min(v[k] for v in vertices), max(v[k] for v in vertices)] for k in range(3)]
    expected = [[-c-t, w+c+t], [-c-t, h+c+t], [0, height]]
    assert all(abs(a-b) < 0.0001 for row, ref in zip(bounds, expected) for a, b in zip(row, ref))

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    with (out / 'accord-logger-case-bottom.stl').open('wb') as stream:
        stream.write(b'Accord by Jayson Gazeley; CERN-OHL-P-2.0; units mm'.ljust(80, b'\0'))
        stream.write(struct.pack('<I', len(faces)))
        for face, normal in zip(faces, normals):
            coords = [value for i in face for value in vertices[i]]
            stream.write(struct.pack('<12fH', *normal, *coords, 0))
    scad = f'''// SPDX-License-Identifier: CERN-OHL-P-2.0
// Copyright 2026 Jayson Gazeley — https://github.com/jgazeley/accord
// Plain case bottom. Millimetres; same XY datum as the PCB reference.
// Generated by tools/build_case_bottom.py; edit these dimensions in OpenSCAD.
pcb_width = {w:g};
pcb_height = {h:g};
pcb_radius = {r:g};
clearance = {c:g};  // gap on EACH side of the PCB
wall = {t:g};
floor_thickness = {f:g};
internal_depth = {depth:g};
$fn = 128;

assert(clearance > 0 && wall > 0 && floor_thickness > 0 && internal_depth > 0);

module profile(gap) {{
    hull()
        for (x = [pcb_radius, pcb_width-pcb_radius])
            for (y = [pcb_radius, pcb_height-pcb_radius])
                translate([x,y]) circle(r=pcb_radius+gap);
}}

difference() {{
    linear_extrude(height=floor_thickness+internal_depth)
        profile(clearance+wall);
    translate([0,0,floor_thickness])
        linear_extrude(height=internal_depth+0.1)
            profile(clearance);
}}
'''
    (out / 'accord-logger-case-bottom.scad').write_text(scad)
    report = dict(units='mm', source_pcb_sha256=data['source_sha256'],
                  pcb=[w, h], clearance_per_side=c, wall=t, floor=f, internal_depth=depth,
                  outside=[w+2*(c+t), h+2*(c+t), height], inside=[w+2*c, h+2*c, depth],
                  inner_corner_radius=r+c, outer_corner_radius=r+c+t,
                  triangles=len(faces), bounds=bounds, mesh_volume_mm3=round(volume, 6),
                  analytic_volume_mm3=round(exact_volume, 6),
                  validation='Closed oriented manifold, Euler characteristic 2, positive volume; bounds and volume checked')
    (out / 'dimensions.json').write_text(json.dumps(report, indent=2)+'\n')
    if args.preview:
        preview(out, vertices, faces, normals, report)
    print(json.dumps(report, indent=2))


def preview(out, vertices, faces, normals, report):
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    scale = 2
    image = Image.new('RGB', (1100*scale, 820*scale), '#f4f6fa')
    eye = (0.78, -0.78, 0.9)

    def project(p):
        x, y, z = p
        return ((x+y)*0.7071, (-x+y)*0.45+z*0.78)

    points = [project(p) for p in vertices]
    x0, x1 = min(p[0] for p in points), max(p[0] for p in points)
    y0, y1 = min(p[1] for p in points), max(p[1] for p in points)
    factor = min(950/(x1-x0), 450/(y1-y0))
    left = (1100-(x1-x0)*factor)/2
    pixels = [((left+(x-x0)*factor)*scale, (140+(y1-y)*factor)*scale) for x, y in points]
    canvas = np.array(image)
    zbuffer = np.full(canvas.shape[:2], -np.inf)
    for i, face in enumerate(faces):
        normal = normals[i]
        if dot(normal, eye) <= 0:
            continue
        brightness = 0.6+0.4*max(0, dot(normal, (0.2, -0.4, 0.894)))
        if all(abs(vertices[v][2]-report['floor']) < 1e-6 for v in face):
            brightness *= 0.86  # Shade the recessed floor for clarity.
        color = tuple(int(c*brightness) for c in (100, 155, 197))
        a, b, c = [pixels[v] for v in face]
        xmin = max(0, math.floor(min(a[0], b[0], c[0])))
        xmax = min(canvas.shape[1]-1, math.ceil(max(a[0], b[0], c[0])))
        ymin = max(0, math.floor(min(a[1], b[1], c[1])))
        ymax = min(canvas.shape[0]-1, math.ceil(max(a[1], b[1], c[1])))
        yy, xx = np.mgrid[ymin:ymax+1, xmin:xmax+1]
        denominator = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(denominator) < 1e-9:
            continue
        u = ((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/denominator
        v = ((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/denominator
        q = 1-u-v
        depths = [dot(vertices[v], eye) for v in face]
        z = u*depths[0]+v*depths[1]+q*depths[2]
        region = zbuffer[ymin:ymax+1, xmin:xmax+1]
        visible = (u >= -1e-6) & (v >= -1e-6) & (q >= -1e-6) & (z > region)
        region[visible] = z[visible]
        canvas[ymin:ymax+1, xmin:xmax+1][visible] = color
    image = Image.fromarray(canvas)
    draw = ImageDraw.Draw(image)
    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    title = ImageFont.truetype(font_path, 28*scale)
    font = ImageFont.truetype(font_path, 20*scale)
    draw.text((55*scale, 40*scale), 'Accord logger — simple case bottom', font=title, fill='#24394b')
    w, h, z = report['outside']
    lines = [f'{w:g} × {h:g} × {z:g} mm outside',
             f'{report["wall"]:g} mm walls / {report["floor"]:g} mm floor / {report["internal_depth"]:g} mm internal depth',
             f'{report["clearance_per_side"]:g} mm PCB clearance per side · rounded corners',
             'Plain tray; component clearance and mounting details still to be fitted.']
    for i, line in enumerate(lines):
        draw.text((55*scale, (650+32*i)*scale), line, font=font, fill='#24394b')
    image.resize((1100, 820), Image.Resampling.LANCZOS).save(out / 'preview.png')


if __name__ == '__main__':
    main()
