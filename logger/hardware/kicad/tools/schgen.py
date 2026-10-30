"""Build a KiCad 9 .kicad_sch from a component/net description.

Every symbol is placed at rotation 0 and every connection is made by placing a
net label exactly on the pin's endpoint, so no wire geometry has to be solved.
"""
import os
import uuid as _uuid
import sexp

SYMDIR = '/usr/share/kicad/symbols'
STUB = 2.54   # pin-to-label stub length, mm


# Fixed project namespace; never change after PCB association.
NAMESPACE = _uuid.uuid5(_uuid.NAMESPACE_URL, 'https://github.com/jgazeley/accord/logger')


def u(*key):
    return str(_uuid.uuid5(NAMESPACE, repr(key)))


class Lib:
    def bbox(self, lib_id):
        """(x_min, y_min, x_max, y_max) of graphics and pins, library coords."""
        node = self.defs(lib_id)[0][1]
        xs, ys = [], []

        def pt(x, y):
            xs.append(float(x)); ys.append(float(y))

        def walk(n):
            for item in n:
                if not isinstance(item, list):
                    continue
                kind = item[0]
                if kind == 'symbol':
                    walk(item)
                elif kind in ('rectangle', 'arc', 'bezier'):
                    for key in ('start', 'end', 'mid'):
                        g = sexp.get(item, key)
                        if g:
                            pt(g[1], g[2])
                elif kind in ('polyline', 'rectangle'):
                    g = sexp.get(item, 'pts')
                    if g:
                        for xy in sexp.getall(g, 'xy'):
                            pt(xy[1], xy[2])
                elif kind == 'circle':
                    c, r = sexp.get(item, 'center'), sexp.get(item, 'radius')
                    if c and r:
                        pt(float(c[1]) - float(r[1]), float(c[2]) - float(r[1]))
                        pt(float(c[1]) + float(r[1]), float(c[2]) + float(r[1]))
                elif kind == 'pin':
                    g = sexp.get(item, 'at')
                    pt(g[1], g[2])
        walk(node)
        g = sexp.get(node, 'pts')
        if not xs:
            return (0.0, 0.0, 0.0, 0.0)
        return (min(xs), min(ys), max(xs), max(ys))

    def fieldpos(self, lib_id):
        """{'Reference': (x, y, rot), 'Value': ...} in library coords."""
        node = self.defs(lib_id)[0][1]
        out = {}
        for p in sexp.getall(node, 'property'):
            if p[1][1:] in ('Reference', 'Value'):
                at = sexp.get(p, 'at')
                out[p[1][1:]] = (float(at[1]), float(at[2]),
                                 int(float(at[3])) if len(at) > 3 else 0)
        return out

    def __init__(self, extra=None):
        self._cache = {}
        self._files = {}
        self.extra = extra or {}   # libname -> path

    def _path(self, libname):
        if libname in self.extra:
            return self.extra[libname]
        return os.path.join(SYMDIR, libname + '.kicad_sym')

    def _file(self, libname):
        if libname not in self._files:
            self._files[libname] = sexp.read(self._path(libname))
        return self._files[libname]

    def _raw(self, libname, name):
        for s in sexp.getall(self._file(libname), 'symbol'):
            if s[1] == '"' + name:
                return s
        raise KeyError(libname + ':' + name)

    def defs(self, lib_id):
        """Return [(lib_id, flattened defnode)].

        A schematic's lib_symbols cannot carry `extends`, so a derived symbol is
        flattened the way KiCad resolves it: the parent's body with the derived
        symbol's own property values and unit names.
        """
        libname, name = lib_id.split(':', 1)
        raw = self._raw(libname, name)
        ext = sexp.get(raw, 'extends')
        if ext is None:
            node = [x for x in raw]
            node[1] = sexp.q(lib_id)
            return [(lib_id, node)]
        parent = self.defs(libname + ':' + ext[1][1:])[0][1]
        pname = ext[1][1:]
        over = {p[1][1:]: p for p in sexp.getall(raw, 'property')}
        node = []
        for x in parent:
            if isinstance(x, list) and x[0] == 'property':
                node.append(over.pop(x[1][1:], x))
            elif isinstance(x, list) and x[0] == 'symbol':
                sub = [y for y in x]
                sub[1] = sexp.q(x[1][1:].replace(pname, name, 1))
                node.append(sub)
            else:
                node.append(x)
        for p in over.values():
            node.insert(node.index(sexp.get(node, 'embedded_fonts')), p)
        node[1] = sexp.q(lib_id)
        return [(lib_id, node)]

    def pins(self, lib_id):
        """{number: (name, etype, x, y)} with library-space coords."""
        if lib_id in self._cache:
            return self._cache[lib_id]
        libname, name = lib_id.split(':', 1)
        raw = self._raw(libname, name)
        ext = sexp.get(raw, 'extends')
        if ext is not None:
            res = self.pins(libname + ':' + ext[1][1:])
        else:
            res = {}
            for unit in sexp.getall(raw, 'symbol'):
                for p in sexp.getall(unit, 'pin'):
                    at = sexp.get(p, 'at')
                    nm = sexp.get(p, 'name')[1][1:]
                    nu = sexp.get(p, 'number')[1][1:]
                    res[nu] = (nm, p[1], float(at[1]), float(at[2]),
                               int(float(at[3])))
        self._cache[lib_id] = res
        return res


def _prop(name, value, x, y, hide=False, justify=None, size=1.27):
    eff = ['effects', ['font', ['size', str(size), str(size)]]]
    if justify:
        eff.append(['justify', justify])
    if hide:
        eff.append(['hide', 'yes'])
    return ['property', sexp.q(name), sexp.q(value),
            ['at', f'{x:.2f}', f'{y:.2f}', '0'], eff]


class Sheet:
    def __init__(self, title, rev, paper='A1', date='2026-10-29', comments=()):
        self.title, self.rev, self.paper, self.date = title, rev, paper, date
        self.comments = comments
        self.uuid = u("sheet", "accord-logger")
        self.items = []
        self.used = []        # lib_ids in placement order
        self.refs = {}        # ref -> (lib_id, x, y)
        self.lib = None

    # ---- placement -------------------------------------------------
    @staticmethod
    def _xf(px, py, rot):
        """Library pin coords -> schematic offset, for rot 0/90/180/270.

        Verified against kicad-cli netlists rather than assumed.
        """
        u, v = px, -py
        return {0: (u, v), 90: (v, -u), 180: (-u, -v), 270: (-v, u)}[rot % 360]

    def _fieldxy(self, lib_id, which, x, y, rot):
        x1, y1, x2, y2 = self.lib.bbox(lib_id)
        corners = [self._xf(a, b, rot) for a in (x1, x2) for b in (y1, y2)]
        left = x + min(c[0] for c in corners)
        right = x + max(c[0] for c in corners)
        top = y + min(c[1] for c in corners)
        bottom = y + max(c[1] for c in corners)
        if right - left <= 6.0:   # a narrow two-pin part: fields beside it
            return (right + 1.27, y - 1.78 if which == 'Reference' else y + 1.78)
        return (left, top - 1.78 if which == 'Reference' else bottom + 2.54)

    def symbol(self, ref, lib_id, value, x, y, nets=None, footprint='',
               fields=None, rot=0, in_bom=True, on_board=True,
               dnp=False, hide_value=False, nc=(), labelsize=1.27):
        identity = (fields or {}).get('Source_designator', ref)
        if ref in self.refs:
            raise ValueError('duplicate reference: ' + ref)
        pins = self.lib.pins(lib_id)
        if lib_id not in self.used:
            self.used.append(lib_id)
        self.refs[ref] = (lib_id, x, y, rot)
        node = ['symbol', ['lib_id', sexp.q(lib_id)],
                ['at', f'{x:.2f}', f'{y:.2f}', str(rot)], ['unit', '1']]
        node += [['exclude_from_sim', 'no'],
                 ['in_bom', 'yes' if in_bom else 'no'],
                 ['on_board', 'yes' if on_board else 'no'],
                 ['dnp', 'yes' if dnp else 'no'],
                 ['uuid', sexp.q(u('symbol', identity))],
                 _prop('Reference', ref, *self._fieldxy(lib_id, 'Reference',
                                                       x, y, rot),
                       hide=False),
                 _prop('Value', value, *self._fieldxy(lib_id, 'Value',
                                                      x, y, rot),
                       hide=hide_value),
                 _prop('Footprint', footprint, x, y, True),
                 _prop('Datasheet', '', x, y, True),
                 _prop('Description', '', x, y, True)]
        for k, v in (fields or {}).items():
            node.append(_prop(k, v, x, y, True))
        for num in sorted(pins, key=lambda s: (len(s), s)):
            node.append(['pin', sexp.q(num), ['uuid', sexp.q(u('pin', identity, num))]])
        node.append(['instances',
                     ['project', sexp.q('accord-logger'),
                      ['path', sexp.q('/' + self.uuid),
                       ['reference', sexp.q(ref)], ['unit', '1']]]])
        self.items.append(node)
        for num, net in (nets or {}).items():
            px, py, lrot = self.pin_at(ref, num, full=True)
            # A short stub outward from the pin, with the label at its far end,
            # so the label never sits on top of KiCad's pin number.
            out = (lrot + rot + 180) % 360
            dx, dy = {0: (1, 0), 90: (0, -1), 180: (-1, 0),
                      270: (0, 1)}[out]
            ex, ey = px + dx * STUB, py + dy * STUB
            self.wire(px, py, ex, ey)
            self.label(net, ex, ey, out, labelsize)
        for num in nc:
            px, py, _ = self.pin_at(ref, num, full=True)
            self.items.append(['no_connect', ['at', f'{px:.2f}', f'{py:.2f}'],
                               ['uuid', sexp.q(u('nc', identity, str(num)))]])
        return node

    def pin_at(self, ref, num, full=False):
        lib_id, x, y, rot = self.refs[ref]
        nm, etype, px, py, lrot = self.lib.pins(lib_id)[str(num)]
        dx, dy = self._xf(px, py, rot)
        return (x + dx, y + dy, lrot) if full else (x + dx, y + dy)

    def label(self, name, x, y, rot=0, size=1.27):
        self.items.append(['label', sexp.q(name),
                           ['at', f'{x:.2f}', f'{y:.2f}', str(rot % 360)],
                           ['effects', ['font', ['size', str(size), str(size)]]],
                           ['uuid', sexp.q(u('label', name, x, y, rot))]])

    def glabel(self, name, x, y, rot=0, shape='bidirectional'):
        self.items.append(['global_label', sexp.q(name), ['shape', shape],
                           ['at', f'{x:.2f}', f'{y:.2f}', str(rot)],
                           ['effects', ['font', ['size', '1.27', '1.27']]],
                           ['uuid', sexp.q(u('glabel', name, x, y, rot))]])

    def text(self, s, x, y, size=1.27, bold=False):
        eff = ['effects', ['font', ['size', str(size), str(size)]] +
               ([['bold', 'yes']] if bold else []),
               ['justify', 'left', 'top']]
        self.items.append(['text', sexp.q(s), ['at', f'{x:.2f}', f'{y:.2f}', '0'],
                           eff, ['uuid', sexp.q(u('text', s, x, y))]])

    def rect(self, x1, y1, x2, y2, dash=True, width=0.2):
        self.items.append(['rectangle',
                           ['start', f'{x1:.2f}', f'{y1:.2f}'],
                           ['end', f'{x2:.2f}', f'{y2:.2f}'],
                           ['stroke', ['width', str(width)],
                            ['type', 'dash' if dash else 'solid']],
                           ['fill', ['type', 'none']],
                           ['uuid', sexp.q(u('rect', x1, y1, x2, y2))]])

    def wire(self, x1, y1, x2, y2):
        self.items.append(['wire', ['pts', ['xy', f'{x1:.2f}', f'{y1:.2f}'],
                                    ['xy', f'{x2:.2f}', f'{y2:.2f}']],
                           ['stroke', ['width', '0'], ['type', 'default']],
                           ['uuid', sexp.q(u('wire', x1, y1, x2, y2))]])

    # ---- output ----------------------------------------------------
    def write(self, path):
        tb = ['title_block', ['title', sexp.q(self.title)],
              ['date', sexp.q(self.date)], ['rev', sexp.q(self.rev)]]
        for i, c in enumerate(self.comments, 1):
            tb.append(['comment', str(i), sexp.q(c)])
        libsyms = ['lib_symbols']
        seen = set()
        for lib_id in self.used:
            for nm, node in self.lib.defs(lib_id):
                if nm in seen:
                    continue
                seen.add(nm)
                libsyms.append(node)
        root = ['kicad_sch', ['version', '20250114'],
                ['generator', sexp.q('gen_logger_sch.py')],
                ['generator_version', sexp.q('9.0')],
                ['uuid', sexp.q(self.uuid)], ['paper', sexp.q(self.paper)],
                tb, libsyms] + self.items + [
                ['sheet_instances', ['path', sexp.q('/'), ['page', sexp.q('1')]]],
                ['embedded_fonts', 'no']]
        open(path, 'w', encoding='utf-8').write(sexp.dump(root) + '\n')
