#!/usr/bin/env python3
"""Check the captured schematic against the documents it was captured from.

Reads validation/netlist.net and BOM.csv and asserts the pin map of
REV_A_INTERFACES section 1 (Rev A column), the fitted input-cell values of
AS_BUILT section 2, the deliberately unconnected pins, and the placeholder
inventory. This proves the capture agrees with the written sources; it proves
nothing about circuit behaviour.

Usage: python3 check_capture.py [project-dir]
"""
import csv
import os
import re
import sys

HERE = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
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
# net name -> {(ref, pin)}
nets = {}
for m in re.finditer(r'\(net \(code "\d+"\) \(name "([^"]*)"\)(.*?)(?=\n    \(net |\Z)',
                     text, re.S):
    name = m.group(1).lstrip('/')
    nodes = set(re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', m.group(2)))
    nets[name] = nodes
pin_net = {}
for name, nodes in nets.items():
    for ref, pin in nodes:
        pin_net[(ref, pin)] = name


def unconnected(ref, pin):
    """True when the pin carries no net.

    An explicit no-connect flag is reported by kicad-cli as a single-node
    'unconnected-(<ref>-<pin>)' net, which is what deliberate non-connection
    looks like here.
    """
    net = pin_net.get((ref, pin))
    return net is None or net.startswith('unconnected-')

comps = dict(re.findall(r'\(comp \(ref "([^"]+)"\)\s*\(value "([^"]*)"\)', text))
fps = dict(re.findall(r'\(comp \(ref "([^"]+)"\).*?\(footprint "([^"]*)"\)', text, re.S))

# ------------------------------- REV_A_INTERFACES section 1, Rev A column
# Pico module pin number -> expected net. Physical pin numbers, as the table
# gives them.
PINMAP = {
    '4': 'VSS_IN',          # GP2  VSS in
    '5': 'TACH_IN',         # GP3  Tach in
    '6': 'BRAKE_IN',        # GP4  Brake warning in
    '7': 'QUAL_N_REPORT',   # GP5  QUAL_N_REPORT
    '9': 'HOLD_RAW',        # GP6  HOLD_RAW
    '21': 'SD_MISO',        # GP16
    '22': 'SD_CS',          # GP17
    '24': 'SD_SCK',         # GP18
    '25': 'SD_MOSI',        # GP19
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

# Pins that must stay unconnected: GP0/GP1, GP7, GP8-GP10, GP28, and the
# module pins the as-built leaves alone.
FREE = {'1': 'GP0', '2': 'GP1', '10': 'GP7', '11': 'GP8', '12': 'GP9',
        '14': 'GP10', '34': 'GP28', '35': 'ADC_VREF', '37': '3V3_EN',
        '40': 'VBUS'}
for pin, label in FREE.items():
    check(f'U1 pin {pin} ({label}) unconnected', unconnected('U1', pin),
          f'on net {pin_net.get(("U1", pin))!r}')

# The seven stacked GND pins must all land on PGND, not just the one labelled.
for pin in ('3', '8', '13', '18', '23', '28', '38'):
    check(f'U1 pin {pin} GND -> PGND', pin_net.get(('U1', pin)) == 'PGND',
          f'got {pin_net.get(("U1", pin))!r}')

# ------------------------------------------- AS_BUILT section 2 input cells
# branch: (tap, top value, bottom value, bottom return, signal net)
CELLS = {
    'VSS':  ('B2_TAP',  '22k',  '33k',  'PGND', 'VSS_IN'),
    'TACH': ('B1_TAP',  '22k',  '6.8k', 'PGND', 'TACH_IN'),
    'BRK':  ('C14_TAP', '22k',  '6.8k', 'PGND', 'BRAKE_IN'),
    'FUEL': ('C11_TAP', '7.5k', '4.7k', 'AGND', 'FUEL_DIV'),
    'SUP':  ('B11_TAP', '22k',  '4.7k', 'AGND', 'SUPPLY_DIV'),
}
bom = list(csv.DictReader(open(BOM, encoding='utf-8')))
by_src = {r['source_designator']: r for r in bom}
for key, (tap, rt, rb, ret, sig) in CELLS.items():
    top, bot = by_src.get(f'R_{key}_T'), by_src.get(f'R_{key}_B')
    check(f'{key} divider top value', top and top['value'] == rt,
          f'got {top and top["value"]!r}')
    check(f'{key} divider bottom value', bot and bot['value'] == rb,
          f'got {bot and bot["value"]!r}')
    check(f'{key} divider bottom returns to {ret}',
          bot and pin_net.get((bot['reference'], '2')) == ret,
          f'got {bot and pin_net.get((bot["reference"], "2"))!r}')
    # The isolation placeholder sits upstream of the divider top: the tap
    # reaches only the placeholder, never the resistor.
    iso = by_src.get(f'XISO_{key}')
    check(f'{key} isolation placeholder present', iso is not None)
    if iso and top:
        # The tap must not reach the divider top directly. B11 additionally
        # feeds the ignition opto through FIGN, which is not a divider and is
        # isolated by the optocoupler itself.
        allowed = {iso['reference'], 'J2', by_src['FIGN']['reference']}
        check(f'{key} tap reaches no divider top directly',
              {n[0] for n in nets.get(tap, set())} <= allowed,
              f'tap {tap} also reaches '
              f'{sorted({n[0] for n in nets.get(tap, set())} - allowed)}')
        check(f'{key} divider top is downstream of isolation',
              pin_net.get((top['reference'], '1')) == pin_net.get((iso['reference'], '2')),
              'top is not fed from the placeholder output')

# Both ADC channels keep the fitted 1k + 1uF + two 1N5819.
for key, adc in (('FUEL', 'FUEL_ADC'), ('SUP', 'SUPPLY_ADC')):
    ser, cap = by_src.get(f'R_{key}_S'), by_src.get(f'C_{key}')
    check(f'{key} series resistor 1k', ser and ser['value'] == '1k')
    check(f'{key} filter capacitor 1uF', cap and cap['value'] == '1uF')
    hi, lo = by_src.get(f'D_{key}_H'), by_src.get(f'D_{key}_L')
    check(f'{key} upper clamp anode at the pin',
          hi and pin_net.get((hi['reference'], '2')) == adc
          and pin_net.get((hi['reference'], '1')) == 'P3V3_SW',
          'upper clamp orientation wrong')
    check(f'{key} lower clamp cathode at the pin',
          lo and pin_net.get((lo['reference'], '1')) == adc
          and pin_net.get((lo['reference'], '2')) == 'AGND',
          'lower clamp orientation wrong')

# Digital clamps: anode at the pin, cathode to switched 3V3.
for key, sig in (('VSS', 'VSS_IN'), ('TACH', 'TACH_IN'), ('BRK', 'BRAKE_IN')):
    d = by_src.get(f'D_{key}')
    check(f'{key} clamp anode at the pin',
          d and pin_net.get((d['reference'], '2')) == sig
          and pin_net.get((d['reference'], '1')) == 'P3V3_SW',
          'clamp orientation wrong')

# --------------------------------------- ignition cell, AS_BUILT section 3.4
ign = {s: by_src.get(s) for s in ('DI', 'RLED', 'U2', 'C_IGN', 'RIGN')}
check('ignition series diode is 1N5819',
      ign['DI'] and ign['DI']['value'] == '1N5819')
check('ignition series resistor is the measured 2.2k',
      ign['RLED'] and ign['RLED']['value'] == '2.2k')
check('ignition output capacitor is 100nF',
      ign['C_IGN'] and ign['C_IGN']['value'] == '100nF')
check('no input-side capacitor on the opto LED',
      not any(r['source_designator'].startswith('C_IGN_IN') for r in bom))
check('opto LED cathode returns to B16 as fitted',
      pin_net.get(('U2', '2')) == 'B16',
      f'got {pin_net.get(("U2", "2"))!r}')
check('opto emitter returns to PGND', pin_net.get(('U2', '3')) == 'PGND')
check('opto collector does not reach GP5 directly',
      pin_net.get(('U2', '4')) != pin_net.get(('U1', '7')),
      'the old raw-GP5 arrangement would violate D-RA-03')
check('GP5 pull-up is 10k to switched 3V3',
      ign['RIGN'] and ign['RIGN']['value'] == '10k'
      and pin_net.get((ign['RIGN']['reference'], '1')) == 'P3V3_SW')

# ------------------------------------------------- HOLD path, delta D2
hold = {s: by_src.get(s) for s in ('RPD', 'JH', 'RH')}
check('HOLD pulldown is 47k', hold['RPD'] and hold['RPD']['value'] == '47k')
check('HOLD pulldown is on GP6',
      hold['RPD'] and pin_net.get((hold['RPD']['reference'], '1')) == 'HOLD_RAW')
check('JH link is in the HOLD path',
      hold['JH'] and pin_net.get((hold['JH']['reference'], '1')) == 'HOLD_RAW')
check('MAX_ON inhibit is not inserted into the HOLD path',
      {n[0] for n in nets.get('HOLD_N', set())}
      == {by_src['XMAXON']['reference'], by_src['TP_HOLDN']['reference']},
      'HOLD_N reaches more than the placeholder and its test point')

# --------------------------------------------------------- SD, delta D6
check('SD module is on switched 3V3', pin_net.get(('J5', '1')) == 'P3V3_SW')
check('SD bulk capacitor present and on the SD supply',
      by_src.get('C_SD')
      and pin_net.get((by_src['C_SD']['reference'], '1')) == 'P3V3_SW')

# -------------------------------------------- J3 unpopulated, J4 service
for pin in ('1', '2', '3', '4', '5', '6'):
    check(f'J3 pin {pin} unconnected', unconnected('J3', pin),
          f'on net {pin_net.get(("J3", pin))!r}')
check('J4 carries the RUN-to-GND pair',
      pin_net.get(('J4', '1')) == 'RUN' and pin_net.get(('J4', '2')) == 'PGND')
for pin in ('3', '4'):
    check(f'J4 pin {pin} (UART0 service) unconnected', unconnected('J4', pin),
          f'on net {pin_net.get(("J4", pin))!r}')

# ------------------------------------------- placeholder inventory
PLACE = ['XISO_VSS', 'XISO_TACH', 'XISO_BRK', 'XISO_FUEL', 'XISO_SUP',
         'XQUAL', 'XVP', 'XMAXON']
for p in PLACE:
    r = by_src.get(p)
    check(f'placeholder {p} in the BOM', r is not None)
    if r:
        check(f'placeholder {p} has no footprint',
              r['footprint'] == '(none assigned)', f'got {r["footprint"]!r}')
        check(f'placeholder {p} is marked unselected',
              'REQUIRED_BEFORE' in r['status'], f'got {r["status"]!r}')
# D-OFFSTATE-01: five positions kept, B2's required on measured evidence and
# the other four under analog review.
iso_rows = [r for r in bom if r['value'].startswith('SIGNAL_ISOLATION')]
check('five D4 isolation positions', len(iso_rows) == 5,
      f'got {len(iso_rows)}: D4 needs one position per branch')
check('exactly one D4 position marked required',
      sum(1 for r in iso_rows if r['value'].endswith('(required)')) == 1,
      'only B2 has a measured parked-drain case')
check('the required D4 position is B2',
      by_src['XISO_VSS']['value'].endswith('(required)'),
      f'got {by_src["XISO_VSS"]["value"]!r}')
for k in ('TACH', 'BRK', 'FUEL', 'SUP'):
    check(f'D4 position {k} marked under review',
          by_src[f'XISO_{k}']['value'].endswith('(under review)'),
          f'got {by_src[f"XISO_{k}"]["value"]!r}')
check('MAX_ON placeholder present',
      any(r['value'] == 'MAX_ON' for r in bom))
check('VEHICLE_PROTECTION placeholder present',
      any(r['value'] == 'VEHICLE_PROTECTION' for r in bom))
check('TVS candidate is distinct from the VEHICLE_PROTECTION placeholder',
      by_src.get('TVS') and by_src['TVS']['footprint'] != '(none assigned)')

# ---------------------------------------- footprints assigned or explained
NO_FP_OK = set(PLACE) | {'J1', 'J2'}
for r in bom:
    if r['footprint'] == '(none assigned)':
        check(f'{r["reference"]} ({r["source_designator"]}) footprint explained',
              r['source_designator'] in NO_FP_OK,
              'no footprint and no recorded reason')

# ------------------------------- every library URI must be project-relative
for tbl in ('sym-lib-table', 'fp-lib-table'):
    body = open(os.path.join(HERE, tbl), encoding='utf-8').read()
    uris = re.findall(r'\(uri "([^"]*)"\)', body)
    check(f'{tbl} has at least one library', bool(uris))
    for uri in uris:
        check(f'{tbl} URI is KIPRJMOD-relative', uri.startswith('${KIPRJMOD}'),
              uri)

# ------------------------------------- no net was silently merged away
# Connections are made by labels on short stubs. If a stub landed on another
# component's pin, two named nets would merge and one name would disappear, so
# every name this capture declares must still exist as its own net.
DECLARED = {
    'B2_TAP', 'B1_TAP', 'C14_TAP', 'C11_TAP', 'B11_TAP', 'B16',
    'B2_ISO', 'B1_ISO', 'C14_ISO', 'C11_ISO', 'B11_ISO',
    'VSS_IN', 'TACH_IN', 'BRAKE_IN', 'FUEL_DIV', 'FUEL_ADC',
    'SUPPLY_DIV', 'SUPPLY_ADC', 'P3V3_SW', 'PGND', 'AGND',
    'IGN_FUSED', 'IGN_POS', 'IGN_LED_A', 'IGN_N', 'QUAL_N_REPORT', 'IGN_B',
    'HOLD_RAW', 'HOLD_JH', 'HOLD_B', 'HOLD_N',
    'SD_MISO', 'SD_CS', 'SD_SCK', 'SD_MOSI', 'RUN',
    'SPARE_GP11', 'SPARE_GP12',
    'BATT_IN', 'BATT_F', 'P12', 'GATE', 'SINK', 'VIN_SW', 'SW', 'BOOST',
    'B5', 'VSYS', 'A5', 'VCLK', 'PGOOD', 'ARM', 'EXPIRED',
}
for n in sorted(DECLARED):
    check(f'net {n} exists as its own net', n in nets, 'merged away or renamed')
check('no unexpected named nets',
      not (set(nets) - DECLARED - {n for n in nets if n.startswith('unconnected-')}),
      f'unexpected: {sorted(set(nets) - DECLARED - {n for n in nets if n.startswith("unconnected-")})}')

# ----------------------------------------------- deltas D7 and D13
check('D13: DOR is the 1N4004 candidate, B5 anode to VSYS cathode',
      by_src.get('DOR') and by_src['DOR']['value'].startswith('1N4004')
      and pin_net.get((by_src['DOR']['reference'], '2')) == 'B5'
      and pin_net.get((by_src['DOR']['reference'], '1')) == 'VSYS')
check('D7: the Pico is fed from the onboard buck through DOR, not from VBUS',
      'VSYS' in nets and unconnected('U1', '40'))
check('QP switches P12 into VIN_SW',
      pin_net.get((by_src['QP']['reference'], '3')) == 'P12'
      and pin_net.get((by_src['QP']['reference'], '2')) == 'VIN_SW')

print(f'{checks - len(fails)}/{checks} checks passed')
for f in fails:
    print('  FAIL', f)
sys.exit(1 if fails else 0)
