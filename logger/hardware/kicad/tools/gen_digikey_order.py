#!/usr/bin/env python3
"""DigiKey order file for one Rev A board plus spares (DECISIONS D-ORDER-19).

Reads BOM.csv, maps every fitted and DNP line to an orderable manufacturer
part, applies the spares rule and adds the off-board items the owner asked
for. Refuses to write if any BOM row has no mapping, so a BOM change cannot
silently drop a part from the order.

Spares rule (owner, D-ORDER-19): cheap passives and small diodes get one
spare and round up to DigiKey's 10-piece break; cheap ICs and transistors
get one spare; expensive or special parts are ordered exactly.

usage, from logger/hardware/kicad:
  python3 tools/gen_digikey_order.py              # writes order/digikey_rev_a.csv
"""
import csv
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOM = os.path.join(HERE, 'BOM.csv')
OUT = os.path.join(HERE, 'order', 'digikey_rev_a.csv')

R0204 = 'Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal'
R0207 = 'Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical'
R0414 = 'Resistor_THT:R_Axial_DIN0414_L11.9mm_D4.5mm_P5.08mm_Vertical'
R0805 = 'Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder'
C0805 = 'Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder'

# (value, footprint) -> (manufacturer, MPN, rule). Rules: 'p10' passive
# (n + 1, rounded up to 10), 'p1' one spare, 'x' exact.
# DIN0204: Stackpole RNMF14 (1/4 W mini metal film, 3.3 x 1.78 mm body);
# >= 0.2 W at 85 C, which covers R22's >= 0.15 W (D-THT-15).
# DIN0207: Stackpole RNF14 (1/4 W, 6.35 mm body), as the keyless parts.
# DIN0414 vertical: Vishay PR01 (1 W, 0207 body) stands in the vertical
# footprint; covers R13 (0.5 W spec) and R32 (0.259 W fault).
BY_VALUE = {
    ('22k', R0204): ('Stackpole', 'RNMF14FTC22K0', 'p10'),
    ('33k', R0204): ('Stackpole', 'RNMF14FTC33K0', 'p10'),
    ('6.8k', R0204): ('Stackpole', 'RNMF14FTC6K80', 'p10'),
    ('7.5k', R0204): ('Stackpole', 'RNMF14FTC7K50', 'p10'),
    ('4.7k', R0204): ('Stackpole', 'RNMF14FTC4K70', 'p10'),
    ('1k', R0204): ('Stackpole', 'RNMF14FTC1K00', 'p10'),
    ('47k', R0204): ('Stackpole', 'RNMF14FTC47K0', 'p10'),
    ('220k', R0204): ('Stackpole', 'RNMF14FTC220K', 'p10'),
    ('100k', R0204): ('Stackpole', 'RNMF14FTC100K', 'p10'),
    ('10k', R0204): ('Stackpole', 'RNMF14FTC10K0', 'p10'),
    ('820R', R0204): ('Stackpole', 'RNMF14FTC820R', 'p10'),
    ('2.2k', R0204): ('Stackpole', 'RNMF14FTC2K20', 'p10'),
    ('270R', R0204): ('Stackpole', 'RNMF14FTC270R', 'p10'),
    ('10k', R0207): ('Stackpole', 'RNF14FTC10K0', 'p10'),
    ('390R', R0207): ('Stackpole', 'RNF14FTC390R', 'p10'),
    ('120R', R0207): ('Stackpole', 'RNF14FTC120R', 'p10'),
    ('2.2k', R0414): ('Vishay', 'PR01000102201JR500', 'p1'),
    ('1k', R0414): ('Vishay', 'PR01000101001JR500', 'p1'),
    ('0R', R0805): ('Yageo', 'RC0805JR-070RL', 'p10'),
    ('100k', R0805): ('Yageo', 'RC0805FR-07100KL', 'p10'),
    ('1k', R0805): ('Yageo', 'RC0805FR-071KL', 'p10'),
    ('4.7k', R0805): ('Yageo', 'RC0805FR-074K7L', 'p10'),
    ('10k', R0805): ('Yageo', 'RC0805FR-0710KL', 'p10'),
    ('1uF', C0805): ('Samsung', 'CL21B105KAFNNNE', 'p10'),
    ('100nF', C0805): ('Samsung', 'CL21B104KBCNNNC', 'p10'),
    ('100nF/50V', C0805): ('Samsung', 'CL21B104KBCNNNC', 'p10'),
    ('100nF/100V', C0805): ('TDK', 'C2012X7R2A104K125AA', 'p10'),
    ('10nF', C0805): ('Samsung', 'CL21B103KBANNNC', 'p10'),
    ('10nF/50V', C0805): ('Samsung', 'CL21B103KBANNNC', 'p10'),
}

# reference -> (manufacturer, MPN, rule) for named parts
BY_REF = {
    'J1': ('JAE', 'IL-AG5-14P-D3L2-A', 'x'),
    'U3': ('Broadcom', 'ASSR-601JV-000E', 'x'),
    'U1': ('Raspberry Pi', 'SC0918', 'x'),
    'U2': ('Sharp', 'PC817XNNSZ1B', 'p1'),
    'U4': ('Texas Instruments', 'TPS70950QDBVRQ1', 'p1'),
    'U5': ('Texas Instruments', 'TPS3839K50DBZR', 'p1'),
    'U6': ('Texas Instruments', 'LM2678T-5.0/NOPB', 'x'),
    'U7': ('Micro Crystal', 'OV-7604-C7-32.768KHZ-20PPM-TA-QC', 'p1'),
    'U8': ('Nexperia', '74AHC1G17GV,125', 'p1'),
    'U9': ('Texas Instruments', 'SN74LVC1G97DBVR', 'p1'),
    'U10': ('Texas Instruments', 'CD74HC4060M96', 'p1'),
    'U11': ('Texas Instruments', 'CD74HC4020M96', 'p1'),
    'U12': ('Texas Instruments', 'CD4011BM96', 'p1'),
    'U13': ('Texas Instruments', 'CD4071BM96', 'p1'),
    'U14': ('Texas Instruments', 'CD4093BM96', 'p1'),
    'U15': ('Analog Devices', 'MAX3485EPA+', 'x'),
    'U16': ('Analog Devices', 'DS3231SN#', 'x'),
    'Q1': ('onsemi', 'MMBT3904LT1G', 'p1'), 'Q9': ('onsemi', 'MMBT3904LT1G', 'p1'),
    'Q2': ('Nexperia', 'BSS138P,215', 'p1'), 'Q3': ('Nexperia', 'BSS138P,215', 'p1'),
    'Q4': ('Nexperia', 'BSS138P,215', 'p1'), 'Q8': ('Nexperia', 'BSS138P,215', 'p1'),
    'Q5': ('Infineon', 'IPD50P04P4L11ATMA2', 'p1'),
    'Q6': ('onsemi', '2N3904BU', 'p1'), 'Q7': ('onsemi', '2N3904BU', 'p1'),
    'L1': ('Bourns', 'RLB0912-220KL', 'x'),
    'D108': ('Vishay', '1.5KE20A-E3/54', 'p1'), 'D113': ('Vishay', '1.5KE20A-E3/54', 'p1'),
    'D112': ('Vishay', 'SB360-E3/54', 'p1'), 'D115': ('Vishay', 'SB360-E3/54', 'p1'),
    'D110': ('Diodes Inc', '1N4148W-7-F', 'p10'),
    'D111': ('Vishay', 'BZX55C22-TAP', 'p10'),
    'D114': ('Vishay', 'BZX55C10-TAP', 'p10'),
    'D116': ('Vishay', '1N4004-E3/54', 'p10'),
    'C3': ('WIMA', 'MKS2C041001F00JSSD', 'p1'),
    'C4': ('Murata', 'GRM32ER71H475KA88L', 'p10'),
    'C5': ('Murata', 'GRM32ER71H475KA88L', 'p10'),
    'C6': ('Murata', 'GRM32ER71H475KA88L', 'p10'),
    'C8': ('Panasonic', 'EEU-FC1V470', 'p1'),
    'C10': ('Panasonic', 'EEU-FR1H101', 'p1'),
    'C14': ('Panasonic', 'EEU-FR1C102', 'p1'),
    'C15': ('KYOCERA AVX', 'TAP336K016SCS', 'p1'),
    'BT1': ('Keystone', '3034', 'x'),
    'TP21': ('Keystone', '5001', 'p10'), 'TP22': ('Keystone', '5001', 'p10'),
    'TP23': ('Keystone', '5001', 'p10'),
}
for _d in ('D101', 'D102', 'D103', 'D104', 'D105', 'D106', 'D107', 'D109'):
    BY_REF[_d] = ('onsemi', '1N5819RLG', 'p10')

# Single-row headers come from one breakaway strip; J3 is its own 2x03.
HEADER_STRIP = ('JP1', 'JP2', 'JP3', 'JP4', 'J4', 'J5')
BY_REF['J3'] = ('Sullins', 'PRPC003DAAN-RC', 'p1')
# Copper pads only: nothing to order.
PAD_ONLY = 'TestPoint:TestPoint_Pad_D2.0mm'

EXTRAS = [  # (manufacturer, MPN, qty, what for)
    ('Sullins', 'PREC040SAAN-RC', 1,
     '1x40 breakaway header: JP1-JP4, J4 (1x02) and J5 (1x06), 16 pins'),
    ('Sullins', 'QPC02SXGN-RC', 10, 'jumper shunts: JP1 HOLD link, J4, spares'),
    ('Mill-Max', '110-43-308-41-001000', 1, 'DIP-8 socket for U15 MAX3485, as keyless'),
    ('Panasonic', 'BR-2032/BN', 1, 'BT1 cell, BR chemistry rated to +85 C'),
    ('JAE', 'IL-AG5-14S-D3C1-A', 2, 'harness mating housing for J1'),
    ('JAE', 'IL-AG5-C1-5000', 20, 'harness crimp socket contacts, 22-18 AWG (14 + spares)'),
    ('Littelfuse', 'FHAC0001ZXJ', 1, 'inline ATO fuse holder for the harness feed (D-FUSE-10)'),
    ('Littelfuse', '0287001.PXCN', 5, '1 A ATO fuse (D-FUSE-10)'),
]


def qty(n, rule):
    if rule == 'p10':
        return max(10, math.ceil((n + 1) / 10) * 10)
    return n + 1 if rule == 'p1' else n


def main():
    rows = list(csv.DictReader(open(BOM, newline='', encoding='utf-8')))
    lines, missing = {}, []
    for r in rows:
        ref, fp = r['reference'], r['footprint']
        if ref in HEADER_STRIP or fp == PAD_ONLY:
            continue
        m = BY_REF.get(ref) or BY_VALUE.get((r['value'], fp))
        if not m:
            missing.append(f"{ref} {r['value']} {fp}")
            continue
        key = (m[0], m[1])
        e = lines.setdefault(key, {'refs': [], 'rule': m[2], 'value': r['value']})
        e['refs'].append(ref + (' (DNP)' if r['population'] == 'DNP' else ''))
    if missing:
        sys.exit('no DigiKey mapping for: ' + '; '.join(missing))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['Quantity', 'Manufacturer Part Number', 'Manufacturer',
                    'Board quantity', 'Reference Designators', 'Notes'])
        for (mfr, mpn), e in lines.items():
            n = len(e['refs'])
            w.writerow([qty(n, e['rule']), mpn, mfr, n, ' '.join(e['refs']),
                        e['value']])
        for mfr, mpn, q, why in EXTRAS:
            w.writerow([q, mpn, mfr, '', '', why])
    print(f'wrote {OUT}: {len(lines)} board lines + {len(EXTRAS)} extras')


if __name__ == '__main__':
    main()
