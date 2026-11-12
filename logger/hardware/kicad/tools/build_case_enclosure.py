#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Jayson Gazeley
"""Build a PLA+ prototype snap lid and its matching receiver-window bottom.

Requires NumPy, Manifold3D and Pillow. The earlier case-bottom STL is the
input blank; this does not modify it. All geometry uses millimetres.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct

import manifold3d as m
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def box(origin, size):
    return m.Manifold.cube(size).translate(origin)


def read_stl(path):
    raw = path.read_bytes()
    count = struct.unpack_from('<I', raw, 80)[0]
    assert len(raw) == 84 + count * 50
    points, faces, lookup = [], [], {}
    for i in range(count):
        values = struct.unpack_from('<12fH', raw, 84 + i * 50)
        face = []
        for j in (3, 6, 9):
            p = tuple(values[j:j+3])
            if p not in lookup:
                lookup[p] = len(points)
                points.append(p)
            face.append(lookup[p])
        faces.append(face)
    return m.Manifold(m.Mesh(np.array(points, dtype=np.float32),
                             np.array(faces, dtype=np.uint32)))


def mesh_arrays(solid):
    mesh = solid.to_mesh()
    v, f = mesh.vert_properties[:, :3], mesh.tri_verts
    normals = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    lengths = np.linalg.norm(normals, axis=1)
    assert np.all(lengths > 1e-9), 'Degenerate triangle'
    return v, f, normals / lengths[:, None]


def write_stl(path, solid):
    v, f, normals = mesh_arrays(solid)
    with path.open('wb') as stream:
        stream.write(b'Accord by Jayson Gazeley; CERN-OHL-P-2.0; units mm'.ljust(80, b'\0'))
        stream.write(struct.pack('<I', len(f)))
        for face, normal in zip(f, normals):
            stream.write(struct.pack('<12fH', *normal, *v[face].flatten(), 0))
    # Validate the exported bytes, including independently welded STL vertices.
    result = read_stl(path)
    assert result.status() == m.Error.NoError
    assert len(result.decompose()) == 1
    v, f, _ = mesh_arrays(result)
    edges = Counter((int(face[j]), int(face[(j+1) % 3])) for face in f for j in range(3))
    assert all(n == 1 and edges[b, a] == 1 for (a, b), n in edges.items())
    return result, dict(triangles=len(f), connected_solids=1,
                        euler_characteristic=len(v)-len(edges)//2+len(f),
                        volume_mm3=result.volume(), bounds=list(result.bounding_box()),
                        sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def render(path, parts, title, lines):
    """Orthographic z-buffer preview of the actual meshes, no CAD viewer needed."""
    from PIL import Image, ImageDraw, ImageFont
    width, height = 1200, 900
    eye = np.array([0.78, -0.78, 0.90])
    arrays = [(*mesh_arrays(s), np.array(color)) for s, color in parts]
    all_v = np.concatenate([a[0] for a in arrays])
    projection = np.array([[0.7071, 0.7071, 0], [-0.45, 0.45, 0.78]])
    projected = all_v @ projection.T
    lo, hi = projected.min(axis=0), projected.max(axis=0)
    factor = min(1090/(hi[0]-lo[0]), 620/(hi[1]-lo[1]))
    left = (width-(hi[0]-lo[0])*factor)/2
    canvas = np.full((height, width, 3), (244, 246, 250), dtype=np.uint8)
    depth = np.full((height, width), -np.inf)
    for vertices, faces, normals, color in arrays:
        proj = vertices @ projection.T
        pixels = np.column_stack((left+(proj[:, 0]-lo[0])*factor,
                                  110+(hi[1]-proj[:, 1])*factor))
        depths = vertices @ eye
        for face, normal in zip(faces, normals):
            if normal @ eye <= 0:
                continue
            a, b, c = pixels[face]
            xmin, ymin = np.maximum(0, np.floor(np.min([a, b, c], axis=0)).astype(int))
            xmax, ymax = np.minimum([width-1, height-1], np.ceil(np.max([a, b, c], axis=0)).astype(int))
            yy, xx = np.mgrid[ymin:ymax+1, xmin:xmax+1]
            den = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den) < 1e-9:
                continue
            u = ((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
            v = ((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den
            q = 1-u-v
            z = u*depths[face[0]]+v*depths[face[1]]+q*depths[face[2]]
            region = depth[ymin:ymax+1, xmin:xmax+1]
            visible = (u >= -1e-6) & (v >= -1e-6) & (q >= -1e-6) & (z > region)
            region[visible] = z[visible]
            brightness = 0.55+0.45*max(0, normal @ np.array([0.2, -0.4, 0.894]))
            canvas[ymin:ymax+1, xmin:xmax+1][visible] = (color*brightness).astype(np.uint8)
    image = Image.fromarray(canvas)
    draw = ImageDraw.Draw(image)
    font = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    draw.text((40, 28), title, font=ImageFont.truetype(font, 28), fill='#24394b')
    for i, line in enumerate(lines):
        draw.text((40, 778+i*29), line, font=ImageFont.truetype(font, 19), fill='#24394b')
    image.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engagement', type=float, default=0.4, help='Hook intrusion into bottom wall')
    parser.add_argument('--lip-clearance', type=float, default=0.3, help='Radial alignment gap')
    parser.add_argument('--preview', action='store_true')
    args = parser.parse_args()
    if not 0.1 <= args.engagement <= 0.6 or not 0.2 <= args.lip_clearance <= 0.5:
        parser.error('Prototype ranges: engagement 0.1..0.6; lip clearance 0.2..0.5 mm')
    reference = json.loads((ROOT/'mechanical/accord-logger-mechanical.json').read_text())
    base_dir = ROOT/'mechanical/case-bottom'
    dims = json.loads((base_dir/'dimensions.json').read_text())
    source = base_dir/'accord-logger-case-bottom.stl'
    assert hashlib.sha256((ROOT/reference['source']).read_bytes()).hexdigest() == reference['source_sha256']
    assert dims['source_pcb_sha256'] == reference['source_sha256']
    # This mating design is sized for the approved Rev A tray, not arbitrary blanks.
    assert dims['pcb'] == [120, 83] and dims['outside'] == [126, 89, 16]
    assert dims['wall'] == 2 and dims['inner_corner_radius'] == 3
    assert dims['pcb_top_z'] == 8.775
    sd, jae = dims['cutouts']
    assert sd['reference'] == 'J5' and jae['reference'] == 'J1'
    assert jae['width'] == 28 and jae['center_along_wall'] == 40
    assert jae['requested_z_range'] == [8.275, 24.775]
    assert sd['actual_z_range'][1] < 13
    w, h, r, seam, top_z, roof = 120, 83, 2, 16, 29, 2
    engagement, lip_gap = args.engagement, args.lip_clearance
    centers = [(r, r), (w-r, r), (w-r, h-r), (r, h-r)]

    def rounded(gap, z0, z1, upper_gap=None):
        upper_gap = gap if upper_gap is None else upper_gap
        corners = [m.Manifold.cylinder(z1-z0, r+gap, r+upper_gap,
                                       circular_segments=128).translate((x, y, z0))
                   for x, y in centers]
        solid = corners[0]
        for corner in corners[1:]:
            solid += corner
        return solid.hull()

    base = read_stl(source)
    assert base.status() == m.Error.NoError and len(base.decompose()) == 1
    assert abs(base.volume()-dims['mesh_volume_mm3']) < 0.001
    bottom = base
    positions = [(x, y, direction) for y, direction in [(-3, -1), (86, 1)] for x in (18, 102)]
    receivers = []
    for x, y, direction in positions:
        origin = [x-4.5, y-0.1 if direction == -1 else y-2.1, 12.6]
        cutter = box(origin, [9, 2.2, 2.2])
        receivers.append(cutter)
        bottom -= cutter

    lid = rounded(3, seam, top_z)-rounded(1, seam-0.1, top_z-roof)
    lip_outer = 1-lip_gap
    lip_inner = lip_outer-1
    skirt = rounded(lip_outer, 13, 16.1)-rounded(lip_inner, 12.9, 16.2)
    # A tapered root joins the inset skirt to the lid wall; printable roof-down.
    root = rounded(1.2, 16, 17.5)-rounded(lip_inner, 16, 17.5, 1)
    lid = lid+skirt+root
    jae_cutter = box([118, 26, 8.275], [5.2, 28, 16.5])
    lid -= jae_cutter

    # Local coordinates: u points outwards from the outside wall, v is case Z.
    beam_profile = [(0.3, 12.8), (1.5, 12.8), (1.5, 26.9), (-0.3, 28.7), (-0.3, 25)]
    beam_profile += [(-0.3+0.6*math.cos(a), 24.4+0.6*math.sin(a))
                     for a in np.linspace(math.pi/2, 0, 17)[1:]]
    hook_profile = [(0.35, 12.8), (0.35, 14.6), (-engagement, 14.6), (-engagement, 14), (0.3, 12.8)]

    def clip_shape(profile, x, y, direction):
        section = m.CrossSection([np.array(profile)])
        return m.Manifold.extrude(section, 8).transform(
            [[0, 0, 1, x-4], [direction, 0, 0, y], [0, 1, 0, 0]])

    clips = []
    for x, y, direction in positions:
        clip = clip_shape(beam_profile, x, y, direction)+clip_shape(hook_profile, x, y, direction)
        clips.append(clip)
        lid += clip
    printed_lid = lid.rotate((180, 0, 0)).translate((0, h, top_z))
    out = ROOT/'mechanical/case-enclosure'
    out.mkdir(exist_ok=True)
    bottom, bottom_report = write_stl(out/'accord-logger-bottom.stl', bottom)
    lid, lid_report = write_stl(out/'accord-logger-top-assembled.stl', lid)
    printed_lid, print_report = write_stl(out/'accord-logger-top.stl', printed_lid)
    assert bottom_report['euler_characteristic'] == -8  # SD window + 4 receivers
    assert lid_report['euler_characteristic'] == 2
    assert np.allclose(bottom_report['bounds'], [-3, -3, 0, 123, 86, 16], atol=1e-5)
    assert np.allclose(lid_report['bounds'], [-3, -4.5, 12.8, 123, 87.5, 29], atol=1e-5)
    assert np.allclose(print_report['bounds'], [-3, -4.5, 0, 123, 87.5, 16.2], atol=1e-5)
    # Actual exported-mesh mating, access and preserved-feature checks.
    overlap = (bottom ^ lid).volume()
    assert abs(overlap) < 1e-4
    assert abs(((bottom+lid) ^ jae_cutter).volume()) < 1e-4  # STL float32 rounding
    sd_access = box(sd['cutter_origin'], sd['cutter_size'])
    assert abs(((bottom+lid) ^ sd_access).volume()) < 1e-4
    protected = box([-4, -5, 0], [128, 94, 12.5])
    assert abs(((base-bottom) ^ protected).volume()) < 1e-4
    expected_removed = 4*9*2*2.2
    assert abs(base.volume()-bottom.volume()-expected_removed) < 0.001
    # Roof bridge is intact across the connector opening above its requested top.
    bridge = box([121.1, 26.1, 24.875], [1.8, 27.8, 2])
    assert abs((bridge-lid).volume()) < 1e-4
    for clip, receiver, (x, y, direction) in zip(clips, receivers, positions):
        # Hook engages the wall's original envelope only inside the new window.
        assert (clip ^ base).volume() > 0.1
        assert abs(((clip ^ base)-receiver).volume()) < 1e-4
        # Raising a closed latch hits the upper rail, so it actually retains.
        assert (clip.translate((0, 0, 0.5)) ^ bottom).volume() > 0.1
        # Outward release by engagement + 0.1 clears that rail.
        released = clip.translate((0, direction*(engagement+0.1), 0.5))
        assert abs((released ^ bottom).volume()) < 1e-4
    report = dict(units='mm', material_intent='PLA+; first-print prototype',
                  source_pcb_sha256=reference['source_sha256'],
                  source_bottom_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  assembly_body_size=[126, 89, 29], assembly_with_clips_size=[126, 92, 29],
                  seam_z=16, roof_thickness=2, roof_underside_z=27, wall=2,
                  pcb_top_z=dims['pcb_top_z'], lip=dict(insertion=3, radial_clearance=lip_gap,
                  thickness=1, lowest_z=13, interrupted_at_JAE=True),
                  snap=dict(count=4, centers_x=[18, 102], walls=['front', 'back'],
                  beam_width=8, beam_thickness=1.2, outside_gap=0.3, root_radius=0.6,
                  root_z=25, hook_retention_z=14.6, hook_tip_z=12.8,
                  radial_engagement=engagement, receiver_width=9, receiver_z=[12.6, 14.8],
                  vertical_play=0.2),
                  jae_opening=dict(width=28, height=16.5, center_y=40, z=[8.275, 24.775]),
                  bottom=bottom_report, lid_assembled=lid_report, lid_print=print_report,
                  validation=dict(exported_meshes_closed_oriented_connected=True,
                  closed_assembly_overlap_mm3=overlap, SD_and_JAE_apertures_clear=True,
                  original_geometry_below_z_12_5_preserved=True, latch_retention_and_release_checked=True,
                  physical_fit_and_fatigue_tested=False))
    (out/'dimensions.json').write_text(json.dumps(report, indent=2)+'\n')
    write_scad(out, engagement, lip_gap, beam_profile)
    if args.preview:
        blue, orange = (100, 155, 197), (225, 163, 88)
        render(out/'assembled-preview.png', [(bottom, blue), (lid, orange)],
               'Accord logger — snap-on top, assembled',
               ['126 × 89 × 29 mm body; 92 mm across external clips',
                'JAE aperture: 28 × 16.5 mm, completed by raised lid',
                f'PLA+ prototype — four clips, {engagement:g} mm nominal engagement'])
        render(out/'exploded-preview.png', [(bottom, blue), (lid.translate((0, 0, 24)), orange)],
               'Accord logger — matching bottom and lid',
               ['Lid lifted 24 mm for illustration; PCB omitted',
                'Four receiver windows in bottom; alignment lip interrupted at JAE connector',
                'Existing studs, SD opening and bottom chamfer retained'])
        render(out/'top-print-preview.png', [(printed_lid, orange)],
               'Accord logger — lid, roof down for printing',
               ['Primary top STL is already in this orientation; Z minimum = 0',
                'Inset alignment skirt and four exterior cantilever clips',
                'Fit and clip durability still need a first print in the intended PLA+'])
    print(json.dumps(report, indent=2))


def write_scad(out, engagement, lip_gap, beam):
    # Same constructive geometry as the exported STL; base is imported, lid editable.
    source = '''// SPDX-License-Identifier: CERN-OHL-P-2.0
// Copyright 2026 Jayson Gazeley — https://github.com/jgazeley/accord
// mm. Requires ../case-bottom/accord-logger-case-bottom.stl as the base blank.
part = "top"; // top (roof down), bottom, assembled, exploded
engagement = ENGAGEMENT; // 0.1..0.6; regenerate BOTH parts after fitting changes
lip_clearance = LIP_GAP; // radial, 0.2..0.5
$fn = 128;
assert(engagement >= 0.1 && engagement <= 0.6);
assert(lip_clearance >= 0.2 && lip_clearance <= 0.5);
module rounded(gap, z0, z1, upper_gap=undef) {
    hull() for (x=[2,118]) for(y=[2,81]) translate([x,y,z0])
        cylinder(h=z1-z0, r1=2+gap, r2=2+(is_undef(upper_gap)?gap:upper_gap));
}
module receivers() {
    for(x=[18,102]) for(y=[-3.1,83.9])
        translate([x-4.5,y,12.6]) cube([9,2.2,2.2]);
}
module bottom() {
    difference() {
        import("../case-bottom/accord-logger-case-bottom.stl", convexity=10);
        receivers();
    }
}
module clips() {
    for(x=[18,102]) for(side=[[-3,-1],[86,1]])
        multmatrix([[0,0,1,x-4],[side[1],0,0,side[0]],[0,1,0,0],[0,0,0,1]]) {
            linear_extrude(height=8) polygon(BEAM);
            linear_extrude(height=8) polygon([[0.35,12.8],[0.35,14.6],
                [-engagement,14.6],[-engagement,14],[0.3,12.8]]);
        }
}
module lid() {
    union() {
        difference() {
            union() {
                difference() { rounded(3,16,29); rounded(1,15.9,27); }
                difference() {
                    rounded(1-lip_clearance,13,16.1);
                    rounded(-lip_clearance,12.9,16.2);
                }
                difference() {
                    rounded(1.2,16,17.5); rounded(-lip_clearance,16,17.5,1);
                }
            }
            // Cut wall AND alignment skirt to complete the lower JAE notch.
            translate([118,26,8.275]) cube([5.2,28,16.5]);
        }
        clips();
    }
}
if(part=="bottom") bottom();
else if(part=="top") translate([0,83,29]) rotate([180,0,0]) lid();
else if(part=="assembled" || part=="exploded") {
    color([0.39,0.61,0.77]) bottom();
    color([0.88,0.64,0.35]) translate([0,0,part=="exploded"?24:0]) lid();
}
else assert(false,"Unknown part selector");
'''
    source = source.replace('ENGAGEMENT', str(engagement)).replace('LIP_GAP', str(lip_gap))
    source = source.replace('BEAM', json.dumps(beam))
    (out/'accord-logger-enclosure.scad').write_text(source)


if __name__ == '__main__':
    main()
