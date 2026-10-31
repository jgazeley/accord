#!/usr/bin/env python3
"""Stage the board in small ordered steps (DECISIONS D-STAGE-11, revised).

The schematic stays complete. Parts outside the steps already switched on
carry KiCad's "Exclude from board" flag, so "Update PCB from Schematic"
leaves them off the board; switching a step on and updating adds just that
step without touching what is already placed.

Each step is one function of 2-10 parts that connects to parts already on
the board, with its own test points. They are in build order: Pico
peripherals, then the vehicle inputs one channel at a time, then the
always-on 5 V rail and ignition, then the power hold and the cutoff timer
chip by chip in signal order.

usage, from logger/hardware/kicad (close KiCad's schematic first; the
schematic file is edited in place):
  python3 tools/board_chunks.py status           # numbered list, next marked
  python3 tools/board_chunks.py next             # switch on the next step
  python3 tools/board_chunks.py add rtc in_tach  # switch on named steps
  python3 tools/board_chunks.py off clk_osc      # switch steps back off
  python3 tools/board_chunks.py full-netlist validation/netlist.net

kicad-cli omits board-excluded symbols from its netlist export, so the
design checks (check_capture.py, check_layout_closure.py) must run on the
FULL netlist: full-netlist exports it from a scratch copy with every part
switched on. Every BOM part is in exactly one step; the script refuses to
run otherwise.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCH = os.path.join(HERE, 'accord-logger.kicad_sch')

# (phase, step, parts, what it is and where it goes)
STEPS = [
    ('placed', 'power', 'C9 C10 C11 C12 C13 C14 D112 D113 D114 D115 D116 L1 '
     'Q5 Q6 Q7 R31 R32 R33 R34 R35 R36 R37 U6',
     'entry protection, QP switch, LM2678 buck, DOR'),
    ('placed', 'pico', 'U1', 'Pico W'),
    ('placed', 'sd', 'C8 J5', 'SD module header and its bulk capacitor'),
    ('placed', 'connector', 'J1', 'the 14-way JAE board connector'),

    ('A  Pico peripherals', 'rtc', 'U16 C25 R50 R51 R52 BT1',
     'DS3231 clock. U16 near Pico GP20-22 (pins 26/27/29, right side, '
     'antenna end); C25 at U16 pins 2/13; R50-R52 pull-ups beside it. BT1 '
     'holder (24 x 21 mm) away from the antenna; the back side is fine'),
    ('A  Pico peripherals', 'rs485', 'U15 C24 R30',
     'MAX3485 (DIP-8 socket) between Pico GP8-10 (pins 11/12/14) and J1 '
     'pins 1/7; C24 at U15 pins 8/5; R30 DE pull-down beside it'),
    ('A  Pico peripherals', 'rs485_links', 'R47 R48 R49 JP2 JP3 JP4',
     '390R bias pair, 120R termination and their three jumpers, next to '
     'U15 pins 6/7 (A/B)'),
    ('A  Pico peripherals', 'headers', 'J3 J4',
     'J3 2x03 spare header (GP11-13 + switched power) by Pico pins 15-17; '
     'J4 RUN-GND reset by pin 30'),
    ('A  Pico peripherals', 'power_tps', 'TP1 TP2 TP3 TP4 TP5 TP6 TP7 TP21 '
     'TP22 TP23',
     'test points on the placed power block: P12, GATE, VIN_SW, SW, B5, '
     'VSYS, 3V3, two PGND, AGND. Each beside the part that makes its net; '
     'AGND near Pico pin 33'),

    ('B  vehicle inputs', 'in_tach', 'R3 R4 D102',
     'B1 tach: J1.4 -> R3 22k -> GP3 (pin 5), R4 6.8k to PGND, D102 clamp '
     'to 3V3 at the Pico pin'),
    ('B  vehicle inputs', 'in_brake', 'R5 R6 D103',
     'C14 brake: J1.13 -> R5 22k -> GP4 (pin 6), R6 6.8k to PGND, D103 '
     'clamp to 3V3 at the Pico pin'),
    ('B  vehicle inputs', 'in_fuel', 'R7 R8 R9 C1 D104 D105',
     'C11 fuel: J1.9 -> R7 7.5k / R8 4.7k -> R9 1k -> GP26 (pin 31); C1 and '
     'the D104/D105 clamps at the ADC pin; returns to AGND, not PGND'),
    ('B  vehicle inputs', 'in_supply', 'D108 R10 R11 R12 C2 D106 D107',
     'B11 supply sense: J1.5 -> D108 TVS right at J1 -> R10 22k / R11 4.7k '
     '-> R12 1k -> GP27 (pin 32); C2 and D106/D107 at the ADC pin; AGND '
     'returns'),
    ('B  vehicle inputs', 'in_vss', 'U3 R1 R2 D101',
     'B2 VSS: J1.3 -> U3 ASSR-601JV relay output -> R1 22k / R2 33k -> GP2 '
     '(pin 4), D101 clamp at the Pico pin. The relay LED driver comes '
     'later (iso_enable)'),

    ('C  always-on 5 V and ignition', 'ign_opto', 'D109 R13 D110 U2',
     'ignition opto: B11 tap -> D109 -> R13 2.2k -> U2 PC817 LED, D110 '
     'across it. U2 output pins 3/4 are the A5 side: keep the two sides apart'),
    ('C  always-on 5 V and ignition', 'a5_clamp', 'R22 D111 TP8',
     'second-stage clamp: R22 820R from P12 to P_AON, D111 22 V zener to '
     'PGND, near the entry protection (D112/D113). Both run warm under '
     'fault, so give them air'),
    ('C  always-on 5 V and ignition', 'a5_reg', 'U4 C4 C5 C6 TP9',
     'TPS70950 always-on 5 V (A5): C4 at its input, C5/C6 at its output'),
    ('C  always-on 5 V and ignition', 'a5_supervisor', 'U5 C7 TP17',
     'TPS3839 supervisor on A5, makes PGOOD; C7 at its supply pin'),
    ('C  always-on 5 V and ignition', 'iso_enable', 'R23 Q3 Q4 R24 R25 R26 '
     'R27 TP20',
     'U3 relay LED driver: R23 270R from B5, Q3 (PGOOD) and Q4 (GP7, pin '
     '10) in series to PGND, with their gate resistors. Next to U3'),
    ('C  always-on 5 V and ignition', 'qual_rc', 'R14 R15 C3 TP12',
     'ignition filter on the opto output: R14 47k, R15 220k, C3 1 uF '
     '(IGN_A -> IGN_RC). Next to U2 pins 3/4'),
    ('C  always-on 5 V and ignition', 'qual_reset', 'Q1 R16 R17 R18',
     'QRESET discharges the ignition filter when BAD: Q1 and R16-R18, next '
     'to C3'),
    ('C  always-on 5 V and ignition', 'qual_report', 'Q2 R19 R20 R21 TP11',
     'QREPORT drives GP5 (pin 7) from IGN_Q: Q2 with R19/R20, R21 10k '
     'pull-up to 3V3 at the Pico pin'),

    ('D  power hold and cutoff timer', 'hold', 'JP1 R28 R29 TP19',
     'HOLD: GP6 (pin 9) -> JP1 maintenance link -> R29 1k -> Q7 base; R28 '
     '47k pull-down at the Pico pin'),
    ('D  power hold and cutoff timer', 'clk_osc', 'U7 R38 C15 C16 TP10',
     '32.768 kHz oscillator U7 on its own filtered rail: R38 1k from A5, '
     'C15 33 uF and C16 10 nF at U7'),
    ('D  power hold and cutoff timer', 'clk_gate', 'U8 C17 U9 C18 TP14',
     'oscillator enable buffer U8 (C17) and clock gate U9 (C18), beside U7'),
    ('D  power hold and cutoff timer', 'schmitt', 'U14 C23 TP13',
     'CD4093 Schmitt gates: conditions the ignition filter and PGOOD into '
     'IGN_Q / BAD. C23 at its supply pins. Near C3 and U5'),
    ('D  power hold and cutoff timer', 'latch', 'U12 C21 TP15',
     'CD4011 ARM latch, C21 at its supply pins. Beside U14'),
    ('D  power hold and cutoff timer', 'or_tree', 'U13 C22',
     'CD4071 reset OR tree, C22 at its supply pins. Beside U12'),
    ('D  power hold and cutoff timer', 'divider', 'U10 C19',
     'CD74HC4060 divides the gated 32 kHz clock; C19 at its supply pins. '
     'Between U9 and U11'),
    ('D  power hold and cutoff timer', 'counter', 'U11 C20 R39 R40 R41 TP16',
     'CD74HC4020 counter, C20 at its supply pins. R39 (0R, production '
     '2048 s) or R40 (0R, 64 s bench test, DNP) picks the tap; R41 pulls '
     'EXPIRED down'),
    ('D  power hold and cutoff timer', 'cutoff_switch', 'Q8 R42 R43',
     'QS series switch in the HOLD sink path (Q7 collector to SINK), with '
     'R42/R43 on its gate. Next to Q6/Q7'),
    ('D  power hold and cutoff timer', 'hold_monitor', 'Q9 R44 R45 R46 TP18',
     'QMON senses HOLD_RAW into HOLD_N for the timer: Q9 with R44-R46'),
]
CHUNKS = {name: refs.split() for _, name, refs, _ in STEPS}
NOTE = {name: note for _, name, _, note in STEPS}
REF_CHUNK = {r: k for k, refs in CHUNKS.items() for r in refs}
assert len(REF_CHUNK) == sum(map(len, CHUNKS.values())), 'part in two steps'


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
        sys.exit(f'step table out of date: not in any step {missing}, '
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


def status(text, blocks, quiet=False):
    ob = on_board(text, blocks)
    on = {k for k, refs in CHUNKS.items() if all(ob[r] for r in refs)}
    nxt = next((n for _, n, _, _ in STEPS if n not in on), None)
    phase = None
    for i, (ph, name, _, _) in enumerate(STEPS):
        refs = CHUNKS[name]
        n = sum(ob[r] for r in refs)
        if quiet:
            continue
        if ph != phase:
            print(f'{ph}:')
            phase = ph
        state = 'ON ' if n == len(refs) else ('off' if n == 0 else 'MIXED')
        mark = '   <- next' if name == nxt else ''
        print(f'  {i:2d} {state} {name:14s} {" ".join(refs)}{mark}')
    return on, nxt


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
        sys.exit()
    on, nxt = status(text, blocks, quiet=True)
    if cmd == 'next':
        if not nxt:
            sys.exit('every step is already on')
        args = [nxt]
    elif cmd not in ('add', 'off', 'only'):
        sys.exit(__doc__)
    bad = [a for a in args if a not in CHUNKS]
    if bad or not args:
        sys.exit(f'unknown step(s) {bad}; choose from {list(CHUNKS)}')
    if cmd == 'off':
        wanted = on - set(args)
    elif cmd == 'only':
        wanted = set(args)
    else:
        wanted = on | set(args)
    write_flags(text, blocks, wanted)
    for a in args:
        if cmd != 'off':
            print(f'switched on {a}: {" ".join(CHUNKS[a])}\n  {NOTE[a]}')
        else:
            print(f'switched off {a}')
    print('Now in KiCad: reopen the schematic, then Update PCB from Schematic.')
