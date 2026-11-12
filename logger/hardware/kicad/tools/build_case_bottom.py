#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Jayson Gazeley
"""Build an open tray with stepped locating studs at the PCB mounting holes.

STL and editable OpenSCAD output use millimetres. Manifold3D and NumPy join
the supports to the floor; Pillow renders the optional preview.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct

import manifold3d
import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wall', type=float, default=2)
    parser.add_argument('--clearance', type=float, default=1, help='PCB edge gap per side')
    parser.add_argument('--floor', type=float, default=4)
    parser.add_argument('--depth', type=float, default=12, help='Interior depth above floor')
    parser.add_argument('--bottom-chamfer', type=float, default=1, help='Exterior bottom bevel: equal XY and Z setback')
    parser.add_argument('--support-height', type=float, default=3.175, help='PCB underside above inside floor')
    parser.add_argument('--support-diameter', type=float, default=6)
    parser.add_argument('--pin-clearance', type=float, default=0.2, help='DIAMETRAL clearance in PCB holes')
    parser.add_argument('--pin-height', type=float, default=3, help='Total pin height above shoulder')
    parser.add_argument('--opening-clearance', type=float, default=0.5, help='Opening allowance on each side of body envelope')
    parser.add_argument('--sd-body-width', type=float, default=28.8, help='Provisional SD socket width from SD-slot.jpg')
    parser.add_argument('--sd-body-height', type=float, default=2.75, help='Provisional SD socket height above its seating plane')
    parser.add_argument('--sd-base-offset', type=float, default=0, help='SD socket seating plane above main PCB top')
    parser.add_argument('--jae-base-offset', type=float, default=0, help='J1 seating plane above main PCB top')
    parser.add_argument('--preview', action='store_true', help='Render PNG using Pillow and NumPy')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'mechanical/case-bottom')
    args = parser.parse_args()
    if not all(math.isfinite(v) and v > 0 for v in
               (args.wall, args.clearance, args.floor, args.depth, args.bottom_chamfer,
                args.support_height, args.support_diameter, args.pin_clearance, args.pin_height,
                args.opening_clearance, args.sd_body_width, args.sd_body_height)):
        parser.error('All dimensions must be finite and positive')
    if not all(math.isfinite(v) and v >= 0 for v in (args.sd_base_offset, args.jae_base_offset)):
        parser.error('Socket offsets above the PCB must be finite and nonnegative')
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
    bevel = args.bottom_chamfer
    if bevel > t or bevel >= f:
        parser.error('Bottom chamfer must not exceed wall thickness and must be below floor thickness')
    holes = data['mounting_holes']
    support_height, support_radius = args.support_height, args.support_diameter/2
    pin_height, tip_height, tip_diameter_reduction = args.pin_height, 0.5, 0.6
    seat_z = f+support_height
    pcb_top_z = seat_z+data['thickness']
    interfaces = data['interfaces']
    jae, sd = interfaces['J1'], interfaces['J5']
    jae_lo, jae_hi = jae['fab_bounds']
    # J1 faces the +X edge; J5's pin row is parallel to the -Y wall.
    if (jae['footprint'] != 'JAE_IL-AG5-14P-D3L2-A' or jae['layer'] != 'F.Cu'
            or not math.isclose(jae_hi[1]-jae_lo[1], 26.5)
            or not math.isclose(jae_hi[0]-jae_lo[0], 18.2)
            or jae_hi[0] < w):
        parser.error('J1 placement changed: review opening wall and alignment')
    sd_x, sd_y = sd['pin_span_center']
    if (any(abs(p['center'][1]-sd_y) > 1e-5 for p in sd['numbered_pad_centers'])
            or sd_y >= min(sd_x, w-sd_x, h-sd_y)):
        parser.error('J5 placement changed: review projected SD access wall')
    jae_center_y = (jae_lo[1]+jae_hi[1])/2
    margin = args.opening_clearance
    # JAE catalogue page 10: body B=26.5 +/-0.5, height=15 +/-0.5 mm.
    jae_width, jae_height, jae_tolerance = 26.5, 15, 0.5
    cutouts = []
    for ref, center, body_w, body_h, tolerance, offset, wall_name in (
            ('J5', sd_x, args.sd_body_width, args.sd_body_height, 0, args.sd_base_offset, 'front (-Y)'),
            ('J1', jae_center_y, jae_width, jae_height, jae_tolerance, args.jae_base_offset, 'right (+X)')):
        opening_width = body_w+tolerance+2*margin
        z0 = pcb_top_z+offset-margin
        z1 = pcb_top_z+offset+body_h+tolerance+margin
        limit = w if ref == 'J5' else h
        if center-opening_width/2 <= r or center+opening_width/2 >= limit-r:
            parser.error(f'{ref} opening reaches a rounded case corner')
        if not f < z0 < height:
            parser.error(f'{ref} opening must start above the floor and below the rim')
        if ref == 'J5':
            origin = [center-opening_width/2, -c-t-0.1, z0]
            size = [opening_width, t+0.2, z1-z0]
        else:
            origin = [w+c-0.1, center-opening_width/2, z0]
            size = [t+0.2, opening_width, z1-z0]
        cutouts.append(dict(reference=ref, wall=wall_name, center_along_wall=center,
                            width=opening_width, nominal_body_size=[body_w, body_h],
                            positive_body_tolerance=tolerance, clearance_each_side=margin,
                            base_offset_above_pcb=offset, requested_z_range=[z0, z1],
                            actual_z_range=[z0, min(z1, height)],
                            kind='window' if z1 < height else 'top-open notch',
                            cutter_origin=origin, cutter_size=size,
                            removed_volume_mm3=opening_width*t*(min(z1, height)-z0)))
    if pin_height <= max(tip_height, data['thickness']):
        parser.error('Pins must extend through the PCB and exceed the 0.5 mm tip height')
    if support_height+pin_height > depth:
        parser.error('Support and pin must fit below the case rim')
    for hole in holes:
        if not tip_diameter_reduction < hole['diameter']-args.pin_clearance < args.support_diameter:
            parser.error('Pin must fit the hole, have a positive tip and be narrower than the support')
        # The circular shoulder must sit within the PCB perimeter. This also
        # keeps the base clear of the case wall for the four corner locations.
        x, y = hole['center']
        if min(x, w-x, y, h-y) < support_radius:
            parser.error('Support diameter extends beyond the PCB edge')
    segments = 32  # per quarter-circle: <0.003 mm chord error at R7

    def ring(radius, z):
        return [(cx+radius*math.cos(math.radians(start+90*j/segments)),
                 cy+radius*math.sin(math.radians(start+90*j/segments)), z)
                for (cx, cy), start in zip(centers, (-90, 0, 90, 180))
                for j in range(segments+1)]

    rings = [ring(r+c+t-bevel, 0), ring(r+c+t, bevel), ring(r+c+t, height),
             ring(r+c, height), ring(r+c, f)]
    n = len(rings[0])
    vertices = [p for ring_points in rings for p in ring_points]
    vertices += [(w/2, h/2, 0), (w/2, h/2, f)]
    faces = []
    for i in range(n):
        j = (i+1) % n
        # Bevel, outer wall, rim and inner wall, then bottom and cavity floor.
        for band in range(4):
            a, b = band*n, (band+1)*n
            faces.extend([(a+i, a+j, b+j), (a+i, b+j, b+i)])
        faces.extend([(5*n, j, i), (5*n+1, 4*n+i, 4*n+j)])

    solid = manifold3d.Manifold(manifold3d.Mesh(
        np.array(vertices, dtype=np.float32), np.array(faces, dtype=np.uint32)))
    supports = []
    for hole in holes:
        x, y = hole['center']
        pin_radius = (hole['diameter']-args.pin_clearance)/2
        tip_radius = pin_radius-tip_diameter_reduction/2
        # Sink the base 0.05 mm into the floor for an unambiguous solid union.
        base = manifold3d.Manifold.cylinder(support_height+0.05, support_radius,
                    circular_segments=128).translate((x, y, f-0.05))
        pin = manifold3d.Manifold.cylinder(pin_height-tip_height, pin_radius,
                    circular_segments=128).translate((x, y, seat_z))
        tip = manifold3d.Manifold.cylinder(tip_height, pin_radius, tip_radius,
                    circular_segments=128).translate((x, y, seat_z+pin_height-tip_height))
        solid = solid+base+pin+tip
        supports.append(dict(reference=hole['reference'], center=[x, y],
                             shoulder_z=seat_z, base_diameter=2*support_radius,
                             pin_diameter=round(2*pin_radius, 6),
                             tip_diameter=round(2*tip_radius, 6)))
    for cutout in cutouts:
        cutter = manifold3d.Manifold.cube(cutout['cutter_size']).translate(cutout['cutter_origin'])
        solid = solid-cutter
    assert solid.status() == manifold3d.Error.NoError
    assert len(solid.decompose()) == 1, 'Studs must be joined to the floor'
    mesh = solid.to_mesh()
    vertices = mesh.vert_properties[:, :3].tolist()
    faces = mesh.tri_verts.tolist()

    # Check the actual float32 geometry that will be written to STL.
    vertices = [struct.unpack('<3f', struct.pack('<3f', *p)) for p in vertices]
    directed = Counter((face[i], face[(i+1) % 3]) for face in faces for i in range(3))
    assert all(count == 1 and directed[b, a] == 1 for (a, b), count in directed.items())
    # A closed window through a wall adds a handle; a top-open notch does not.
    expected_euler = 2-2*sum(c['kind'] == 'window' for c in cutouts)
    assert len(vertices) - len(directed)//2 + len(faces) == expected_euler
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

    # Cross-sectional area is quadratic in offset: Simpson's rule is exact.
    bevel_volume = bevel*(area(c+t-bevel)+4*area(c+t-bevel/2)+area(c+t))/6
    exact_volume = area(c+t)*(height-bevel)+bevel_volume-area(c)*depth
    for support in supports:
        pr, tr = support['pin_diameter']/2, support['tip_diameter']/2
        exact_volume += math.pi*(support_radius**2*support_height
                                 + pr**2*(pin_height-tip_height)
                                 + tip_height*(pr**2+pr*tr+tr**2)/3)
    exact_volume -= sum(c['removed_volume_mm3'] for c in cutouts)
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
// Case bottom with locating studs. Millimetres; same XY datum as the PCB.
// Generated by tools/build_case_bottom.py; edit these dimensions in OpenSCAD.
pcb_width = {w:g};
pcb_height = {h:g};
pcb_radius = {r:g};
clearance = {c:g};  // gap on EACH side of the PCB
wall = {t:g};
floor_thickness = {f:g};
internal_depth = {depth:g};
bottom_chamfer = {bevel:g};  // 45-degree exterior bottom edge, horizontal and vertical
support_height = {support_height:g};  // PCB underside above the INSIDE floor
support_diameter = {2*support_radius:g};
pin_clearance = {args.pin_clearance:g};  // DIAMETRAL clearance in each PCB hole
pin_height = {pin_height:g};  // includes the tapered tip
tip_height = {tip_height:g};
tip_diameter_reduction = {tip_diameter_reduction:g};
pcb_thickness = {data['thickness']:g};
pcb_top_z = floor_thickness+support_height+pcb_thickness;
opening_clearance = {margin:g};
sd_center_x = {sd_x:g};  // midpoint of J5 pins projected to front (-Y) wall
sd_body_width = {args.sd_body_width:g};
sd_body_height = {args.sd_body_height:g};
sd_base_offset = {args.sd_base_offset:g};  // PROVISIONAL: directly above PCB per owner
jae_center_y = {jae_center_y:g};  // J1 F.Fab body midpoint, right (+X) wall
jae_body_width = {jae_width:g};
jae_body_height = {jae_height:g};
jae_positive_tolerance = {jae_tolerance:g};
jae_base_offset = {args.jae_base_offset:g};
sd_opening_width = sd_body_width+2*opening_clearance;
jae_opening_width = jae_body_width+jae_positive_tolerance+2*opening_clearance;
// x, y, PCB hole diameter; H1, H2, H3, H4 (asymmetric lower holes).
mounts = {json.dumps([h['center']+[h['diameter']] for h in holes])};
$fn = 128;

assert(clearance > 0 && wall > 0 && floor_thickness > 0 && internal_depth > 0);
assert(bottom_chamfer > 0 && bottom_chamfer <= wall && bottom_chamfer < floor_thickness);
assert(support_height > 0 && support_height+pin_height <= internal_depth);
assert(pin_clearance > 0 && pin_height > max(pcb_thickness, tip_height));
assert(opening_clearance > 0 && sd_base_offset >= 0 && jae_base_offset >= 0);
assert(sd_body_width > 0 && sd_body_height > 0);
assert(pcb_top_z+sd_base_offset-opening_clearance > floor_thickness);
assert(pcb_top_z+jae_base_offset-opening_clearance > floor_thickness);

module profile(gap) {{
    hull()
        for (x = [pcb_radius, pcb_width-pcb_radius])
            for (y = [pcb_radius, pcb_height-pcb_radius])
                translate([x,y]) circle(r=pcb_radius+gap);
}}

module case_body() {{ union() {{
    difference() {{
        union() {{
            hull()
                for (x = [pcb_radius, pcb_width-pcb_radius])
                    for (y = [pcb_radius, pcb_height-pcb_radius])
                        translate([x,y,0])
                            cylinder(h=bottom_chamfer,
                                r1=pcb_radius+clearance+wall-bottom_chamfer,
                                r2=pcb_radius+clearance+wall);
            translate([0,0,bottom_chamfer])
                linear_extrude(height=floor_thickness+internal_depth-bottom_chamfer)
                    profile(clearance+wall);
        }}
        translate([0,0,floor_thickness])
            linear_extrude(height=internal_depth+0.1)
                profile(clearance);
    }}
    for (mount = mounts) {{
        pin_diameter = mount[2]-pin_clearance;
        assert(pin_diameter > tip_diameter_reduction && pin_diameter < support_diameter);
        translate([mount[0],mount[1],floor_thickness]) {{
            translate([0,0,-0.05])
                cylinder(h=support_height+0.05, d=support_diameter);
            translate([0,0,support_height])
                cylinder(h=pin_height-tip_height, d=pin_diameter);
            translate([0,0,support_height+pin_height-tip_height])
                cylinder(h=tip_height, d1=pin_diameter, d2=pin_diameter-tip_diameter_reduction);
        }}
    }}
}} }}

difference() {{
    case_body();
    translate([sd_center_x-sd_opening_width/2, -clearance-wall-0.1,
               pcb_top_z+sd_base_offset-opening_clearance])
        cube([sd_opening_width, wall+0.2, sd_body_height+2*opening_clearance]);
    // Extends above the current rim: the JAE opening is a top-open notch.
    translate([pcb_width+clearance-0.1, jae_center_y-jae_opening_width/2,
               pcb_top_z+jae_base_offset-opening_clearance])
        cube([wall+0.2, jae_opening_width,
              jae_body_height+jae_positive_tolerance+2*opening_clearance]);
}}
'''
    (out / 'accord-logger-case-bottom.scad').write_text(scad)
    report = dict(units='mm', source_pcb_sha256=data['source_sha256'],
                  pcb=[w, h], pcb_thickness=data['thickness'], clearance_per_side=c, wall=t, floor=f, internal_depth=depth,
                  outside=[w+2*(c+t), h+2*(c+t), height], inside=[w+2*c, h+2*c, depth],
                  inner_corner_radius=r+c, outer_corner_radius=r+c+t,
                  bottom_chamfer=bevel, bottom_contact_size=[w+2*(c+t-bevel), h+2*(c+t-bevel)],
                  bottom_corner_radius=r+c+t-bevel,
                  support_height_above_floor=support_height, supports=supports,
                  pin_height=pin_height, pin_diametral_clearance=args.pin_clearance,
                  tip_height=tip_height, pcb_top_z=pcb_top_z, cutouts=cutouts,
                  pin_top_z=seat_z+pin_height, connected_solids=len(solid.decompose()),
                  triangles=len(faces), bounds=bounds, mesh_volume_mm3=round(volume, 6),
                  analytic_volume_mm3=round(exact_volume, 6),
                  euler_characteristic=expected_euler,
                  validation='Closed oriented manifold, expected opening topology, positive volume; bounds and volume checked')
    (out / 'dimensions.json').write_text(json.dumps(report, indent=2)+'\n')
    cutout_drawing(out, report)
    if args.preview:
        preview(out, vertices, faces, normals, report)
        preview(out, vertices, faces, normals, report, underside=True)
    print(json.dumps(report, indent=2))


def cutout_drawing(out, report):
    """Two wall elevations with the PCB height datum and full body envelopes."""
    from html import escape
    items = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="680" viewBox="0 0 1000 680">',
             '<!-- Accord by Jayson Gazeley; CERN-OHL-P-2.0 -->',
             '<rect width="1000" height="680" fill="white"/>',
             '<g font-family="sans-serif" fill="#24394b">']

    def label(x, y, text, size=16):
        items.append(f'<text x="{x:g}" y="{y:g}" font-size="{size}">{escape(text)}</text>')

    label(35, 30, 'Logger case — SD access and JAE connector opening', 23)
    label(35, 60, f'PCB top Z = floor {report["floor"]:g} + supports {report["support_height_above_floor"]:g}'
          f' + PCB {report["pcb_thickness"]:g} = {report["pcb_top_z"]:g} mm. All dimensions in mm.')
    for index, cut in enumerate(report['cutouts']):
        base = 255+300*index
        scale, left = 6, 80
        span = report['pcb'][0 if cut['reference'] == 'J5' else 1]
        gap = report['clearance_per_side']+report['wall']
        xmap = lambda x: left+(x+gap)*scale
        ymap = lambda z: base-z*scale
        rim = report['outside'][2]
        center, width = cut['center_along_wall'], cut['width']
        z0, z1 = cut['actual_z_range']
        axis = 'X' if cut['reference'] == 'J5' else 'Y'
        label(35, base-160, f'{cut["reference"]} — {cut["wall"]}, {cut["kind"]}; center {axis}={center:g}', 18)
        items.append(f'<rect x="{left}" y="{ymap(rim)}" width="{(span+2*gap)*scale}" '
                     f'height="{rim*scale}" fill="#d8e5ee" stroke="#344f63"/>')
        items.append(f'<rect x="{xmap(center-width/2)}" y="{ymap(z1)}" width="{width*scale}" '
                     f'height="{(z1-z0)*scale}" fill="white" stroke="#1565c0" stroke-width="2"/>')
        body_w, body_h = cut['nominal_body_size']
        tolerance = cut['positive_body_tolerance']
        bottom = report['pcb_top_z']+cut['base_offset_above_pcb']
        items.append(f'<rect x="{xmap(center-(body_w+tolerance)/2)}" y="{ymap(bottom+body_h+tolerance)}" '
                     f'width="{(body_w+tolerance)*scale}" height="{(body_h+tolerance)*scale}" '
                     'fill="none" stroke="#aa6200" stroke-width="1.5" stroke-dasharray="5 3"/>')
        for z, title in ((report['floor'], 'Inside floor'), (report['pcb_top_z'], 'PCB top')):
            items.append(f'<path d="M {left} {ymap(z)} H {xmap(span+gap)}" '
                         'stroke="#55838d" stroke-dasharray="4 4"/>')
            label(xmap(span+gap)+8, ymap(z)+4, f'{title}: {z:g}', 12)
        label(35, base+30, f'Opening width {width:g}; {axis}={center-width/2:g}..{center+width/2:g}; '
              f'actual Z={z0:g}..{z1:g} ({z1-z0:g} high).')
        note = ('Provisional SD envelope: socket seated directly above PCB; header row projected to nearest wall.'
                if cut['reference'] == 'J5' else
                f'Full connector clearance reaches Z={cut["requested_z_range"][1]:g}, above the Z={rim:g} rim.')
        label(35, base+55, note, 14)
    label(35, 650, 'Blue: cut opening. Orange dashed: socket/body envelope (JAE maximum tolerance). Not a measured assembly fit.', 14)
    items.extend(['</g>', '</svg>'])
    (out / 'cutout-layout.svg').write_text('\n'.join(items)+'\n')


def preview(out, vertices, faces, normals, report, underside=False):
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    scale = 2
    image = Image.new('RGB', (1100*scale, 820*scale), '#f4f6fa')
    sign = -1 if underside else 1
    eye = (0.78, -0.78, 0.9*sign)

    def project(p):
        x, y, z = p
        return ((x+y)*0.7071, (-x+y)*0.45*sign+z*0.78)

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
        brightness = 0.6+0.4*max(0, dot(normal, (0.2, -0.4, 0.894*sign)))
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
    label = 'Accord logger — underside' if underside else 'Accord logger — simple case bottom'
    draw.text((55*scale, 40*scale), label, font=title, fill='#24394b')
    w, h, z = report['outside']
    lines = [f'{w:g} × {h:g} × {z:g} mm outside',
             f'{report["wall"]:g} mm walls / {report["floor"]:g} mm floor / {report["internal_depth"]:g} mm internal depth',
             f'{report["clearance_per_side"]:g} mm PCB clearance · {report["bottom_chamfer"]:g} mm bottom chamfer',
             f'Four stepped studs · PCB raised {report["support_height_above_floor"]:g} mm above floor']
    if underside:
        lines[-1] = f'Exterior bottom edge: {report["bottom_chamfer"]:g} × {report["bottom_chamfer"]:g} mm bevel at 45°'
    for i, line in enumerate(lines):
        draw.text((55*scale, (650+32*i)*scale), line, font=font, fill='#24394b')
    name = 'underside-preview.png' if underside else 'preview.png'
    image.resize((1100, 820), Image.Resampling.LANCZOS).save(out / name)


if __name__ == '__main__':
    main()
