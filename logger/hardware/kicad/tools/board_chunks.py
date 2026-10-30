#!/usr/bin/env python3
"""Stage the board by subsystem (DECISIONS D-STAGE-11).

The schematic stays complete. Parts outside the chunks the owner is working
on carry KiCad's "Exclude from board" flag, so "Update PCB from Schematic"
leaves them off the board; switching a chunk back on and updating adds just
that chunk without touching what is already placed.

usage, from logger/hardware/kicad:
  python3 tools/board_chunks.py status
  python3 tools/board_chunks.py only power pico sd connector
  python3 tools/board_chunks.py add rs485
  python3 tools/board_chunks.py full-netlist validation/netlist.net

kicad-cli omits board-excluded symbols from its netlist export, so the
design checks (check_capture.py, check_layout_closure.py) must run on the
FULL netlist: full-netlist exports it from a scratch copy with every part
switched on. Close KiCad before only/add; the schematic is edited in place.

Chunks follow the titled frames on the schematic sheet. Every BOM part is in
exactly one chunk; the script refuses to run otherwise.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCH = os.path.join(HERE, 'accord-logger.kicad_sch')

CHUNKS = {
    'power': 'C9 C10 C11 C12 C13 C14 D112 D113 D114 D115 D116 L1 Q5 Q6 Q7 '
             'R31 R32 R33 R34 R35 R36 R37 U6',
    'pico': 'U1',
    'sd': 'C8 J5',
    'connector': 'J1',
    'inputs': 'C1 C2 D101 D102 D103 D104 D105 D106 D107 D108 R1 R2 R3 R4 '
              'R5 R6 R7 R8 R9 R10 R11 R12 U3',
    'a5_supply': 'C4 C5 C6 C7 D111 R22 U4 U5',
    'ignition_opto': 'D109 D110 R13 U2',
    'qualified_ignition': 'C3 Q1 Q2 R14 R15 R16 R17 R18 R19 R20 R21',
    'iso_enable': 'Q3 Q4 R23 R24 R25 R26 R27',
    'hold': 'JP1 R28 R29',
    'clock': 'C15 C16 C17 C18 R38 U7 U8 U9',
    'cutoff': 'C19 C20 C21 C22 C23 Q8 Q9 R39 R40 R41 R42 R43 R44 R45 R46 '
              'U10 U11 U12 U13 U14',
    'rs485': 'C24 JP2 JP3 JP4 R47 R48 R49 U15',
    'spare_reset': 'J3 J4 R30',
    'rtc': 'BT1 C25 R50 R51 R52 U16',
    'testpoints': ' '.join(f'TP{n}' for n in range(1, 26)),
}
CHUNKS = {k: v.split() for k, v in CHUNKS.items()}
REF_CHUNK = {r: k for k, refs in CHUNKS.items() for r in refs}


def symbol_blocks(text):
    """(start, end, reference) for every placed symbol instance."""
    out = []
    for m in re.finditer(r'\n\t\(symbol\n', text):
        st, d = m.start() + 2, 0
        for j in range(st, len(text)):
            if text[j] == '(':
                d += 1
            elif text[j] == ')':
                d -= 1
                if d == 0:
                    break
        block = text[st:j + 1]
        ref = re.search(r'\(property "Reference" "([^"]+)"', block)
        if ref and not ref.group(1).startswith('#'):
            out.append((st, j + 1, ref.group(1)))
    return out


def load():
    text = open(SCH, encoding='utf-8').read()
    blocks = symbol_blocks(text)
    refs = {r for _, _, r in blocks}
    missing = sorted(refs - set(REF_CHUNK))
    stale = sorted(set(REF_CHUNK) - refs)
    if missing or stale:
        sys.exit(f'chunk table out of date: not in any chunk {missing}, '
                 f'not in the schematic {stale}')
    return text, blocks


def on_board(text, blocks):
    return {r: '(on_board yes)' in text[s:e] for s, e, r in blocks}


def write_flags(text, blocks, wanted):
    for s, e, r in sorted(blocks, reverse=True):
        blk = text[s:e]
        flag = '(on_board yes)' if REF_CHUNK[r] in wanted else '(on_board no)'
        blk = re.sub(r'\(on_board (yes|no)\)', flag, blk, count=1)
        text = text[:s] + blk + text[e:]
    open(SCH, 'w', encoding='utf-8').write(text)


def status(text, blocks):
    ob = on_board(text, blocks)
    for k, refs in CHUNKS.items():
        n = sum(ob[r] for r in refs)
        state = 'ON ' if n == len(refs) else ('off' if n == 0 else 'MIXED')
        print(f'  {state}  {k:20s} {len(refs):3d} parts')
    return {k for k, refs in CHUNKS.items() if all(ob[r] for r in refs)}


def full_netlist(out):
    tmp = tempfile.mkdtemp()
    try:
        for f in os.listdir(HERE):
            src = os.path.join(HERE, f)
            if f.endswith(('.kicad_sch', '.kicad_pro', '.kicad_sym')) or \
                    f in ('sym-lib-table', 'fp-lib-table'):
                shutil.copy(src, tmp)
        shutil.copytree(os.path.join(HERE, 'accord-logger.pretty'),
                        os.path.join(tmp, 'accord-logger.pretty'))
        p = os.path.join(tmp, 'accord-logger.kicad_sch')
        t = open(p, encoding='utf-8').read()
        open(p, 'w', encoding='utf-8').write(
            t.replace('(on_board no)', '(on_board yes)'))
        subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format',
                        'kicadsexpr', '-o', os.path.abspath(out), p],
                       check=True, stdout=subprocess.DEVNULL)
        # keep the committed file free of the scratch path
        n = open(out, encoding='utf-8').read().replace(tmp, HERE)
        open(out, 'w', encoding='utf-8').write(n)
    finally:
        shutil.rmtree(tmp)
    print('wrote full netlist', out)


if __name__ == '__main__':
    cmd, args = (sys.argv[1] if len(sys.argv) > 1 else 'status'), sys.argv[2:]
    if cmd == 'full-netlist':
        full_netlist(args[0] if args else
                     os.path.join(HERE, 'validation', 'netlist.net'))
        sys.exit()
    text, blocks = load()
    if cmd == 'status':
        status(text, blocks)
    elif cmd in ('only', 'add'):
        bad = [a for a in args if a not in CHUNKS]
        if bad or not args:
            sys.exit(f'unknown chunk(s) {bad}; choose from {list(CHUNKS)}')
        current = status(text, blocks) if cmd == 'add' else set()
        write_flags(text, blocks, current | set(args))
        print('now on board:')
        status(*load())
    else:
        sys.exit(__doc__)
