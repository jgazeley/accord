#!/usr/bin/env python3
"""Check the schematic against the documents the circuit comes from.

Reads validation/netlist.net and BOM.csv and asserts, connection by
connection, that the drawing says what the source documents say:

  REV_A_INTERFACES S1   the Rev A pin map, and which pins stay free
  AS_BUILT S2/S3.4a     the five fitted input cells and the opto pinout
  DESIGN.md S3          the power connection list
  CUTOFF_MARGIN_REVIEW  S1 clock block, S2 qualified IGN / reset / report,
                        S3 the always-on supply boundary
  MAX_ON_CUTOFF         the latch, counter, permission-switch and HOLD-sense
                        connection tables, and their Boolean equations
  LAYOUT_CLOSURE.md     the LRA-12 decisions: entry clamp, A5 second stage,
                        B2 isolation and its enable, the four bypassed
                        branches, connectors, the LED return and the
                        cutoff-period selection

It proves the drawing agrees with the written design. It proves nothing about
circuit behaviour: for the numbers, run ../power/check_layout_closure.py.

Two habits here are deliberate, both learned on this board. Assertions are
made against the EXPORTED NETLIST, which is what gets built, not against the
parts table that generated it - a check that reads the same table twice only
proves the table is self-consistent. And every part whose symbol cannot
express polarity is pinned down by pin number, with a guard that fails if a
future part arrives in the same blind spot.

Usage: python3 check_capture.py [project-dir]
"""
import csv
import os
import re
import sys

_ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
HERE = (_ARGS[0] if _ARGS
        else os.path.dirname(os.path.abspath(__file__)))
NET = os.path.join(HERE, 'validation', 'netlist.net')
BOM = os.path.join(HERE, 'BOM.csv')

fails = []
checks = 0


def check(label, ok, detail=''):
    global checks
    checks += 1
    if not ok:
        fails.append(f'{label}: {detail}')


# ----------------------------------------------------------------- netlist
text = open(NET, encoding='utf-8').read()
nets = {}
for m in re.finditer(
        r'\(net \(code "\d+"\) \(name "([^"]*)"\)(.*?)(?=\n    \(net |\Z)',
        text, re.S):
    name = m.group(1).lstrip('/')
    nodes = set(re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)',
                           m.group(2)))
    nets[name] = nodes
pin_net = {}
for name, nodes in nets.items():
    for ref, pin in nodes:
        pin_net[(ref, pin)] = name
NAMED = {n for n in nets if not n.startswith('unconnected-')}

bom = list(csv.DictReader(open(BOM, encoding='utf-8')))
by_src = {r['source_designator']: r for r in bom}
by_ref = {r['reference']: r for r in bom}


dups = sorted({r['source_designator'] for r in bom
               if sum(1 for q in bom
                      if q['source_designator'] == r['source_designator']) > 1})
check('no duplicate source designator in the BOM', not dups,
      f'{dups} would collide in the BOM and in every lookup by designator')
refs = [r['reference'] for r in bom]
check('no duplicate KiCad reference', len(refs) == len(set(refs)))


def by_role(src, role):
    """Net on a transistor pin by its role (E/B/C), independent of package."""
    for _blk in text.split('(net (code')[1:]:
        _n = re.search(r'\(name "([^"]*)"', _blk).group(1).lstrip('/')
        if re.search(r'\(node \(ref "%s"\) \(pin "[^"]+"\) \(pinfunction "%s"\)'
                     % (re.escape(R(src)), role), _blk):
            return _n
    return None


def R(src):
    """The KiCad reference for a source designator."""
    return by_src[src]['reference'] if src in by_src else '<missing:%s>' % src


def unconnected(ref, pin):
    """True when the pin carries no net.

    An explicit no-connect flag is reported by kicad-cli as a single-node
    'unconnected-(<ref>-<pin>)' net; a symbol pin typed `free` simply does
    not appear at all. Both are deliberate non-connection.
    """
    net = pin_net.get((ref, pin))
    return net is None or net.startswith('unconnected-')


def wires(label, src, mapping):
    """Assert a part's whole pin-to-net mapping, by source designator."""
    ref = R(src)
    for pin, net in mapping.items():
        check(f'{label}: {ref} ({src}) pin {pin} -> {net}',
              pin_net.get((ref, str(pin))) == net,
              f'got {pin_net.get((ref, str(pin)))!r}')


def value(src, want):
    r = by_src.get(src)
    check(f'{src} value is {want}', r is not None and r['value'] == want,
          f'got {r and r["value"]!r}')


def only(net, allowed_srcpins, why=''):
    """Assert exactly which pins a net reaches.

    This catches a label stub landing on a neighbouring pin, and it is what
    makes an isolation claim mean anything: a switch upstream of a divider is
    only isolation if nothing else sits on the upstream net.
    """
    want = {(R(s), str(p)) for s, p in allowed_srcpins}
    got = nets.get(net, set())
    check(f'net {net} reaches exactly its intended pins', got == want,
          f'extra {sorted(got - want)}, missing {sorted(want - got)}. {why}')


# ------------------------------- REV_A_INTERFACES section 1, Rev A column
PINMAP = {
    '4': 'VSS_IN',          # GP2  VSS in
    '5': 'TACH_IN',         # GP3  Tach in
    '6': 'BRAKE_IN',        # GP4  Brake warning in
    '7': 'QUAL_N_REPORT',   # GP5  hardware-qualified ignition report
    '9': 'HOLD_RAW',        # GP6  HOLD
    '10': 'ISO_EN',         # GP7  B2 isolation enable, taken up by LRA-12
    '11': 'UART1_TX',       # GP8  offered to the expansion header
    '12': 'UART1_RX',       # GP9
    '14': 'BUS_DE',         # GP10 tied DE//RE
    '15': 'SPARE_GP11',
    '16': 'SPARE_GP12',
    '17': 'SPARE_GP13',     # GP13 offered as an expansion spare
    '21': 'SD_MISO',        # GP16
    '22': 'SD_CS',          # GP17
    '24': 'SD_SCK',         # GP18
    '25': 'SD_MOSI',        # GP19
    '26': 'RTC_SDA',        # GP20 I2C0 SDA, DS3231 (D-RTC-14)
    '27': 'RTC_SCL',        # GP21 I2C0 SCL
    '29': 'RTC_INT',        # GP22 DS3231 INT/SQW
    '30': 'RUN',
    '31': 'FUEL_ADC',       # GP26 ADC0
    '32': 'SUPPLY_ADC',     # GP27 ADC1
    '33': 'AGND',
    '36': 'P3V3_SW',
    '39': 'VSYS',
    '3': 'PGND',
}
for pin, net in PINMAP.items():
    check(f'U1 pin {pin} -> {net}', pin_net.get(('U1', pin)) == net,
          f'got {pin_net.get(("U1", pin))!r}')

# Pins that must stay unconnected. GP0/GP1 stay free; GP14/15 are
# unassigned; GP28 is the last ADC channel. GP20-22 went to the RTC.
FREE = {'1': 'GP0', '2': 'GP1', '19': 'GP14', '20': 'GP15',
        '34': 'GP28', '35': 'ADC_VREF', '37': '3V3_EN', '40': 'VBUS'}
for pin, label in FREE.items():
    check(f'U1 pin {pin} ({label}) unconnected', unconnected('U1', pin),
          f'on net {pin_net.get(("U1", pin))!r}')
for pin in ('3', '8', '13', '18', '23', '28', '38'):
    check(f'U1 pin {pin} GND -> PGND', pin_net.get(('U1', pin)) == 'PGND',
          f'got {pin_net.get(("U1", pin))!r}')

# No rail but switched 3V3 may be tied to a GPIO net through a resistor.
GPIO_NETS = set(PINMAP.values()) - {'PGND', 'AGND', 'P3V3_SW', 'VSYS'}
for r in bom:
    if not r['symbol'].startswith('Device:R'):
        continue
    ends = {pin_net.get((r['reference'], '1')),
            pin_net.get((r['reference'], '2'))}
    if ends & GPIO_NETS and ends & {'A5', 'B5', 'P12', 'P_AON', 'VCLK'}:
        check(f'{r["reference"]} does not tie a GPIO to a non-3V3 rail',
              False, f'between {sorted(x for x in ends if x)}')
checks += 1        # the absence of any such part is itself one check

# ------------------------------------------- AS_BUILT section 2 input cells
CELLS = {
    'VSS':  ('B2_ISO',  '22k',  '33k',  'PGND'),
    'TACH': ('B1_TAP',  '22k',  '6.8k', 'PGND'),
    'BRK':  ('C14_TAP', '22k',  '6.8k', 'PGND'),
    'FUEL': ('C11_TAP', '7.5k', '4.7k', 'AGND'),
    'SUP':  ('B11_TAP', '22k',  '4.7k', 'AGND'),
}
for key, (top_net, rt, rb, ret) in CELLS.items():
    value(f'R_{key}_T', rt)
    value(f'R_{key}_B', rb)
    check(f'{key} divider top is fed from {top_net}',
          pin_net.get((R(f'R_{key}_T'), '1')) == top_net,
          f'got {pin_net.get((R(f"R_{key}_T"), "1"))!r}')
    check(f'{key} divider bottom returns to {ret}',
          pin_net.get((R(f'R_{key}_B'), '2')) == ret,
          f'got {pin_net.get((R(f"R_{key}_B"), "2"))!r}')

for key, adc in (('FUEL', 'FUEL_ADC'), ('SUP', 'SUPPLY_ADC')):
    value(f'R_{key}_S', '1k')
    value(f'C_{key}', '1uF')
    check(f'{key} upper clamp anode at the pin',
          pin_net.get((R(f'D_{key}_H'), '2')) == adc
          and pin_net.get((R(f'D_{key}_H'), '1')) == 'P3V3_SW',
          'upper clamp orientation wrong')
    check(f'{key} lower clamp cathode at the pin',
          pin_net.get((R(f'D_{key}_L'), '1')) == adc
          and pin_net.get((R(f'D_{key}_L'), '2')) == 'AGND',
          'lower clamp orientation wrong')
for key, sig in (('VSS', 'VSS_IN'), ('TACH', 'TACH_IN'), ('BRK', 'BRAKE_IN')):
    check(f'{key} clamp anode at the pin',
          pin_net.get((R(f'D_{key}'), '2')) == sig
          and pin_net.get((R(f'D_{key}'), '1')) == 'P3V3_SW',
          'clamp orientation wrong')

# -------------------------------------- X1 resolved: the B2 series isolation
# The point of the part is that nothing bridges it, so these net-identity
# assertions carry the whole isolation claim.
only('B2_TAP', [('J1', 3), ('UISO', 15), ('UISO', 16)],
     'the B2 divider top must be reachable only through the relay')
only('B2_ISO', [('UISO', 9), ('UISO', 10), ('R_VSS_T', 1)],
     'the relay output feeds the divider top and nothing else')
only('ISO_LED_K', [('UISO', 5), ('QISO_PG', 3)],
     'the LED cathode must reach only the permission switch')
only('ISO_MID', [('QISO_PG', 2), ('QISO_EN', 3)],
     'the two switch channels must be in series, not in parallel')
wires('isolation relay', 'UISO',
      {4: 'ISO_LED_A', 5: 'ISO_LED_K', 9: 'B2_ISO', 10: 'B2_ISO',
       15: 'B2_TAP', 16: 'B2_TAP'})
check('UISO pin 3 is left unconnected, as the datasheet requires',
      unconnected(R('UISO'), '3'),
      'pin 3 is internally tied to pin 5, the LED cathode')
for p in ('1', '2', '6', '7', '8'):
    check(f'UISO pin {p} (NC lead) unconnected', unconnected(R('UISO'), p),
          f'on {pin_net.get((R("UISO"), p))!r}')
check('the relay footprint is the local 12-pad variant, not a stock SOIC-16W',
      by_src['UISO']['footprint'].startswith('accord-logger:ASSR-601Jx'),
      f'got {by_src["UISO"]["footprint"]!r}')

value('R_ISO', '270R')
wires('iso enable', 'R_ISO', {1: 'B5', 2: 'ISO_LED_A'})
wires('iso enable', 'QISO_PG', {1: 'ISO_PG_G', 2: 'ISO_MID', 3: 'ISO_LED_K'})
wires('iso enable', 'QISO_EN', {1: 'ISO_EN_G', 2: 'PGND', 3: 'ISO_MID'})
wires('iso enable', 'R_ISOEN', {1: 'ISO_EN', 2: 'ISO_EN_G'})
wires('iso enable', 'R_ISOEN_PD', {1: 'ISO_EN_G', 2: 'PGND'})
wires('iso enable', 'R_ISOPG', {1: 'PGOOD', 2: 'ISO_PG_G'})
wires('iso enable', 'R_ISOPG_PD', {1: 'ISO_PG_G', 2: 'PGND'})
check('the isolation LED is fed from a rail that dies with the board',
      pin_net.get((R('R_ISO'), '1')) == 'B5',
      'an always-on rail here would leave B2 connected while parked, which '
      'is the fault this part exists to remove')
check('both enable gates are pulled down, so the relay is open by default',
      pin_net.get((R('R_ISOEN_PD'), '2')) == 'PGND'
      and pin_net.get((R('R_ISOPG_PD'), '2')) == 'PGND')

# ------------------- X2-X5: the four branches decided as a justified bypass
# Positive assertion of the decision: each tap reaches its divider top
# directly, with no isolation device on it. B11 also feeds the ignition opto
# through DI and carries the entry clamp.
BYPASSED = {
    'B1_TAP': [('J1', 4), ('R_TACH_T', 1)],
    'C14_TAP': [('J1', 13), ('R_BRK_T', 1)],
    'C11_TAP': [('J1', 9), ('R_FUEL_T', 1)],
    'B11_TAP': [('J1', 5), ('R_SUP_T', 1), ('DI', 2), ('TVS_B11', 1)],
}
for net, allowed in BYPASSED.items():
    only(net, allowed, 'this branch is a decided bypass: its tap feeds the '
                       'fitted divider and nothing else')
check('no signal-isolation placeholder survives anywhere',
      not any('SIGNAL_ISOLATION' in r['value'] for r in bom))
check('no placeholder of any kind survives',
      not any(r['symbol'].startswith('Custom:PLACEHOLDER') for r in bom),
      'X1-X8 are resolved; a dashed body would contradict that')
value('TVS_B11', '1.5KE20A-E3/54')
wires('entry clamp', 'TVS_B11', {1: 'B11_TAP', 2: 'PGND'})

# --------------------------- ignition cell, AS_BUILT 3.4 with the LRA-12 fix
value('DI', '1N5819HW')
value('RLED', '2.2k')
wires('opto cell', 'U2', {1: 'IGN_LED_A', 2: 'PGND', 3: 'IGN_A', 4: 'A5'})
check('the opto LED cathode returns to PGND, not to the B16 conductor',
      pin_net.get(('U2', '2')) == 'PGND'
      and pin_net.get(('U2', '2')) != pin_net.get(('J1', '10')),
      'R06-REV-2: B16 is a reference and must never carry the LED current')
check('no capacitor sits across the old opto output node',
      'C_IGN' not in by_src,
      'the node it filtered no longer exists after the X6 rewire')
check('no fuse is fitted on the board (D-FUSE-10: harness inline fuse)',
      not any(r['symbol'] == 'Device:Fuse' for r in bom))
check('BATT_IN runs straight from J1 to the reverse-block diode',
      sorted(n for n, net in pin_net.items() if net == 'BATT_IN')
      == sorted([('J1', '6'), (R('DREV'), '2')]))
check('the onboard ignition fuse is not fitted',
      'FIGN' not in by_src,
      'per-branch fuses belong at the tap end (D10)')
check('the opto collector does not reach GP5 directly',
      pin_net.get(('U2', '4')) != pin_net.get(('U1', '7')),
      'the old raw-GP5 arrangement would violate D-RA-03')
check('the opto reverse clamp is antiparallel with the LED',
      pin_net.get((R('DR'), '1')) == 'IGN_LED_A'
      and pin_net.get((R('DR'), '2')) == 'PGND',
      'with the cathode on PGND the clamp has to share both nodes')

# ---------------------------------------- X6 resolved: qualified ignition
for src, want in (('RIGNA', '47k'), ('RRC', '220k'), ('CQUAL', '1uF'),
                  ('R_RSTB', '22k'), ('R_RSTPD', '100k'),
                  ('R_RSTC', '4.7k'), ('R_REPG', '1k'),
                  ('R_REPPD', '100k'), ('RIGN', '10k')):
    value(src, want)
wires('IGN filter', 'RIGNA', {1: 'IGN_A', 2: 'PGND'})
wires('IGN filter', 'RRC', {1: 'IGN_A', 2: 'IGN_RC'})
wires('IGN filter', 'CQUAL', {1: 'IGN_RC', 2: 'PGND'})
wires('IGN reset', 'QRESET', {2: 'PGND', 1: 'RST_B', 3: 'RST_C'})
wires('IGN reset', 'R_RSTB', {1: 'BAD', 2: 'RST_B'})
wires('IGN reset', 'R_RSTPD', {1: 'RST_B', 2: 'PGND'})
wires('IGN reset', 'R_RSTC', {1: 'RST_C', 2: 'IGN_RC'})
wires('IGN report', 'QREPORT', {1: 'REP_G', 2: 'PGND', 3: 'QUAL_N_REPORT'})
wires('IGN report', 'R_REPG', {1: 'IGN_Q', 2: 'REP_G'})
wires('IGN report', 'R_REPPD', {1: 'REP_G', 2: 'PGND'})
wires('IGN report', 'RIGN', {1: 'P3V3_SW', 2: 'QUAL_N_REPORT'})
only('QUAL_N_REPORT', [('QREPORT', 3), ('RIGN', 2), ('TP_QUALN', 1),
                       ('U1', 7)],
     'nothing else may load or feed the report node')
check('the report node carries no capacitor, so its delay is not an unknown',
      not any(r['symbol'].startswith('Device:C')
              and 'QUAL_N_REPORT' in (pin_net.get((r['reference'], '1')),
                                      pin_net.get((r['reference'], '2')))
              for r in bom),
      'D1 asks for the report delay to sit inside the 10 ms budget; with no '
      'capacitor it is the pullup against node capacitance alone')
check('IGN_RC rises for ON: the filter charges through RRC from IGN_A',
      pin_net.get((R('RRC'), '1')) == 'IGN_A',
      'an empty capacitor must mean OFF (CUTOFF_MARGIN_REVIEW S2)')

# ---------------------------------- X7 second stage and the A5 rail
value('R_AON', '820R')
value('DZ_AON', 'BZX55C22')
wires('A5 supply', 'R_AON', {1: 'P12', 2: 'P_AON'})
wires('A5 supply', 'DZ_AON', {1: 'P_AON', 2: 'PGND'})
wires('A5 supply', 'C_AON', {1: 'P_AON', 2: 'PGND'})
wires('A5 supply', 'UA5', {1: 'P_AON', 2: 'PGND', 5: 'A5'})
check('the A5 regulator enable is left open to enable',
      unconnected(R('UA5'), '3'),
      'its absolute maximum is 7 V; it must never be tied to a rail')
check('the A5 regulator is fed through the second stage, not from P12',
      pin_net.get((R('UA5'), '1')) == 'P_AON',
      'the <=28 V protected-rail criterion is met at P_AON')
for ref in ('C_A5A', 'C_A5B'):
    wires('A5 output capacitance', ref, {1: 'A5', 2: 'PGND'})
wires('supervisor', 'USUP', {1: 'PGND', 2: 'PGOOD', 3: 'A5'})
wires('supervisor', 'C_USUP', {1: 'A5', 2: 'PGND'})
value('TVS', '1.5KE20A-E3/54')
wires('entry clamp', 'TVS', {1: 'P12', 2: 'PGND'})
check('the entry clamp is not the 41.4 V inherited part',
      '1.5KE30A' not in by_src['TVS']['value'],
      'that clamp is above the 40 V ratings of QI, QH, the LM2678 and QP')

# -------------------------------------- X8 resolved: the independent cutoff
value('RGS', '10k')
value('DZ', 'BZX55C10')
wires('clock', 'RCLK', {1: 'A5', 2: 'VCLK'})
wires('clock', 'CCLK', {1: 'VCLK', 2: 'PGND'})
wires('clock', 'C_CLK', {1: 'VCLK', 2: 'PGND'})
wires('clock', 'UXO', {4: 'VCLK', 3: 'CLKOE', 2: 'PGND', 1: 'XO_OUT'})
wires('clock', 'UOE', {2: 'ARM', 3: 'PGND', 4: 'CLKOE', 5: 'VCLK'})
wires('clock', 'UGCLK', {1: 'PGND', 2: 'PGND', 3: 'XO_OUT', 4: 'CLK32',
                         5: 'A5', 6: 'ARM'})
check('the oscillator enable buffer runs from the filtered rail, not A5',
      pin_net.get((R('UOE'), '5')) == 'VCLK',
      'it must not inject A5 into the oscillator enable pin')
only('XO_OUT', [('UXO', 1), ('UGCLK', 3)],
     'total XO_OUT load must stay inside 10 pF, so nothing else sits here')

wires('counter', 'UCLK', {16: 'A5', 8: 'PGND', 12: 'COUNT1_RESET',
                          11: 'CLK32', 3: 'UCLK_Q14'})
for p in ('9', '10'):
    check(f'UCLK pin {p} (internal oscillator) left open',
          unconnected(R('UCLK'), p),
          'the external clock drives pin 11 instead')
wires('counter', 'UCOUNT', {16: 'A5', 8: 'PGND', 10: 'UCLK_Q14',
                            11: 'BASE_RESET', 2: 'CNT_Q13', 13: 'CNT_Q8'})
check('UCOUNT is not reset by NARM',
      pin_net.get((R('UCOUNT'), '11')) == 'BASE_RESET',
      'resetting it from NARM would erase EXPIRED as it disarmed the latch')
wires('latch', 'ULATCH', {1: 'SET_N', 2: 'NARM', 3: 'ARM', 4: 'NARM',
                          5: 'RESET_N', 6: 'ARM', 7: 'PGND', 8: 'QUAL_N',
                          9: 'QUAL_N', 10: 'IGN_Q', 12: 'PGND', 13: 'PGND',
                          14: 'A5'})
check('the unused latch gate has its inputs tied to a rail',
      pin_net.get((R('ULATCH'), '12')) == 'PGND'
      and pin_net.get((R('ULATCH'), '13')) == 'PGND',
      'a floating CMOS input draws current and can oscillate')
check('the unused latch gate output is left open',
      unconnected(R('ULATCH'), '11'))
wires('reset tree', 'UOR', {1: 'BAD', 2: 'IGN_Q', 3: 'BASE_RESET',
                            4: 'COUNT1_RESET', 5: 'BASE_RESET', 6: 'NARM',
                            7: 'PGND', 8: 'BAD', 9: 'EXPIRED',
                            10: 'FAULT_RESET', 11: 'ARM_RESET',
                            12: 'FAULT_RESET', 13: 'HOLD_N', 14: 'A5'})
wires('qualifier', 'USCH', {1: 'IGN_RC', 2: 'A5', 3: 'QUAL_N', 4: 'BAD',
                            5: 'PGOOD', 6: 'PGOOD', 7: 'PGND',
                            8: 'ARM_RESET', 9: 'ARM_RESET', 10: 'RESET_N',
                            11: 'SET_N', 12: 'IGN_Q', 13: 'RESET_N',
                            14: 'A5'})

# The Boolean equations of MAX_ON_CUTOFF, read back off the netlist by package
# pin rather than retyped: (label, package, input pins, output pin,
# expected input nets, expected output net).
GATES = [
    ('BASE_RESET = BAD OR IGN_Q', 'UOR', (1, 2), 3,
     {'BAD', 'IGN_Q'}, 'BASE_RESET'),
    ('COUNT1_RESET = BASE_RESET OR NARM', 'UOR', (5, 6), 4,
     {'BASE_RESET', 'NARM'}, 'COUNT1_RESET'),
    ('FAULT_RESET = BAD OR EXPIRED', 'UOR', (8, 9), 10,
     {'BAD', 'EXPIRED'}, 'FAULT_RESET'),
    ('ARM_RESET = FAULT_RESET OR HOLD_N', 'UOR', (12, 13), 11,
     {'FAULT_RESET', 'HOLD_N'}, 'ARM_RESET'),
    ('RESET_N = NOT ARM_RESET', 'USCH', (8, 9), 10,
     {'ARM_RESET'}, 'RESET_N'),
    ('SET_N = NOT (IGN_Q AND RESET_N)', 'USCH', (12, 13), 11,
     {'IGN_Q', 'RESET_N'}, 'SET_N'),
    ('QUAL_N = Schmitt NOT IGN_RC', 'USCH', (1, 2), 3,
     {'IGN_RC', 'A5'}, 'QUAL_N'),
    ('BAD = NOT PGOOD', 'USCH', (5, 6), 4, {'PGOOD'}, 'BAD'),
    ('ARM = NAND(SET_N, NARM)', 'ULATCH', (1, 2), 3,
     {'SET_N', 'NARM'}, 'ARM'),
    ('NARM = NAND(RESET_N, ARM)', 'ULATCH', (5, 6), 4,
     {'RESET_N', 'ARM'}, 'NARM'),
    ('IGN_Q = NOT QUAL_N', 'ULATCH', (8, 9), 10, {'QUAL_N'}, 'IGN_Q'),
]
for label, src, ins, out, want_in, want_out in GATES:
    got_in = {pin_net.get((R(src), str(p))) for p in ins}
    check(f'{src}: {label} inputs', got_in == want_in,
          f'got {sorted(x or "None" for x in got_in)}, '
          f'want {sorted(want_in)}')
    check(f'{src}: {label} output',
          pin_net.get((R(src), str(out))) == want_out,
          f'got {pin_net.get((R(src), str(out)))!r}')

# the permission switch, which is where the cutoff acts on the HOLD path
wires('permission switch', 'QS', {1: 'ARM_G', 2: 'QH_C', 3: 'SINK'})
wires('permission switch', 'R_QSG', {1: 'ARM', 2: 'ARM_G'})
wires('permission switch', 'R_QSPD', {1: 'ARM_G', 2: 'PGND'})
check('QS is in series between SINK and the QH collector',
      pin_net.get((R('QH'), '3')) == 'QH_C'
      and pin_net.get((R('QS'), '2')) == 'QH_C'
      and pin_net.get((R('QS'), '3')) == 'SINK',
      'capture question Q6: the inhibit has to interrupt the HOLD sink path')
only('QH_C', [('QH', 3), ('QS', 2)],
     'nothing may bridge the permission switch')
check('QI still sinks directly, so raw ignition overrides the cutoff',
      pin_net.get((R('QI'), '3')) == 'SINK')
check('QH keeps its emitter grounded',
      by_role('QH', 'E') == 'PGND',
      'interrupting the emitter would couple fault voltage into HOLD')
wires('HOLD sense', 'QMON', {2: 'PGND', 1: 'MON_B', 3: 'HOLD_N'})
wires('HOLD sense', 'R_MONB', {1: 'HOLD_RAW', 2: 'MON_B'})
wires('HOLD sense', 'R_MONPD', {1: 'MON_B', 2: 'PGND'})
wires('HOLD sense', 'R_MONC', {1: 'HOLD_N', 2: 'A5'})
check('QMON senses HOLD_RAW ahead of the JH maintenance link',
      pin_net.get((R('R_MONB'), '1')) == 'HOLD_RAW',
      'opening JH must release QH without blinding the monitor')
check('the A5 pullup stays on HOLD_N, not on the GPIO',
      {pin_net.get((R('R_MONC'), '1')),
       pin_net.get((R('R_MONC'), '2'))} == {'HOLD_N', 'A5'})

# the cutoff-period selection: exactly one link, clearly distinguished
wires('period select', 'R_EXPP', {1: 'CNT_Q13', 2: 'EXPIRED'})
wires('period select', 'R_EXPT', {1: 'CNT_Q8', 2: 'EXPIRED'})
wires('period select', 'R_EXP', {1: 'EXPIRED', 2: 'PGND'})
check('the production period link is fitted',
      by_src['R_EXPP']['population'] == 'FIT',
      f'got {by_src["R_EXPP"]["population"]!r}')
check('the accelerated test link is DNP',
      by_src['R_EXPT']['population'] == 'DNP',
      'fitting both would short two counter outputs together')
check('exactly one period link is populated',
      sum(1 for s in ('R_EXPP', 'R_EXPT')
          if by_src[s]['population'] == 'FIT') == 1)
check('EXPIRED cannot float with neither link fitted',
      pin_net.get((R('R_EXP'), '2')) == 'PGND')
check('the maintenance HOLD link and the period select are different things',
      by_src['JH']['value'] == 'HOLD link'
      and by_src['R_EXPP']['value'] == '0R')

# one local bypass per logic package, on that package's own supply
for cap, rail in (('C_UCLK', 'A5'), ('C_UCOUNT', 'A5'), ('C_ULATCH', 'A5'),
                  ('C_UOR', 'A5'), ('C_USCH', 'A5'), ('C_GCLK', 'A5'),
                  ('C_USUP', 'A5'), ('C_OE', 'VCLK')):
    wires('bypass', cap, {1: rail, 2: 'PGND'})
    value(cap, '100nF')

# ------------------------------------------------- HOLD path, delta D2
value('RPD', '47k')
wires('HOLD driver', 'RPD', {1: 'HOLD_RAW', 2: 'PGND'})
wires('HOLD driver', 'JH', {1: 'HOLD_RAW', 2: 'HOLD_JH'})
wires('HOLD driver', 'RH', {1: 'HOLD_JH', 2: 'HOLD_B'})
wires('HOLD driver', 'RBH', {1: 'HOLD_B', 2: 'PGND'})

# --------------------------------------------------------- SD, delta D6
check('SD module is on switched 3V3', pin_net.get(('J5', '1')) == 'P3V3_SW')
wires('SD bulk', 'C_SD', {1: 'P3V3_SW', 2: 'PGND'})
check('the SD bulk value is selected, not a range',
      by_src['C_SD']['value'] == '47uF/16V',
      f'got {by_src["C_SD"]["value"]!r}')

# ------------------------------------------- DS3231 RTC, D-RTC-14
# SOIC-16 pinout from the DS3231 datasheet: 1 32KHZ, 2 VCC, 3 INT/SQW,
# 4 RST, 5-12 N.C. "must be connected to ground", 13 GND, 14 VBAT, 15 SDA,
# 16 SCL. Asserted by number, not through the library symbol's pin names.
wires('RTC', 'URTC', {2: 'P3V3_SW', 3: 'RTC_INT', 13: 'PGND', 14: 'RTC_VBAT',
                      15: 'RTC_SDA', 16: 'RTC_SCL',
                      **{n: 'PGND' for n in range(5, 13)}})
for _p in ('1', '4'):
    check(f'RTC pin {_p} (32KHZ / RST) is left open', unconnected(R('URTC'), _p))
check('the RTC is the DS3231SN on SOIC-16W',
      by_src['URTC']['value'] == 'DS3231SN'
      and by_src['URTC']['footprint'] == 'Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm')
wires('RTC bypass', 'C_RTC', {1: 'P3V3_SW', 2: 'PGND'})
for _src, _net, _v in (('R_SDA', 'RTC_SDA', '4.7k'), ('R_SCL', 'RTC_SCL', '4.7k'),
                       ('R_RTCINT', 'RTC_INT', '10k')):
    # pull-ups on SWITCHED 3V3 only: nothing may feed the Pico while it is off
    wires('RTC pull-up', _src, {1: 'P3V3_SW', 2: _net})
    value(_src, _v)
only('RTC_VBAT', [('BT_RTC', 1), ('URTC', 14)],
     'the cell feeds VBAT and nothing else: no charging path, no load')
check('the RTC cell is a BR2032, rated to +85 C',
      by_src['BT_RTC']['value'] == 'BR2032')

# R12-REV-4: onboard keyless RS-485 and default-open topology.
wires('spare header', 'J3', {1:'B5',2:'PGND',3:'P3V3_SW',4:'SPARE_GP13'})
wires('RS485 default listen', 'R_DE', {1:'BUS_DE',2:'PGND'})
value('R_DE','10k')
wires('keyless U5 pin map', 'U485', {1:'UART1_RX',2:'BUS_DE',3:'BUS_DE',
      4:'UART1_TX',5:'PGND',6:'RS485_A',7:'RS485_B',8:'P3V3_SW'})
wires('RS485 decoupling', 'C485', {1:'P3V3_SW',2:'PGND'})
wires('RS485 high bias', 'R485_A', {1:'RS485_BIAS_HI',2:'RS485_A'})
wires('RS485 low bias', 'R485_B', {1:'RS485_B',2:'RS485_BIAS_LO'})
wires('RS485 termination', 'R485_TERM', {1:'RS485_A',2:'RS485_TERM'})
wires('RS485 term jumper', 'JP485_TERM', {1:'RS485_TERM',2:'RS485_B'})
wires('RS485 bias HI jumper', 'JP485_HI', {1:'P3V3_SW',2:'RS485_BIAS_HI'})
wires('RS485 bias LO jumper', 'JP485_LO', {1:'RS485_BIAS_LO',2:'PGND'})
for src,v in [('R485_A','390R'),('R485_B','390R'),('R485_TERM','120R'),('C485','100nF')]:
    value(src,v)
only('UART1_TX', [('U1',11),('U485',4)])
only('UART1_RX', [('U1',12),('U485',1)])
only('BUS_DE', [('U1',14),('U485',2),('U485',3),('R_DE',1)])
for src in ('JP485_TERM','JP485_HI','JP485_LO'):
    check(src + ' header fitted without shunt',
          by_src[src]['symbol']=='Jumper:Jumper_2_Open'
          and by_src[src]['status']=='FIT_HEADER_NO_SHUNT')
# Traverse only the bias/termination passives and selected closed jumpers.
# MAX3485 is deliberately excluded: its finite input current is checked in
# the power ledger, not asserted away by this passive-path test.
def bus_reaches(start, target, closed=()):
    adj={}
    for src in ('R485_A','R485_B','R485_TERM',*closed):
        a=pin_net[(R(src),'1')]; b=pin_net[(R(src),'2')]
        adj.setdefault(a,set()).add(b);adj.setdefault(b,set()).add(a)
    seen={start};todo=[start]
    while todo:
        for n in adj.get(todo.pop(),()):
            if n not in seen:seen.add(n);todo.append(n)
    return target in seen
for start,target,jp in [('RS485_A','RS485_B','JP485_TERM'),
                         ('RS485_A','P3V3_SW','JP485_HI'),
                         ('RS485_B','PGND','JP485_LO')]:
    check(jp+' removed breaks passive path',not bus_reaches(start,target))
    check(jp+' installed restores passive path',bus_reaches(start,target,(jp,)))
# Exact footprint parity with read-only keyless source, checked at export.
for src,fp in [('U485','Package_DIP:DIP-8_W7.62mm'),
               ('C485','Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder')]:
    check(src+' matches keyless footprint',by_src[src]['footprint']==fp)
for src in ('R_DE','R485_A','R485_B','R485_TERM'):
    check(src+' matches keyless resistor footprint',by_src[src]['footprint']==
          'Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical')
for src in ('JP485_TERM','JP485_HI','JP485_LO'):
    check(src+' matches keyless JP1 footprint',by_src[src]['footprint']==
          'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical')
# ------------------------ J1, the single board connector (D-CONN-06)
J1_PINS = {1: 'RS485_A', 2: 'PGND', 3: 'B2_TAP', 4: 'B1_TAP', 5: 'B11_TAP',
           6: 'BATT_IN', 7: 'RS485_B', 9: 'C11_TAP', 10: 'AGND',
           13: 'C14_TAP', 14: 'PGND'}
J1_SPARE = (8, 11, 12)
wires('board connector', 'J1', J1_PINS)
for _p in J1_SPARE:
    check(f'J1 pin {_p} is a spare, unconnected', unconnected('J1', str(_p)))
check('J1 is the only off-board harness connector',
      not any(r['footprint'].startswith(('Connector_Molex:', 'accord-logger:JAE'))
              for r in bom if r['reference'] != 'J1'),
      'power, taps and RS-485 all come in on J1')
check('J1 is the JAE IL-AG5-14P-D3L2-A on its generated footprint',
      by_ref['J1']['footprint'] == 'accord-logger:JAE_IL-AG5-14P-D3L2-A'
      and 'IL-AG5-14P-D3L2-A' in by_ref['J1']['manufacturer_part_or_type'])
# The footprint is generated; prove the generator against the keyless 22P,
# which the same reading of the JAE drawing produced, then read J1's real pad
# positions from the committed file rather than assuming them.
sys.path.insert(0, os.path.join(HERE, 'tools'))
import gen_fp_ilag5
_strip = lambda t: [l for l in t.splitlines() if 'descr' not in l and 'tags' not in l]
_k22 = os.path.join(HERE, '..', '..', '..', 'keyless', 'hardware', 'hondaPico.pretty',
                    'JAE_IL-AG5-22P-D3L2.kicad_mod')
check('IL-AG5 generator reproduces the keyless 22P footprint exactly',
      _strip(gen_fp_ilag5.footprint(22)) == _strip(open(_k22).read()))
_fp = os.path.join(HERE, 'accord-logger.pretty', 'JAE_IL-AG5-14P-D3L2-A.kicad_mod')
check('committed 14P footprint is the generator output',
      open(_fp).read() == gen_fp_ilag5.footprint(14))
_pads = {int(n): (float(x), float(y)) for n, x, y in re.findall(
    r'\(pad "(\d+)" thru_hole \w+\s*\(at ([-\d.]+) ([-\d.]+)', open(_fp).read())}
check('J1 footprint has fourteen contacts', sorted(_pads) == list(range(1, 15)))
check('J1 footprint has two 2.2 mm board-guide holes 12.5 mm apart',
      len(re.findall(r'np_thru_hole circle\s*\(at (3.75|16.25) -14.6\)', open(_fp).read())) == 2)
# Neighbours at the mating face: same column order, rows 3.0 mm apart there
# (6.0 mm on the PCB), so map PCB y to the mating-face row offset.
def _face(n):
    x, y = _pads[n]
    return x, 0.0 if y == 0 else 3.0
def _near(a, b, r=4.0):
    (ax, ay), (bx, by) = _face(a), _face(b)
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5 <= r
_all = {**J1_PINS, **{p: 'spare' for p in J1_SPARE}}
_batt = [p for p, n in J1_PINS.items() if n == 'BATT_IN'][0]
_batt_nb = {_all[n] for n in _pads if n != _batt and _near(_batt, n)}
check('BATT_IN\'s neighbours are only grounds and 12 V-level inputs',
      _batt_nb <= {'PGND', 'B11_TAP', 'C14_TAP', 'B1_TAP'},
      f'neighbours {sorted(_batt_nb)}')
check('RS-485 A and B are adjacent contacts', _near(1, 7))
check('RS-485 has its own ground contact beside the pair',
      J1_PINS[2] == 'PGND' and _near(1, 2))
check('fuel and VSS are not adjacent to BATT_IN',
      not _near(_batt, 9) and not _near(_batt, 3))
check('fuel sits beside its AGND reference', _near(9, 10))
wires('reset header', 'J4', {1: 'RUN', 2: 'PGND'})
check('J4 has no unconnected pins left over', ('J4', '3') not in pin_net,
      'capture question Q5: a service header with NC pins was the problem')

# --------------------------------------- grounds: one ADC return, one bond
agnd = pin_net.get(('J1', '10'))
single = {
    'J1.10 cluster ground sense': ('J1', '10'),
    'U1.33 Pico AGND': ('U1', '33'),
    'fuel divider bottom': (R('R_FUEL_B'), '2'),
    'supply divider bottom': (R('R_SUP_B'), '2'),
    'fuel filter capacitor': (R('C_FUEL'), '2'),
    'supply filter capacitor': (R('C_SUP'), '2'),
    'fuel lower clamp': (R('D_FUEL_L'), '2'),
    'supply lower clamp': (R('D_SUP_L'), '2'),
}
for label, node in single.items():
    check(f'single ADC return node carries the {label}',
          pin_net.get(node) == agnd,
          f'on {pin_net.get(node)!r}, not the J1.10 node {agnd!r}')
check('the single ADC return node is the one the Pico AGND pin names',
      agnd == 'AGND', f'got {agnd!r}')
check('AGND and PGND are separate nets on the board',
      'AGND' in nets and 'PGND' in nets and nets['AGND'] != nets['PGND'],
      'they are already joined inside the Pico module, so a board-level '
      'bond would create a second path and a loop')
check('no two-terminal part bridges AGND to PGND',
      not any({pin_net.get((r['reference'], '1')),
               pin_net.get((r['reference'], '2'))} == {'AGND', 'PGND'}
              for r in bom),
      'the junction inside the module is the single point')

# ---------------------------------------- footprints: all assigned, found
for r in bom:
    check(f'{r["reference"]} ({r["source_designator"]}) has a footprint',
          r['footprint'] != '(none assigned)',
          'LRA-12 acceptance requires every populated part to carry one')
LOCAL = os.path.join(HERE, 'accord-logger.pretty')
for r in bom:
    fp = r['footprint']
    if fp.startswith('accord-logger:'):
        name = fp.split(':', 1)[1] + '.kicad_mod'
        check(f'{r["reference"]} local footprint {name} exists',
              os.path.exists(os.path.join(LOCAL, name)))

# ------------------------------- every library URI must be project-relative
for tbl in ('sym-lib-table', 'fp-lib-table'):
    body = open(os.path.join(HERE, tbl), encoding='utf-8').read()
    uris = re.findall(r'\(uri "([^"]*)"\)', body)
    check(f'{tbl} has at least one library', bool(uris))
    for uri in uris:
        check(f'{tbl} URI is KIPRJMOD-relative',
              uri.startswith('${KIPRJMOD}'), uri)

# --------------------------------- polarity of parts whose symbol hides it
# A symbol that names its pins K and A lets a reader and ERC catch a
# reversal. A symbol with pins named A1/A2, or with no pin names at all, does
# not: the orientation then exists only in the footprint and the physical
# part. Those parts are listed here with the mapping the sources require.
POLARITY = {
    'CIN': ({'1': 'VIN_SW', '2': 'PGND'},
            'electrolytic; DESIGN.md S3 "positive VIN_SW". '
            'Device:C_Polarized leaves both pins unnamed, pin 1 being +'),
    'COUT': ({'1': 'B5', '2': 'PGND'},
             'electrolytic; DESIGN.md S3 "Positive B5"'),
    'C_SD': ({'1': 'P3V3_SW', '2': 'PGND'},
             'electrolytic on the SD supply; pin 1 is +'),
    'CCLK': ({'1': 'VCLK', '2': 'PGND'},
             'tantalum on the always-on oscillator rail; pin 1 is +, and a '
             'reversed tantalum fails short'),
    'U2': ({'1': 'IGN_LED_A', '2': 'PGND', '3': 'IGN_A', '4': 'A5'},
           'PC817 pins are unnamed. AS_BUILT S3.4a fixes the pinout: pin 1 '
           'LED anode through the series resistor, pin 2 LED cathode, pin 4 '
           'collector, pin 3 emitter. LRA-12 moved the cathode to PGND and '
           'the output into the A5 domain'),
    'TVS': ({'1': 'P12', '2': 'PGND'},
            'Diode:1.5KExxA draws a cathode bar, so a reversal is visible in '
            'the drawing, but its pins are still named A1/A2 and ERC cannot '
            'check them. The 1.5KE20A is unidirectional: pin 1 is the banded '
            'cathode and goes to P12. DESIGN.md S3 records the inherited part '
            'in this position having been fitted backwards once already'),
    'BT_RTC': ({'1': 'RTC_VBAT', '2': 'PGND'},
               'Keystone 3034 holder: pad 1 is the clip on the cell rim (+), '
               'pad 2 the centre pad under it (-)'),
    'TVS_B11': ({'1': 'B11_TAP', '2': 'PGND'},
                'same symbol, same reason: pin 1 is the banded cathode and '
                'goes to the harness tap'),
    'UISO': ({'4': 'ISO_LED_A', '5': 'ISO_LED_K', '9': 'B2_ISO',
              '10': 'B2_ISO', '15': 'B2_TAP', '16': 'B2_TAP'},
             'the output pair is bidirectional so D1/D2 are interchangeable, '
             'but the LED is not: pin 4 anode, pin 5 cathode, pin 3 unused'),
}
for src, (mapping, why) in POLARITY.items():
    ref = R(src)
    for pin, net in mapping.items():
        check(f'{ref} ({src}) pin {pin} on {net}',
              pin_net.get((ref, pin)) == net,
              f'got {pin_net.get((ref, pin))!r}; {why}')
check('every part listed for polarity exists in the BOM',
      set(POLARITY) <= set(by_src), 'a listed reference is not in the BOM')

# Guard, so a part added later cannot inherit the same blind spot silently.
pinfunc = {}
for m in re.finditer(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)'
                     r'(?: \(pinfunction "([^"]*)"\))?', text):
    pinfunc.setdefault(m.group(1), set()).add(m.group(3) or '')
ORIENTATION_FREE = {
    'Device:R', 'Device:C', 'Device:L', 'Device:Fuse', 'Jumper:Jumper_2_Open',
    'Connector_Generic:Conn_01x02', 'Connector_Generic:Conn_01x04',
    'Connector_Generic:Conn_01x06', 'Connector_Generic:Conn_01x08',
}
for r in bom:
    ref, lib_id = r['reference'], r['symbol']
    names = pinfunc.get(ref, set())
    if len(names) < 2 or (names - {'', 'A1', 'A2'}):
        continue
    if lib_id in ORIENTATION_FREE:
        continue
    check(f'{ref} ({r["source_designator"]}, {lib_id}) has an asserted '
          f'orientation', r['source_designator'] in POLARITY,
          'its symbol cannot express polarity and no POLARITY entry pins it '
          'down; add one or justify it as orientation-free')

# Connections are made by labels on short stubs. If a stub landed on another
# component's pin, two named nets would merge and one name would disappear,
# so every name this design declares must still exist as its own net.
DECLARED = {
    # harness and vehicle inputs
    'B2_TAP', 'B1_TAP', 'C14_TAP', 'C11_TAP', 'B11_TAP', 'B2_ISO',
    'VSS_IN', 'TACH_IN', 'BRAKE_IN', 'FUEL_DIV', 'FUEL_ADC',
    'SUPPLY_DIV', 'SUPPLY_ADC', 'AGND',
    # B2 isolation
    'ISO_LED_A', 'ISO_LED_K', 'ISO_MID', 'ISO_EN', 'ISO_EN_G', 'ISO_PG_G',
    # ignition, vehicle side and A5 side
    'IGN_POS', 'IGN_LED_A', 'IGN_B', 'IGN_A', 'IGN_RC', 'RST_B', 'RST_C',
    'REP_G', 'QUAL_N_REPORT',
    # rails
    'BATT_IN', 'P12', 'P_AON', 'A5', 'VCLK', 'GATE', 'SINK',
    'VIN_SW', 'SW', 'BOOST', 'B5', 'VSYS', 'P3V3_SW', 'PGND',
    # HOLD and the independent cutoff
    'HOLD_RAW', 'HOLD_JH', 'HOLD_B', 'MON_B', 'HOLD_N', 'QH_C', 'ARM_G',
    'ARM', 'NARM', 'SET_N', 'RESET_N', 'QUAL_N', 'IGN_Q', 'BAD', 'PGOOD',
    'BASE_RESET', 'COUNT1_RESET', 'ARM_RESET', 'FAULT_RESET', 'EXPIRED',
    'CNT_Q13', 'CNT_Q8', 'UCLK_Q14', 'CLK32', 'XO_OUT', 'CLKOE',
    # digital interfaces
    'SD_MISO', 'SD_CS', 'SD_SCK', 'SD_MOSI', 'RUN',
    'SPARE_GP11', 'SPARE_GP12', 'SPARE_GP13',
    'UART1_TX', 'UART1_RX', 'BUS_DE',
    'RS485_A', 'RS485_B', 'RS485_BIAS_HI', 'RS485_BIAS_LO', 'RS485_TERM',
    'RTC_SDA', 'RTC_SCL', 'RTC_INT', 'RTC_VBAT',
}
for n in sorted(DECLARED):
    check(f'net {n} exists as its own net', n in nets,
          'merged away or renamed')
check('no unexpected named nets', not (NAMED - DECLARED),
      f'unexpected: {sorted(NAMED - DECLARED)}')
lone = [n for n in sorted(DECLARED) if n in nets and len(nets[n]) < 2]
check('no declared net is left with a single node', not lone,
      f'single-node nets: {lone}')

# ----------------------------------------------- deltas D7 and D13
check('D13: DOR is the 1N4004 candidate, B5 anode to VSYS cathode',
      by_src['DOR']['value'].startswith('1N4004')
      and pin_net.get((R('DOR'), '2')) == 'B5'
      and pin_net.get((R('DOR'), '1')) == 'VSYS')
check('D7: the Pico is fed from the onboard buck through DOR, not from VBUS',
      'VSYS' in nets and unconnected('U1', '40'))
check('QP switches P12 into VIN_SW',
      pin_net.get((R('QP'), '3')) == 'P12'
      and pin_net.get((R('QP'), '2')) == 'VIN_SW')
check('the selected connector is the JAE IL-AG5 family keyless already uses',
      'JAE_IL-AG5' in by_ref['J1']['footprint'])

# ------------------------------------------- D-SMD-09 package conversion
# The SOT-23 pinout differs from the TO-92 one, so assert each NPN's
# emitter/base/collector by the pin ROLE the netlist reports, not by number.
_roles = {}
for _blk in open(NET).read().split('(net (code')[1:]:
    _n = re.search(r'\(name "([^"]*)"', _blk).group(1).lstrip('/')
    for _r, _pin, _fn in re.findall(
            r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\) \(pinfunction "([^"]*)"\)', _blk):
        _roles.setdefault(_r, {})[_fn] = _n
# QI/QH are through-hole 2N3904 (owner's stock, D-THT-13); QRESET/QMON SMD.
_PKG = {'2N3904': 'Package_TO_SOT_THT:TO-92_Inline',
        'MMBT3904': 'Package_TO_SOT_SMD:SOT-23'}
for _src, (_v, _e, _b, _c) in {'QI': ('2N3904', 'PGND', 'IGN_B', 'SINK'),
                               'QH': ('2N3904', 'PGND', 'HOLD_B', 'QH_C'),
                               'QRESET': ('MMBT3904', 'PGND', 'RST_B', 'RST_C'),
                               'QMON': ('MMBT3904', 'PGND', 'MON_B', 'HOLD_N')}.items():
    _q = _roles.get(R(_src), {})
    check(f'{_src} is a {_v} on {_PKG[_v].split(":")[1]} with E/B/C on the right nets',
          by_src[_src]['value'] == _v
          and by_src[_src]['footprint'] == _PKG[_v]
          and (_q.get('E'), _q.get('B'), _q.get('C')) == (_e, _b, _c),
          f'roles {_q}')
check('no through-hole resistor remains outside the kept set',
      not any(r['footprint'].startswith('Resistor_THT')
              and r['source_designator'] not in
              {'R_DE', 'R485_A', 'R485_B', 'R485_TERM', 'RLED', 'RG',
               # D-THT-13: owner's choice for the power block
               'RGS', 'RI', 'RBI', 'RBH', 'RBIN', 'RB5'}
              for r in bom))
check('every 1N5819-class clamp is a SOD-123 1N5819HW',
      all(r['footprint'] == 'Diode_SMD:D_SOD-123' for r in bom
          if r['value'].startswith('1N5819')))
check('logic ICs are SOIC',
      all(by_src[s]['footprint'].startswith('Package_SO:SOIC')
          for s in ('UCLK', 'UCOUNT', 'ULATCH', 'UOR', 'USCH')))

# The regulator copies keyless U3 in its footprint too: StaggerOdd is the
# lead forming soldered and running in this car (owner, October 30).
_k = open(os.path.join(HERE, '..', '..', '..', 'keyless', 'hardware',
                       'hondaPico.kicad_sch'), encoding='utf-8').read()
_kfp = re.findall(r'"Footprint" "(Package_TO_SOT_THT:TO-220-7[^"]*)"', _k)
check('UREG uses the keyless LM2678 footprint',
      len(set(_kfp)) == 1 and by_src['UREG']['footprint'] == _kfp[0],
      f'logger {by_src["UREG"]["footprint"]!r}, keyless {_kfp}')

# ------------------------------------ every pin against the reference map
# The checks above assert chosen connections; this one covers ALL of them.
# validation/pinmap_reference.json records, for the last verified design,
# which pins share a net (named nets by name, unnamed ones by membership).
# Any change fails here until the reference is deliberately updated with
#   python3 check_capture.py --update-reference
import json
_REF = os.path.join(HERE, 'validation', 'pinmap_reference.json')
_groups = {}
for _blk in text.split('(net (code')[1:]:
    _n = re.search(r'\(name "([^"]*)"', _blk).group(1)
    _pins = sorted(f'{r}.{p}' for r, p in
                   re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', _blk))
    if _n.startswith('unconnected-'):
        _n = 'NC:' + _pins[0]
    elif _n.startswith('Net-('):
        _n = 'UNNAMED:' + _pins[0]
    _groups[_n] = _pins
if '--update-reference' in sys.argv:
    json.dump(_groups, open(_REF, 'w'), indent=0, sort_keys=True)
    print('reference pin map updated:', len(_groups), 'nets')
_ref = json.load(open(_REF))
_pin_of = lambda g: {p: n for n, ps in g.items() for p in ps}
_now, _was = _pin_of(_groups), _pin_of(_ref)
_moved = sorted(p for p in set(_now) | set(_was) if _now.get(p) != _was.get(p))
check('every pin is on the same net as in the verified reference',
      not _moved,
      '; '.join(f'{p}: {_was.get(p)} -> {_now.get(p)}' for p in _moved[:12]))

print(f'{checks - len(fails)}/{checks} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
