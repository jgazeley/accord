"""Courtyard study: measure every BOM footprint and check the 80 x 120 fit.

Run from this directory:  python3 fp_area.py

Why this exists. D-ENVELOPE-01 sized the board from "nominal package areas"
over the LRA-06 part set, which had ten parts with no footprint at all and none
of the power logic. LRA-12 adds about sixty parts, so the fit has to be
recomputed from the footprints actually assigned rather than re-quoted.

What it measures. For each part in BOM.csv it opens the assigned .kicad_mod and
takes the bounding box of its F.CrtYd/B.CrtYd courtyard, which is the
manufacturer-or-library statement of the space the part needs including its
own clearance. Where a footprint carries no courtyard it falls back to the pad
extent plus a 0.25 mm margin per side and says so, rather than silently
reporting a smaller number.

What it does not do. A courtyard sum is an occupancy figure, not a placement:
it says nothing about routing channels, keepouts, connector access or whether
any particular arrangement closes. It is a floor, and the allowance over it is
the thing to judge. Final placement is the owner's.

Writes validation/courtyard_study.csv and prints the summary.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'tools'))
import sexp

HERE = os.path.dirname(os.path.abspath(__file__))
LIBDIRS = ['/usr/share/kicad/footprints', HERE]
BOARD_W, BOARD_H = 80.0, 120.0
CRTYD = ('"F.CrtYd', '"B.CrtYd')


def find(fp):
    lib, name = fp.split(':', 1)
    for d in LIBDIRS:
        p = os.path.join(d, lib + '.pretty', name + '.kicad_mod')
        if os.path.exists(p):
            return p
    return None


def _pts(item):
    """Every (x, y) a graphics item mentions, however it is expressed."""
    out = []
    for key in ('start', 'end', 'mid', 'center'):
        g = sexp.get(item, key)
        if g:
            out.append((float(g[1]), float(g[2])))
    g = sexp.get(item, 'pts')
    if g:
        for xy in sexp.getall(g, 'xy'):
            out.append((float(xy[1]), float(xy[2])))
    c, r = sexp.get(item, 'center'), sexp.get(item, 'radius')
    if c and r:
        cx, cy, rr = float(c[1]), float(c[2]), float(r[1])
        out += [(cx - rr, cy - rr), (cx + rr, cy + rr)]
    # a circle drawn as center+end: the end point is on the circumference
    if c and not r:
        e = sexp.get(item, 'end')
        if e and item[0] == 'fp_circle':
            cx, cy = float(c[1]), float(c[2])
            rr = max(abs(float(e[1]) - cx), abs(float(e[2]) - cy))
            out += [(cx - rr, cy - rr), (cx + rr, cy + rr)]
    return out


def measure(path):
    """(width, height, source) from the courtyard, or from the pads."""
    fpn = sexp.read(path)
    cxs, cys = [], []
    for item in fpn:
        if not isinstance(item, list) or not str(item[0]).startswith('fp_'):
            continue
        lay = sexp.get(item, 'layer')
        if not lay or lay[1] not in CRTYD:
            continue
        for x, y in _pts(item):
            cxs.append(x)
            cys.append(y)
    if cxs:
        return (max(cxs) - min(cxs), max(cys) - min(cys), 'courtyard')
    pxs, pys = [], []
    for pad in sexp.getall(fpn, 'pad'):
        at = sexp.get(pad, 'at')
        size = sexp.get(pad, 'size')
        if not at or not size:
            continue
        x, y = float(at[1]), float(at[2])
        w, h = float(size[1]), float(size[2])
        rot = float(at[3]) if len(at) > 3 else 0.0
        if abs((rot / 90.0) % 2 - 1) < 0.01:      # 90 or 270 degrees
            w, h = h, w
        pxs += [x - w / 2, x + w / 2]
        pys += [y - h / 2, y + h / 2]
    if pxs:
        return (max(pxs) - min(pxs) + 0.5, max(pys) - min(pys) + 0.5,
                'pad extent + 0.25 mm/side (no courtyard in footprint)')
    return None


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, 'BOM.csv'))))
    out, total, fitted_total, problems = [], 0.0, 0.0, []
    for r in rows:
        fp = r['footprint']
        if fp == '(none assigned)':
            problems.append('%s has no footprint' % r['reference'])
            continue
        path = find(fp)
        if not path:
            problems.append('%s: footprint %s not found in any library'
                            % (r['reference'], fp))
            continue
        m = measure(path)
        if not m:
            problems.append('%s: %s has neither courtyard nor pads'
                            % (r['reference'], fp))
            continue
        w, h, src = m
        area = w * h
        total += area
        if r['population'] != 'DNP':
            fitted_total += area
        out.append(dict(reference=r['reference'], value=r['value'],
                        footprint=fp, width_mm='%.3f' % w,
                        height_mm='%.3f' % h, area_mm2='%.1f' % area,
                        population=r['population'], measured_from=src))
    out.sort(key=lambda d: -float(d['area_mm2']))
    vdir = os.path.join(HERE, 'validation')
    with open(os.path.join(vdir, 'courtyard_study.csv'), 'w', newline='',
              encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)

    board = BOARD_W * BOARD_H
    print('parts with a footprint : %d of %d' % (len(out), len(rows)))
    print('courtyard sum, fitted  : %.0f mm2' % fitted_total)
    print('courtyard sum, all     : %.0f mm2' % total)
    print('board %.0f x %.0f        : %.0f mm2' % (BOARD_W, BOARD_H, board))
    print('allowance over fitted  : %.2fx' % (board / fitted_total))
    fallback = [d for d in out if d['measured_from'] != 'courtyard']
    print('measured from pads     : %s'
          % (', '.join(d['reference'] for d in fallback) or 'none'))
    print()
    print('largest fifteen:')
    for d in out[:15]:
        print('  %8s mm2  %-10s %6s x %-6s  %s'
              % (d['area_mm2'], d['reference'], d['width_mm'],
                 d['height_mm'], d['footprint'].split(':')[1]))
    if problems:
        print()
        print('PROBLEMS:')
        for p in problems:
            print(' ', p)
    print()
    print('wrote', os.path.join(vdir, 'courtyard_study.csv'))
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
