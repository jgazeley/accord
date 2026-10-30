#!/usr/bin/env python3
"""Check PCB identity survives placement, value, order and reference changes.

Full-file reproducibility is checked by the two generator runs in COMMANDS.txt.
"""
from pathlib import Path
import re
import schgen
import sexp


def placed(ref, x, value, extra=False):
    sheet = schgen.Sheet('identity regression', 'test')
    sheet.lib = schgen.Lib()
    if extra:
        sheet.symbol('R999', 'Device:R', '1k', 10, 10)
    node = sheet.symbol(ref, 'Device:R', value, x, 20,
                        fields={'Source_designator': 'R_AON'})
    return (sheet.uuid, sexp.get(node, 'uuid')[1],
            tuple(sexp.get(pin, 'uuid')[1] for pin in sexp.getall(node, 'pin')))


assert placed('R22', 20, '820R') == placed('R23', 30, '1k', extra=True)
path = Path(__file__).resolve().parents[1] / 'accord-logger.kicad_sch'
ids = re.findall(r'\(uuid "([^"]+)"\)', path.read_text())
assert len(ids) == len(set(ids)), 'duplicate schematic UUID'
print('UUID identity regression passed; %d unique schematic UUIDs' % len(ids))
