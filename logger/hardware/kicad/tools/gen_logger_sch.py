"""Generate the Rev A logger schematic and its BOM from one parts table.

LRA-06 captured the fitted circuit plus the already-decided Rev A deltas and
left eight electrical placeholders, X1-X8. LRA-12 resolves all eight and this
generator now produces the completed design, not a capture with holes. Every
part carries a footprint; nothing dashed remains.

Sources:
  REV_A_INTERFACES.md  S1 pin map, S4 grounds, S5 connectors/test points,
                       S7 deltas D1-D15, S3.4 for the D4 requirement
  AS_BUILT.md          S2 circuit matrix, S3.4/S3.4a ignition, S3.5 SD
  power/DESIGN.md      S3 component-level connection list
  power/CUTOFF_MARGIN_REVIEW.md  S1 clock block, S2 qualified IGN / reset /
                       QREPORT, S3 the always-on supply boundary
  power/MAX_ON_CUTOFF.md         latch/counter connection table, the HOLD-path
                       permission switch and the QMON sense network
  power/COMPONENT_MARGIN_CLOSURE.md and BOM_DELTA.csv   exact passive and
                       semiconductor selections
  isolation/B2_ISOLATION.md      the ASSR-601JV candidate, corrected here
  power/LAYOUT_CLOSURE.md        the LRA-12 decisions, with their calculations
  keyless/hardware/hondaPico.kicad_sch   in-service footprint conventions and
                       the connector family (D-REUSE-02, D-POWER-03)

Connections are made by placing a net label exactly on each pin, so no wire
geometry has to be solved and the netlist is checkable directly.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schgen

OUTDIR = sys.argv[1]
CUSTOM = OUTDIR + '/Custom.kicad_sym'

# ---------------------------------------------------------------- footprints
# Axial parts take the keyless board's in-service vertical mountings rather
# than the horizontal ones LRA-06 guessed. The first reason is that the same
# convention is already soldered and running in this car (D-REUSE-02). The
# second is area: fp_area.py measures the 62 axial parts at 1588 mm2 of
# courtyard vertical against 2208 mm2 horizontal, so this choice is worth
# 620 mm2, 6.5 % of an 80 x 120 board.
FP_R = 'Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical'
FP_R_HALFW = 'Resistor_THT:R_Axial_DIN0414_L11.9mm_D4.5mm_P5.08mm_Vertical'
FP_C_DISC = 'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm'
FP_C_FILM = 'Capacitor_THT:C_Rect_L7.2mm_W2.5mm_P5.00mm_FKS2_FKP2_MKS2_MKP2'
FP_C_1210 = 'Capacitor_SMD:C_1210_3225Metric_Pad1.33x2.70mm_HandSolder'
FP_CP_TANT_D = 'Capacitor_Tantalum_SMD:CP_EIA-7343-31_Kemet-D_HandSolder'
FP_DO41_A = 'Diode_THT:D_DO-41_SOD81_P5.08mm_Vertical_AnodeUp'
FP_DO41_K = 'Diode_THT:D_DO-41_SOD81_P5.08mm_Vertical_KathodeUp'
FP_DO35_K = 'Diode_THT:D_DO-35_SOD27_P2.54mm_Vertical_KathodeUp'
FP_DO35_A = 'Diode_THT:D_DO-35_SOD27_P2.54mm_Vertical_AnodeUp'
FP_DO201_K = 'Diode_THT:D_DO-201AD_P5.08mm_Vertical_KathodeUp'
FP_DO201_A = 'Diode_THT:D_DO-201AD_P5.08mm_Vertical_AnodeUp'
FP_TP = 'TestPoint:TestPoint_Loop_D2.50mm_Drill1.0mm'
FP_HDR2 = 'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical'
FP_HDR3 = 'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical'
FP_HDR6 = 'Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical'
FP_HDR8 = 'Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical'
FP_FUSE = ('Fuse:Fuseholder_Clip-5x20mm_Bel_FC-203-22_Lateral'
           '_P17.80x5.00mm_D1.17mm_Horizontal')
FP_DIP14 = 'Package_DIP:DIP-14_W7.62mm'
FP_DIP16 = 'Package_DIP:DIP-16_W7.62mm'
FP_SOT23_3 = 'Package_TO_SOT_SMD:SOT-23'
FP_SOT23_5 = 'Package_TO_SOT_SMD:SOT-23-5_HandSoldering'
FP_SOT23_6 = 'Package_TO_SOT_SMD:SOT-23-6_Handsoldering'
FP_SOT353 = 'Package_TO_SOT_SMD:SOT-353_SC-70-5_Handsoldering'
FP_TO92 = 'Package_TO_SOT_THT:TO-92_Inline'
FP_DPAK = 'Package_TO_SOT_SMD:TO-252-3_TabPin2'
FP_ASSR = ('accord-logger:ASSR-601Jx_SO-16-12Lead_11.634x10.363mm_P1.27mm')
FP_OSC = ('accord-logger:Oscillator_SMD_MicroCrystal_OV-7604-C7'
          '_SON-4_3.2x1.5mm')
FP_MFJ2 = ('Connector_Molex:Molex_Mini-Fit_Jr_5569-02A2_2x01'
           '_P4.20mm_Horizontal')
FP_MFJ8 = ('Connector_Molex:Molex_Mini-Fit_Jr_5569-08A2_2x04'
           '_P4.20mm_Horizontal')

P = []          # placed parts, in BOM order


GRID = 1.27     # KiCad's connection grid, 50 mil


def snap(v):
    """Place on the 1.27 mm connection grid.

    Every pin endpoint has to land on it, or ERC reports endpoint_off_grid
    and the pin is a connection the editor will not actually make. Snapping
    here rather than at each call site means a new block cannot reintroduce
    the fault by choosing a convenient round number.
    """
    return round(v / GRID) * GRID


def part(ref, lib_id, value, x, y, nets=None, rot=0, fp='', nc=(),
         status='', source='', note='', bom=True, mpn='', hide_value=False,
         dnp=False):
    x, y = snap(x), snap(y)
    P.append(dict(ref=ref, lib_id=lib_id, value=value, x=x, y=y, rot=rot,
                  nets=nets or {}, fp=fp, nc=tuple(nc), status=status,
                  source=source, note=note, bom=bom, mpn=mpn, dnp=dnp,
                  hide_value=hide_value))


class Grid:
    """Left-to-right, wrapping placement inside a frame.

    Connections are by net label, so placement only has to be legible. A grid
    keeps the sixty parts LRA-12 adds from needing sixty hand-tuned
    coordinates that would drift the next time a block changes.
    """

    def __init__(self, x0, y0, x1, dx=44.45, dy=20.32):
        self.x0, self.y, self.x1 = x0, y0, x1
        self.dx, self.dy, self.x = dx, dy, x0

    def next(self, dx=None, dy=None):
        step = dx or self.dx
        if self.x + step > self.x1:
            self.x = self.x0
            self.y += dy or self.dy
        xy = (self.x, self.y)
        self.x += step
        return xy

    def newline(self, dy=None):
        self.x = self.x0
        self.y += dy or self.dy


# ======================================================== vehicle input cells
# J2 is the 8-way cluster harness connector of REV_A_INTERFACES S5.1: the six
# recorded taps plus the two spare contacts that section asks for. LRA-12
# selects the Molex Mini-Fit Jr. family, which is already in service on the
# keyless board in this car (D-POWER-03 consequence 5).
part('J2', 'Connector_Generic:Conn_01x08', 'Cluster harness 8-way',
     40.64, 48.26, rot=180, fp=FP_MFJ8, nc=(7, 8),
     nets={1: 'B2_TAP', 2: 'B1_TAP', 3: 'C14_TAP', 4: 'C11_TAP',
           5: 'B11_TAP', 6: 'AGND'},
     mpn='Molex 39-30-1080 (5569-08A2), 8 circuit right-angle header',
     status='SELECTED', source='REV_A_INTERFACES S5.1 / LAYOUT_CLOSURE S6',
     note='Molex Mini-Fit Jr. 4.20 mm, 8 circuits, right-angle with PCB peg. '
          'Mates with a Mini-Fit Jr. 5557-series receptacle housing and 5556 '
          'female crimp terminals (16-24 AWG); that housing/terminal family '
          'is already in service on the keyless board in this vehicle, so '
          'crimp tooling exists. Pin numbers are Molex cavity numbers. Pins '
          '7-8 are the two spare contacts, unconnected. Pin 6 is the B16 '
          'cluster ground sense, bonded to the single AGND return node at one '
          'point (REV_A_INTERFACES S4, delta D5). Exact order code for '
          'plating/packaging is procurement, not a design gate')

# AS_BUILT S2 rows 1-5a. Ratios, clamps and the fitted ADC protection are
# carried forward with no value changed.
#
# D4, resolved by LRA-12 (LAYOUT_CLOSURE S4): B2 alone takes a series switch.
# The other four branches are a justified bypass. They are all ignition-fed,
# so "board off with the input energized" needs an upstream power fault as
# well as the key being on, and in that state the fitted series resistance
# bounds the injection. B2 is the exception the owner measured: it is held at
# 4.669 V with the key out, by an always-on source, which is why it alone
# gets the switch.

# X1 resolved: Broadcom ASSR-601JV photo-MOSFET relay in the B2 divider top
# leg. Output is a back-to-back avalanche MOSFET pair with no supply of its
# own, so LED-dark is open by construction, and the leakage maximum is stated
# over the whole -40..+105 C recommended operating range.
part('UISO', 'Custom:ASSR-601JV', 'ASSR-601JV', 109.22, 93.98, fp=FP_ASSR,
     nets={4: 'ISO_LED_A', 5: 'ISO_LED_K',
           15: 'B2_TAP', 16: 'B2_TAP', 9: 'B2_ISO', 10: 'B2_ISO'},
     mpn='Broadcom ASSR-601JV-000E', status='SELECTED_AVAILABILITY_OPEN',
     source='isolation/B2_ISOLATION.md; LAYOUT_CLOSURE S4',
     note='B2 series isolation (D4). Output leakage 1000 nA maximum at '
          'VO = 1000 V, specified over recommended operating conditions '
          '(-40 to +105 C for the JV), against 4.669 V actually applied: the '
          'row carries no 25 C override, unlike the withstand row above it. '
          'R_ON 300 ohm max at IO = 2 mA shifts the 22k/33k ratio by -0.54 %. '
          'D1 (15, 16) and D2 (9, 10) are each internally paired and the pair '
          'is bidirectional, so orientation is free. PIN 3 MUST BE LEFT '
          'UNCONNECTED - it is internally tied to pin 5, the LED cathode. '
          'Pins 11-14 do not exist; the local footprint is a 12-pad variant '
          'derived from the manufacturer land pattern, not a stock SOIC-16W. '
          'Availability is the one open item: distributor lifecycle data is '
          'contradictory. Panasonic AQY221N2S is the documented fallback, a '
          'strictly smaller part inside the same keepout, whose 10 nA leakage '
          'maximum is 25 C only')

DIG = [
    # key, label, Y, Rtop, Rbot, top-leg source net, divider node
    ('VSS',  'B2 vehicle speed', 93.98,  '22k', '33k',  'B2_ISO',  'VSS_IN'),
    ('TACH', 'B1 tachometer',   172.72,  '22k', '6.8k', 'B1_TAP',  'TACH_IN'),
    ('BRK',  'C14 brake warning', 251.46, '22k', '6.8k', 'C14_TAP', 'BRAKE_IN'),
]
BYPASS = ('D4 bypass, decided in LAYOUT_CLOSURE S4: this branch is '
          'ignition-fed and measured or logged dead with the key out, so '
          'criterion A is met with no device at all. Reaching criterion B '
          'needs the key on AND an upstream power fault, because ignition '
          'present turns QI on and powers the board. In that fault state the '
          'fitted series resistance bounds the injection. ')
for key, desc, Y, rt, rb, top, sig in DIG:
    tnote = 'fitted divider top, value unchanged'
    if key == 'VSS':
        tnote += '; fed from the ASSR output rather than directly from the tap'
    else:
        tnote += '. ' + BYPASS
    part(f'R_{key}_T', 'Device:R', rt, 162.56, Y, nets={1: top, 2: sig},
         fp=FP_R, status='VERIFY_STOCK', source='AS_BUILT S2',
         note=tnote)
    part(f'R_{key}_B', 'Device:R', rb, 203.2, Y, nets={1: sig, 2: 'PGND'},
         fp=FP_R, status='VERIFY_STOCK', source='AS_BUILT S2',
         note='fitted divider bottom, value unchanged')
    dnote = 'fitted clamp, anode at the pin, cathode to switched 3V3'
    if key == 'VSS':
        dnote += ('. This is the specimen behind U-07\'s first measured '
                  'point: the parked B2 readings give it 159 mV at 109 uA at '
                  'room temperature, a Schottky drop. With UISO fitted the '
                  'branch is open upstream when the board is off, so this '
                  'clamp no longer has a parked path to conduct')
    else:
        dnote += ('. D11 remains open for the tach cell: V_F keeps falling '
                  'below 109 uA, so its clamp onset is lower than a 0.3 V '
                  'assumption gives. LRA-12 changes no ratio')
    part(f'D_{key}', 'Diode:1N5819', '1N5819', 248.92, Y, rot=180,
         nets={2: sig, 1: 'P3V3_SW'}, fp=FP_DO41_A, mpn='Chanzon 1N5819',
         status='VERIFY_STOCK', source='AS_BUILT S2/S3.4a, U-07',
         note=dnote)

ADC = [
    ('FUEL', 'C11 fuel sender', 330.2, '7.5k', '4.7k', 'C11_TAP',
     'FUEL_DIV', 'FUEL_ADC'),
    ('SUP', 'B11 cluster supply', 408.94, '22k', '4.7k', 'B11_TAP',
     'SUPPLY_DIV', 'SUPPLY_ADC'),
]
for key, desc, Y, rt, rb, top, div, adc in ADC:
    part(f'R_{key}_T', 'Device:R', rt, 162.56, Y, nets={1: top, 2: div},
         fp=FP_R, status='VERIFY_STOCK', source='AS_BUILT S2',
         note='fitted divider top, value unchanged. ' + BYPASS +
              'No series element is added, so the card header\'s two-term '
              'fuel calibration (log.adc.fuel div=7500/4700) stays valid and '
              'REV_A_INTERFACES S8.2 needs no change')
    part(f'R_{key}_B', 'Device:R', rb, 203.2, Y, nets={1: div, 2: 'AGND'},
         fp=FP_R, status='VERIFY_STOCK', source='AS_BUILT S2/S3.3',
         note='fitted divider bottom; returns to the single B16 sense node')
    part(f'R_{key}_S', 'Device:R', '1k', 287.02, Y, rot=90,
         nets={1: div, 2: adc}, fp=FP_R, status='VERIFY_STOCK',
         source='AS_BUILT S2 rows 4a/5a',
         note='fitted series resistor at the pin')
    part(f'C_{key}', 'Device:C', '1uF', 312.42, Y, nets={1: adc, 2: 'AGND'},
         fp=FP_C_DISC, status='VERIFY_OR_SOURCE',
         source='AS_BUILT S2 rows 4a/5a',
         note='fitted filter capacitor; exact dielectric/rating not recorded')
    part(f'D_{key}_H', 'Diode:1N5819', '1N5819', 337.82, Y - 10.16, rot=180,
         nets={2: adc, 1: 'P3V3_SW'}, fp=FP_DO41_A, mpn='Chanzon 1N5819',
         status='VERIFY_STOCK', source='AS_BUILT S2 rows 4a/5a',
         note='fitted upper clamp')
    part(f'D_{key}_L', 'Diode:1N5819', '1N5819', 337.82, Y + 10.16,
         nets={1: adc, 2: 'AGND'}, fp=FP_DO41_A, mpn='Chanzon 1N5819',
         status='VERIFY_STOCK', source='AS_BUILT S2 rows 4a/5a',
         note='fitted lower clamp')

# The one harness entry that is not a high-impedance divider: B11 feeds the
# ignition opto LED through 2.2k as well as the supply ADC divider, so it is
# the one cluster line that gets a clamp. The five divider inputs are
# protected by their own 7.5k-22k series resistance (LAYOUT_CLOSURE S3).
part('TVS_B11', 'Diode:1.5KExxA', '1.5KE20A-E3/54', 109.22, 440,
     rot=270, nets={1: 'B11_TAP', 2: 'PGND'}, fp=FP_DO201_K,
     mpn='Vishay 1.5KE20A-E3/54', status='SELECTED',
     source='LAYOUT_CLOSURE S3; D-POWER-03 consequence 2',
     note='ignition/supply-sense entry clamp. Same part as the P12 clamp, so '
          'one qualification covers both: 17.1 V standoff, 19.0-21.0 V VBR at '
          '1 mA, 27.7 V clamp at 54.2 A for 10/1000 us, 1.0 uA maximum '
          'leakage at standoff. POLARITY: Diode:1.5KExxA is the '
          'unidirectional family and draws a real cathode bar, so a reversal '
          'is visible in the drawing - but its pins are still named A1/A2, so '
          'ERC cannot check it and check_capture.py asserts it by pin number '
          'instead. Pin 1 is the banded cathode and goes to the tap. '
          'Keyless protects its harness lines with seven '
          'P6KE30A; the owner has four. They are not used here because their '
          '41.4 V clamp is above the 40 V parts this board puts behind it')

# ================================================================= Pico W
PICO_NC = (1, 2, 19, 20, 26, 27, 29, 34, 35, 37, 40)
part('U1', 'MCU_Module:RaspberryPi_Pico_W', 'RaspberryPi_Pico_W',
     431.8, 101.6, fp='Module:RaspberryPi_Pico_W_SMD_HandSolder',
     nc=PICO_NC, mpn='Raspberry Pi Pico W (RP2040 + CYW43439)',
     status='FITTED', source='REV_A_INTERFACES S1',
     note='fitted module; Rev A column of the pin map. GP7 (pin 10) is the '
          'ISO_EN reservation LRA-12 takes up, confirmed free in S1. GP8/GP9 '
          '(UART1) and GP10 (DE//RE) go to the DNP expansion header, and GP13 '
          'is offered there as a spare; those are offers, not reservations',
     nets={4: 'VSS_IN', 5: 'TACH_IN', 6: 'BRAKE_IN', 7: 'QUAL_N_REPORT',
           9: 'HOLD_RAW', 10: 'ISO_EN', 11: 'UART1_TX', 12: 'UART1_RX',
           14: 'BUS_DE', 15: 'SPARE_GP11', 16: 'SPARE_GP12',
           17: 'SPARE_GP13',
           21: 'SD_MISO', 22: 'SD_CS', 24: 'SD_SCK', 25: 'SD_MOSI',
           30: 'RUN', 31: 'FUEL_ADC', 32: 'SUPPLY_ADC', 33: 'AGND',
           36: 'P3V3_SW', 39: 'VSYS', 3: 'PGND'})

# ====================================================== ignition / opto cell
# AS_BUILT S3.4 / S3.4a for the vehicle side. LRA-12 decisions (R06-REV-2 and
# capture question Q2): the LED cathode returns to PGND, not to the B16
# cluster conductor, and the onboard FIGN is dropped in favour of the tap-end
# fuse the specification asks for.
part('DI', 'Diode:1N5819', '1N5819', 60.96, 490.22, rot=180,
     nets={2: 'B11_TAP', 1: 'IGN_POS'}, fp=FP_DO41_A, mpn='Chanzon 1N5819',
     status='VERIFY_STOCK', source='AS_BUILT S2 row 6 / S3.4',
     note='fitted series diode; owner reported 1N5819, not the 1N4148 of '
          'DESIGN.md S3. The onboard FIGN of DESIGN.md S3 is deliberately '
          'not fitted: REV_A_INTERFACES S5.1 and delta D10 put per-branch '
          'fuses at the tap end, an onboard fuse cannot protect the upstream '
          'harness, and the board cannot draw enough through RI and RLED '
          '(1.1k together) to need one. Capture question Q4, closed')
part('RLED', 'Device:R', '2.2k', 99.06, 490.22, rot=90,
     nets={1: 'IGN_POS', 2: 'IGN_LED_A'}, fp=FP_R_HALFW,
     status='VERIFY_STOCK', source='AS_BUILT S3.4a, measured 2026-10-29',
     note='measured 2.2k carried forward (D15), specified 0.5 W. At the '
          '17.1 V sustained ceiling the standoff of the entry clamp sets, '
          'dissipation is 0.108 W; the 0.792 W figure that broke the 1k '
          'candidate came from the superseded 28 V number. Fitted wattage is '
          'not recorded, so the 0.5 W position is specified rather than '
          'assumed')
part('DR', 'Diode:1N4148', '1N4148', 139.7, 500.38, rot=270,
     nets={1: 'IGN_LED_A', 2: 'PGND'}, fp=FP_DO35_A,
     mpn='Vishay 1N4148-TAP', status='MISSING', source='DESIGN.md S3',
     note='LED reverse clamp. With the LED cathode now on PGND this sits '
          'directly antiparallel with the LED, which is the arrangement '
          'DESIGN.md S3 specifies and the position that actually limits LED '
          'reverse voltage (BVR 6 V on the PC817 input)')
part('U2', 'Isolator:PC817', 'PC817', 190.5, 490.22,
     nets={1: 'IGN_LED_A', 2: 'PGND', 4: 'A5', 3: 'IGN_A'},
     fp='Package_DIP:DIP-4_W7.62mm',
     mpn='Sharp PC817XNNSZ1B or qualified equivalent',
     status='VERIFY_STOCK', source='AS_BUILT S2 rows 6-7 / S3.4; '
                                   'CUTOFF_MARGIN_REVIEW S2',
     note='Rewired by LRA-12 into the A5 domain, which is what X6 was holding '
          'open: collector (4) to A5 and emitter (3) to IGN_A, an emitter '
          'follower into the 47k/220k/1uF qualification filter, replacing the '
          'old collector-to-GP5 arrangement that D-RA-03 forbids mixing with '
          'the qualified proposal. LED CATHODE MOVED FROM B16 TO PGND '
          '(R06-REV-2 / Q2): REV_A_INTERFACES S4 makes B16 a reference that '
          'must never become a power return, and the fitted cell put '
          '4.7-5.8 mA of signal-dependent LED current through the node both '
          'ADC channels reference. No symbol encodes this pinout, so it is '
          'asserted by pin number in check_capture.py: 1 LED anode, 2 LED '
          'cathode, 3 emitter, 4 collector (AS_BUILT S3.4a). The fitted '
          '100 nF across the old collector output is not carried forward - '
          'the node it filtered no longer exists')

# ====================================== X6: qualified ignition, A5 domain
# CUTOFF_MARGIN_REVIEW.md S2, component for component.
g = Grid(40.64, 600.0, 300.0)
x, y = g.next()
part('RIGNA', 'Device:R', '47k', x, y, nets={1: 'IGN_A', 2: 'PGND'},
     fp=FP_R, status='VERIFY_OR_SOURCE', source='CUTOFF_MARGIN_REVIEW S2',
     note='1 % tolerance. Sets the opto emitter load: the ON endpoint must '
          'reach 4.5 V, which draws 95.7 uA, and the OFF endpoint must stay '
          'below 0.3 V, which allows only 6.32 uA of injected leakage into '
          'this node')
x, y = g.next()
part('RRC', 'Device:R', '220k', x, y, nets={1: 'IGN_A', 2: 'IGN_RC'},
     fp=FP_R, status='VERIFY_OR_SOURCE', source='CUTOFF_MARGIN_REVIEW S2',
     note='1 % tolerance; charge leg of the qualification filter')
x, y = g.next()
part('CQUAL', 'Device:C', '1uF', x, y, nets={1: 'IGN_RC', 2: 'PGND'},
     fp=FP_C_FILM, status='PART_SELECTION_OPEN',
     source='CUTOFF_MARGIN_REVIEW S2',
     note='1 uF film, 5 %, >=50 V. Film rather than ceramic because the '
          'filter endpoints depend on its actual capacitance and leakage: a '
          'Class 2 ceramic would move the qualification times with bias and '
          'temperature. An empty capacitor now means IGN OFF, which is the '
          'polarity correction CUTOFF_MARGIN_REVIEW made. Exact series and '
          'insulation resistance remain a procurement item')
x, y = g.next()
part('QRESET', 'Transistor_BJT:2N3904', '2N3904', x, y,
     nets={1: 'PGND', 2: 'RST_B', 3: 'RST_C'}, fp=FP_TO92,
     mpn='onsemi 2N3904', status='VERIFY_STOCK',
     source='CUTOFF_MARGIN_REVIEW S2',
     note='discharges IGN_RC toward OFF while the supervisor says BAD, so a '
          'previously charged filter cannot grant a false rearm on recovery. '
          'Worst RC fall from 5.11 V to 0.9 V is about 10.3 ms against the '
          'supervisor 120 ms minimum release delay. E/B/C = 1/2/3')
x, y = g.next()
part('R_RSTB', 'Device:R', '22k', x, y, nets={1: 'BAD', 2: 'RST_B'},
     fp=FP_R, status='VERIFY_STOCK', source='CUTOFF_MARGIN_REVIEW S2',
     note='1 %; QRESET base drive, about 0.16 mA from a 4.5 V BAD output')
x, y = g.next()
part('R_RSTPD', 'Device:R', '100k', x, y, nets={1: 'RST_B', 2: 'PGND'},
     fp=FP_R, status='VERIFY_STOCK', source='CUTOFF_MARGIN_REVIEW S2',
     note='QRESET base-emitter pulldown')
x, y = g.next()
part('R_RSTC', 'Device:R', '4.7k', x, y, nets={1: 'RST_C', 2: 'IGN_RC'},
     fp=FP_R, status='VERIFY_STOCK', source='CUTOFF_MARGIN_REVIEW S2',
     note='1 %; discharge leg. Initial collector demand about 1.1 mA')
x, y = g.next()
part('QREPORT', 'Transistor_FET:BSS138', 'BSS138P', x, y,
     nets={1: 'REP_G', 2: 'PGND', 3: 'QUAL_N_REPORT'}, fp=FP_SOT23_3,
     mpn='Nexperia BSS138P', status='VERIFY_STOCK',
     source='CUTOFF_MARGIN_REVIEW S2 / REV_A_INTERFACES D1',
     note='translates IGN_Q to the switched 3V3 domain: GP5 LOW means '
          'IGN_Q = 1. Open drain against RIGN, so there is no DC A5 path '
          'into GP5 and no 5 V pullup on any GPIO. gate 1, source 2, '
          'drain 3. The report node carries no capacitor (see D1): with the '
          '10k pullup and about 30 pF of node capacitance the rising edge is '
          'under a microsecond, well inside the 10 ms observation budget')
x, y = g.next()
part('R_REPG', 'Device:R', '1k', x, y, nets={1: 'IGN_Q', 2: 'REP_G'},
     fp=FP_R, status='VERIFY_STOCK', source='CUTOFF_MARGIN_REVIEW S2',
     note='QREPORT gate series resistor')
x, y = g.next()
part('R_REPPD', 'Device:R', '100k', x, y, nets={1: 'REP_G', 2: 'PGND'},
     fp=FP_R, status='VERIFY_STOCK', source='CUTOFF_MARGIN_REVIEW S2',
     note='QREPORT gate pulldown; holds the report off with A5 absent')
x, y = g.next()
part('RIGN', 'Device:R', '10k', x, y,
     nets={1: 'P3V3_SW', 2: 'QUAL_N_REPORT'}, fp=FP_R,
     status='VERIFY_STOCK', source='REV_A_INTERFACES S1 / DESIGN.md S3',
     note='GP5 report-node pull-up to SWITCHED 3V3 (D1). With A5 absent and '
          'the board on USB only, QREPORT is off and GP5 reads HIGH, which '
          'firmware must treat as ignition OFF')

# ============================== X7 second stage: always-on A5 supply boundary
# CUTOFF_MARGIN_REVIEW.md S3 selects the regulator. LRA-12 adds the series
# resistor and clamp that make the "P_AON <= 28 V" contract true at
# temperature rather than only at 25 C: see LAYOUT_CLOSURE S3.
g = Grid(320.0, 600.0, 575.0)
x, y = g.next()
part('R_AON', 'Device:R', '330R', x, y, nets={1: 'P12', 2: 'P_AON'},
     fp=FP_R, status='SELECTED', source='LAYOUT_CLOSURE S3',
     note='second-stage series element for the A5 regulator. At the 0.5 mA '
          'worst A5 load the drop is 0.165 V, so a 6.0 V P12 still presents '
          '5.835 V, above the 5.5 V floor the 500 mV/50 mA dropout maximum '
          'implies for a 5 V output. Chosen large enough that DZ_AON stays '
          'inside 0.5 W: at the 29.19 V hot clamp the zener takes 17.8 mA, '
          '0.42 W. Own dissipation 0.105 W against a 0.25 W part')
x, y = g.next()
part('DZ_AON', 'Device:D_Zener', 'BZX55C22', x, y, rot=270,
     nets={1: 'P_AON', 2: 'PGND'}, fp=FP_DO35_K,
     mpn='Vishay BZX55C22-TAP', status='SELECTED',
     source='LAYOUT_CLOSURE S3',
     note='holds the A5 regulator input inside its envelope independently of '
          'what the entry clamp lets through. VZ 20.8-23.3 V at 5 mA; with '
          'the 0.12 %/K maximum coefficient the 85 C worst is 24.98 V, plus '
          '0.41 V of dynamic drop at 12.5 mA through the 55 ohm maximum, so '
          'P_AON <= 25.4 V: 2.6 V inside the contract 28 V and 4.6 V inside '
          'TPS709 30 V. Minimum VZ at -40 C is 19.18 V, above the 17.1 V '
          'sustained ceiling, so it never conducts in normal operation. '
          'Leakage is a specified maximum with a hot point: 0.1 uA at 25 C '
          'and 2 uA at 150 C, at VR = 18 V. Polarity: pin 1 is the cathode')
x, y = g.next()
part('C_AON', 'Device:C', '4.7uF/50V', x, y, nets={1: 'P_AON', 2: 'PGND'},
     fp=FP_C_1210, mpn='Murata GRM32ER71H475KA88L', status='CONDITIONAL',
     source='COMPONENT_MARGIN_CLOSURE S1 / BOM_DELTA.csv',
     note='A5 input capacitance; effective C must stay >=1 uF across the '
          'P_AON range. X7R 1210 50 V; DC-bias and aging data still required '
          'for procurement. With R_AON the input time constant is 1.55 ms, '
          'inside the 100 ms A5 validity budget')
x, y = g.next(dx=76.2)
part('UA5', 'Custom:TPS70950-Q1_DBV', 'TPS70950QDBVRQ1', x, y,
     nets={1: 'P_AON', 2: 'PGND', 5: 'A5'}, nc=(3,), fp=FP_SOT23_5,
     mpn='TI TPS70950QDBVRQ1', status='RETAIN_UNRESOLVED',
     source='CUTOFF_MARGIN_REVIEW S3 / COMPONENT_MARGIN_CLOSURE S2',
     note='the always-on 5 V rail. DBV pinout IN 1, GND 2, EN 3, NC 4, '
          'OUT 5 (SLVSCE6D Table 4-1). EN is left OPEN to enable; its '
          'absolute maximum is 7 V, so it must never be tied to an '
          'unregulated rail. Blocks OUT-to-IN current when OUT exceeds IN, '
          'which is why this part and not the TPS7A16. Unresolved: ground '
          'current is specified as 2.7 uA maximum at zero load and 10 uA at '
          '100 uA load / 30 V, with nothing in between, and load regulation '
          'starts at 100 uA - the parked operating point is below both. No '
          'permanent preload may be added to buy a specification')
x, y = g.next(dx=76.2)
part('USUP', 'Power_Supervisor:TPS3839DBZ', 'TPS3839K50DBZR', x, y,
     nets={1: 'PGND', 2: 'PGOOD', 3: 'A5'}, fp=FP_SOT23_3,
     mpn='TI TPS3839K50DBZR', status='SELECTED',
     source='CUTOFF_MARGIN_REVIEW S2',
     note='A5 supervisor. Active-low RESET on pin 2 is PGOOD here: HIGH '
          'means the rail is good. Falling threshold 4.271-4.446 V, release '
          '120-350 ms after a valid rail, 44 mV hysteresis. PUSH-PULL output, '
          'so it drives the new ISO permission gate directly: VOH is at least '
          'VDD-0.4 V at 2 mA against the 50 uA that gate divider draws. '
          'Falling propagation delay is 20 us typical with no maximum, so an '
          'arbitrarily fast collapse is not covered by a worst-case bound. '
          'Specified only to +85 C, which is exactly the hot screening point')
for ref, net in (('C_A5A', 'A5'), ('C_A5B', 'A5')):
    x, y = g.next()
    part(ref, 'Device:C', '4.7uF/50V', x, y, nets={1: net, 2: 'PGND'},
         fp=FP_C_1210, mpn='Murata GRM32ER71H475KA88L', status='CONDITIONAL',
         source='COMPONENT_MARGIN_CLOSURE S1 / BOM_DELTA.csv',
         note='A5 output capacitance, two in parallel: 9.4 uF nominal, '
              'effective sum must stay >=2.2 uF at 5.11 V, inside the '
              'regulator 2-47 uF window. Parallel parts do not average '
              'worst-case tolerance')
x, y = g.next()
# C_SUP is already the B11 ADC filter capacitor, so the supervisor bypass is
# C_USUP. A duplicate source designator would collide in the BOM and in every
# check that looks a part up by it; check_capture.py now asserts there is none.
part('C_USUP', 'Device:C', '100nF', x, y, nets={1: 'A5', 2: 'PGND'},
     fp=FP_C_DISC, status='VERIFY_OR_SOURCE',
     source='CUTOFF_MARGIN_REVIEW S2',
     note='supervisor local bypass, across its own supply')

# ===================================================== B2 isolation driver
# The enable path LRA-11 proposed, completed as the manager required: a GPIO
# enable in series with a hardware PGOOD permission, so BAD opens the switch
# with no software step even when QI is holding the board powered.
g = Grid(600.0, 600.0, 828.0)
x, y = g.next()
part('R_ISO', 'Device:R', '270R', x, y, nets={1: 'B5', 2: 'ISO_LED_A'},
     fp=FP_R, status='SELECTED', source='LAYOUT_CLOSURE S4',
     note='1 %. Sized so the WORST-CASE LED current is still at or above the '
          '10 mA the 4.0 ms turn-on maximum is specified at: B5 -5 % with '
          'V_F 1.85 V and both switch channels gives 10.19 mA, nominal '
          '12.41 mA, B5 +5 % with V_F 1.25 V gives 14.66 mA, inside the 7-30 '
          'mA recommended window. The 330 ohm of the original return put the '
          'low corner at 8.64 mA, below the specified point, which would have '
          'left turn-on unspecified. Dissipation 58 mW')
x, y = g.next()
part('QISO_PG', 'Transistor_FET:BSS138', 'BSS138P', x, y,
     nets={1: 'ISO_PG_G', 2: 'ISO_MID', 3: 'ISO_LED_K'}, fp=FP_SOT23_3,
     mpn='Nexperia BSS138P', status='SELECTED',
     source='LAYOUT_CLOSURE S4; LAYOUT_READINESS_2026-10-29',
     note='hardware permission in series with the GPIO enable. Gated from '
          'A5-domain PGOOD, so supervisor BAD opens the B2 branch with no '
          'software step. This is the part the manager required: BAD does NOT '
          'necessarily remove B5, because the original design gates only QH '
          'and QI can hold power with ignition present, so the LED rail alone '
          'cannot carry the fail-open requirement')
x, y = g.next()
part('QISO_EN', 'Transistor_FET:BSS138', 'BSS138P', x, y,
     nets={1: 'ISO_EN_G', 2: 'PGND', 3: 'ISO_MID'}, fp=FP_SOT23_3,
     mpn='Nexperia BSS138P', status='SELECTED', source='LAYOUT_CLOSURE S4',
     note='firmware enable, gated from GP7. Source to PGND so its gate '
          'reference is fixed. Both channels must be on for LED current to '
          'flow; either one off leaves the relay open')
for ref, src, net, nt in (
        ('R_ISOEN', 'ISO_EN', 'ISO_EN_G', 'GP7 gate series resistor'),
        ('R_ISOEN_PD', 'ISO_EN_G', 'PGND',
         'gate pulldown. This is the startup and reset default: GP7 floats '
         'out of reset, so the relay is open before firmware runs, and it '
         'stays open with the Pico unpowered while B5 is present'),
        ('R_ISOPG', 'PGOOD', 'ISO_PG_G', 'PGOOD gate series resistor'),
        ('R_ISOPG_PD', 'ISO_PG_G', 'PGND',
         'gate pulldown; holds the permission gate off with A5 absent')):
    x, y = g.next()
    part(ref, 'Device:R', '1k' if ref.endswith(('ISOEN', 'ISOPG')) else '100k',
         x, y, nets={1: src, 2: net}, fp=FP_R, status='VERIFY_STOCK',
         source='LAYOUT_CLOSURE S4', note=nt)

# ======================================================== HOLD driver (D2)
part('RPD', 'Device:R', '47k', 396.24, 251.46,
     nets={1: 'HOLD_RAW', 2: 'PGND'}, fp=FP_R, status='VERIFY_STOCK',
     source='REV_A_INTERFACES D2 / DESIGN.md S3',
     note='external GP6 pulldown; holds the driver off before output enable')
part('JH', 'Jumper:Jumper_2_Open', 'HOLD link', 441.96, 238.76,
     nets={1: 'HOLD_RAW', 2: 'HOLD_JH'}, fp=FP_HDR2,
     status='VERIFY_OR_SOURCE', source='DESIGN.md S3 / REV_A_INTERFACES S5.3',
     note='MAINTENANCE link, not a test provision: open it for USB work so a '
          'USB-driven HOLD cannot keep the battery circuit on. Opening it '
          'does not inhibit QI and does not change the QMON sense, which '
          'taps HOLD_RAW ahead of this link. Distinct from the two 0 R '
          'period-select links R_EXPP and R_EXPT, which choose the cutoff '
          'period: three different provisions, three different parts')
part('RH', 'Device:R', '1k', 482.6, 238.76, rot=90,
     nets={1: 'HOLD_JH', 2: 'HOLD_B'}, fp=FP_R, status='VERIFY_STOCK',
     source='DESIGN.md S3', note='HOLD base drive')

# ============================================================ SD (D6, S3.5)
part('J5', 'Connector_Generic:Conn_01x06', 'SD breakout 6-way',
     403.86, 381, rot=180, fp=FP_HDR6,
     nets={1: 'P3V3_SW', 2: 'PGND', 3: 'SD_MISO', 4: 'SD_CS', 5: 'SD_SCK',
           6: 'SD_MOSI'},
     status='VERIFY_OR_SOURCE', source='AS_BUILT S2 row 9 / S3.5',
     note='fitted SPI0 breakout module on switched 3V3, 12 MHz; the card must '
          'be removable without removing the board (S5.2)')
part('C_SD', 'Device:C_Polarized', '47uF/16V', 474.98, 381,
     nets={1: 'P3V3_SW', 2: 'PGND'}, fp='Capacitor_THT:CP_Radial_D6.3mm_P2.50mm',
     status='SELECTED', source='REV_A_INTERFACES D6 / LAYOUT_CLOSURE S6',
     note='D6 bulk at the SD supply, confirmed absent 2026-10-29. D6 gave a '
          '10-100 uF range; 47 uF is selected from the duty it has to do - a '
          '200 mA write spike for 1 ms inside a 100 mV droop needs 2 uF, so '
          '47 uF is an order of margin without an oversized can. '
          'Specification for an interchangeable part: 47 uF +/-20 %, >=16 V, '
          'ESR <=0.5 ohm at 100 kHz, 6.3 x 11 mm maximum, 105 C. POLARITY: '
          'pin 1 is the + terminal and goes to the switched 3V3 rail')

# ==================================== expansion and service (LRA-04 bounded)
part('J3', 'Connector_Generic:Conn_01x08', 'Expansion 8-way (DNP bus)',
     403.86, 480, rot=180, fp=FP_HDR8,
     nets={1: 'B5', 2: 'PGND', 3: 'P3V3_SW', 4: 'UART1_TX', 5: 'UART1_RX',
           6: 'BUS_DE', 7: 'SPARE_GP13', 8: 'PGND'},
     status='SELECTED', source='LRA04_REVIEW_2026-10-29 / '
                               'communications/REV_A_PROVISION.md',
     note='the bounded Rev A communications provision: a passive expansion '
          'header for a DNP daughterboard, with NO transceiver, bias or '
          'termination on this board. That is why no off-state claim is '
          'needed - an unpopulated header has no quiescent current and no bus '
          'pins. Pinout 1 B5, 2 GND, 3 switched 3V3, 4 UART1 TX (GP8), '
          '5 UART1 RX (GP9), 6 DE//RE (GP10), 7 spare GP13, 8 GND. The tied '
          'DE//RE line follows the keyless arrangement that was physically '
          'exercised; LRA-04 finding R04-REV-1 is resolved by dropping every '
          'claim that depended on an unreachable shutdown state, not by '
          'spending a second GPIO. A daughterboard may take power only from '
          'pins 1 or 3, both switched: connecting an externally powered '
          'adapter here breaks the off-state contract')
part('R_DE', 'Device:R', '10k', 474.98, 492.76,
     nets={1: 'BUS_DE', 2: 'PGND'}, fp=FP_R, status='VERIFY_STOCK',
     source='communications/REV_A_PROVISION.md',
     note='DE//RE default-listen pulldown, following keyless practice, so the '
          'line is defined while the GPIO still floats at boot. A pulldown '
          'and not a pullup, so nothing feeds an off GPIO')
part('J4', 'Connector_Generic:Conn_01x02', 'Reset RUN-GND',
     403.86, 541.02, rot=180, fp=FP_HDR2, nets={1: 'RUN', 2: 'PGND'},
     status='SELECTED', source='REV_A_INTERFACES S5.1 / LAYOUT_CLOSURE S6',
     note='resolves capture question Q5. J4 is now only the RUN-to-GND reset '
          'pair, shorted with a link for a reset without cutting power, '
          'following the keyless J7 pattern. The service UART that S5.1 also '
          'wanted here is dropped: GP0/GP1 must stay free, firmware already '
          'builds with pico_enable_stdio_usb so the USB CDC console is the '
          'service path, and a UART header would be another externally '
          'powered pullup aimed at an off GPIO. A header with NC pins was '
          'the contradiction; this has none')

# ============================================== onboard power (DESIGN.md S3)
part('J1', 'Connector_Generic:Conn_01x02', 'Power 2-way',
     546.1, 48.26, rot=180, fp=FP_MFJ2, nets={1: 'BATT_IN', 2: 'PGND'},
     mpn='Molex 39-30-1020 (5569-02A2), 2 circuit right-angle header',
     status='SELECTED', source='REV_A_INTERFACES S5.1 / LAYOUT_CLOSURE S6',
     note='protected +12 V from the auxiliary battery and its return. Molex '
          'Mini-Fit Jr. 4.20 mm, 2 circuits, right-angle with PCB peg; same '
          'family as J2 and as the keyless body harness already in service. '
          '9 A per circuit against a 1 A branch, so the margin is in the '
          'crimp rather than the contact. Mates with a 5557-series receptacle '
          'housing and 5556 crimp terminals')
part('F1', 'Device:Fuse', '1A', 584.2, 48.26, rot=90,
     nets={1: 'BATT_IN', 2: 'BATT_F'}, fp=FP_FUSE,
     status='PART_SELECTION_OPEN', source='DESIGN.md S3 / LAYOUT_CLOSURE S3',
     note='board branch fuse. It protects the board against its own faults; '
          'it does NOT protect the harness, which needs a fuse at the feed '
          'source (DESIGN.md S5). It is also the element that has to clear a '
          'sustained overvoltage before the entry clamp fails, and a 1 A '
          'cartridge carrying its own rating at 22 V will not clear quickly - '
          'see the declared sustained-overvoltage limit in LAYOUT_CLOSURE S3. '
          'Exact family, DC interrupt rating and time-current curve stay open '
          'pending the owner exposure inputs')
part('DREV', 'Device:D_Schottky', 'SB360-E3/54', 622.3, 48.26, rot=180,
     nets={2: 'BATT_F', 1: 'P12'}, fp=FP_DO201_A, mpn='Vishay SB360-E3/54',
     status='MISSING_OR_VERIFY_SPARE', source='DESIGN.md S3',
     note='input reverse-blocking diode. It is what makes P12 nonnegative at '
          'the A5 regulator, which that regulator requires, and it keeps the '
          'unidirectional entry clamp out of forward conduction on a reverse '
          'connection. No part borrowed from the live keyless board')
part('TVS', 'Diode:1.5KExxA', '1.5KE20A-E3/54', 660.4, 68.58, rot=270,
     nets={1: 'P12', 2: 'PGND'}, fp=FP_DO201_K,
     mpn='Vishay 1.5KE20A-E3/54', status='SELECTED',
     source='LAYOUT_CLOSURE S3; COMPONENT_MARGIN_CLOSURE S5',
     note='entry clamp, X7 resolved. REPLACES the inherited 1.5KE30A, and '
          'that is a deliberate deviation from the in-service keyless part: '
          'the 41.4 V clamp is above the 40 V absolute ratings of everything '
          'this board puts behind it - QI/QH VCEO, the LM2678 operating '
          'ceiling and the selected QP VDS - and keyless has neither those '
          'drivers nor a 30 V always-on LDO. 17.1 V standoff, 19.0-21.0 V VBR '
          'at 1 mA, 27.7 V clamp at 54.2 A for 10/1000 us, 1.0 uA maximum '
          'leakage at standoff, 0.090 %/K VBR coefficient: the 85 C clamp is '
          '29.19 V, which leaves 10.8 V to the 40 V parts but is above the '
          '28 V protected-rail target, which is why the A5 input has its own '
          'second stage. SUSTAINED input must stay at or below 17.1 V; a '
          '24 V jump start is a declared excluded exposure. POLARITY is '
          'now visible in the drawing, unlike Device:D_TVS which LRA-06 had '
          'to use: Diode:1.5KExxA is the unidirectional family and draws a '
          'cathode bar, with pin 1 the banded cathode to P12 and pin 2 the '
          'anode to PGND - asserted by pin number in check_capture.py, because the '
          'pins are still named A1/A2 and ERC cannot check a cathode bar. '
          'DESIGN.md S3 records this part being fitted backwards once '
          'already (R06-REV-4)')
part('C0', 'Device:C', '100nF/63V', 685.8, 68.58,
     nets={1: 'P12', 2: 'PGND'}, fp=FP_C_DISC, status='VERIFY_OR_SOURCE',
     source='DESIGN.md S3', note='always-on input ceramic')
part('RGS', 'Device:R', '10k', 546.1, 109.22,
     nets={1: 'P12', 2: 'GATE'}, fp=FP_R, status='VERIFY_STOCK',
     source='DESIGN.md S3 / MAX_ON_CUTOFF HOLD-path section',
     note='gate-source pullup, keeps QP off at rest. CHANGED from 100k to '
          '10k by the MAX_ON HOLD-path revision: with 10k the 0.2 V off-gate '
          'limit allows 19.80 uA of total sink leakage rather than 2 uA, '
          'which is what makes the added series switch tolerable. Maximum '
          'dissipation at 16 V is 25.9 mW')
part('DZ', 'Device:D_Zener', 'BZX55C10', 546.1, 139.7, rot=270,
     nets={1: 'P12', 2: 'GATE'}, fp=FP_DO35_K, mpn='Vishay BZX55C10-TAP',
     status='PAIRED_SELECTED', source='COMPONENT_MARGIN_CLOSURE S2 / '
                                      'BOM_DELTA.csv',
     note='gate-source clamp, lowered from 12 V as the paired half of the QP '
          'change: the selected QP has an ASYMMETRIC absolute gate rating of '
          '+5/-16 V, not +/-16 V. 9.4-10.6 V at 5 mA keeps the gate inside '
          'the -14 to +1 V acceptance band at every P12 in the envelope. Do '
          'not populate the new QP with the old 12 V clamp or the old 18 V '
          'magnitude criterion. Low-current and hot clamp voltage remain '
          'unproved: at 12 V the clamp current is only about 1 mA, below the '
          '5 mA test point. Polarity: pin 1 is the cathode, on P12')
part('RG', 'Device:R', '1k', 546.1, 177.8,
     nets={1: 'GATE', 2: 'SINK'}, fp=FP_R_HALFW, status='VERIFY_STOCK',
     source='DESIGN.md S3',
     note='gate sink resistor, 0.5 W position: a clamp short leaves at most '
          '16*16/990 = 0.259 W here')
part('QP', 'Transistor_FET:Q_PMOS_GDS', 'IPD50P04P4L-11', 584.2, 109.22,
     nets={1: 'GATE', 2: 'VIN_SW', 3: 'P12'}, fp=FP_DPAK,
     mpn='Infineon IPD50P04P4L11ATMA2', status='PAIRED_SELECTED',
     source='COMPONENT_MARGIN_CLOSURE S2 / BOM_DELTA.csv',
     note='the switch, selected rather than left at IRF4905 because this is '
          'the part that forces the whole X7 chain: its zero-gate drain '
          'current has a HOT maximum, 70 uA at 125 C (at VDS = -32 V, so '
          'conservative against the 12-16 V actually applied), where the '
          'IRF4905 screen is 250 uA at 150 C and cannot fit the 200 uA '
          'parked allocation at all. Its VDS is -40 V, which is what sets '
          'the entry clamp below 40 V. RDS(on) <=17.2 mohm at -4.5 V/25 C. '
          'PG-TO252-3 DPAK: gate 1, drain 2 and tab, source 3 - the tab is '
          'drain, so the pad carries battery-side switched voltage and is a '
          'layout thermal and clearance item. Body diode is drain-to-source: '
          'it blocks P12 to VIN_SW when off but does not block reverse energy')
part('RI', 'Device:R', '2.2k', 571.5, 203.2, rot=90,
     nets={1: 'IGN_POS', 2: 'IGN_B'}, fp=FP_R, status='VERIFY_STOCK',
     source='DESIGN.md S3',
     note='QI base drive. At 17.1 V sustained the dissipation is 0.112 W, '
          'inside a 0.25 W part; the 0.318 W that would have forced a 0.5 W '
          'position came from the superseded 28 V protected-rail number')
part('RBI', 'Device:R', '100k', 584.2, 231.14,
     nets={1: 'IGN_B', 2: 'PGND'}, fp=FP_R, status='VERIFY_STOCK',
     source='DESIGN.md S3', note='QI base-emitter pulldown')
part('QI', 'Transistor_BJT:2N3904', '2N3904', 609.6, 203.2,
     nets={1: 'PGND', 2: 'IGN_B', 3: 'SINK'}, fp=FP_TO92,
     mpn='onsemi 2N3904', status='VERIFY_STOCK', source='DESIGN.md S3',
     note='direct ignition start path, independent of the qualification '
          'delay and of firmware. Its 40 V VCEO now has 10.8 V of margin to '
          'the 29.19 V hot entry clamp, which is why LRA-12 does not replace '
          'it: the lower clamp resolves the stated incompatibility instead. '
          'Off leakage under the 100k base pulldown is still unspecified hot. '
          'E/B/C = 1/2/3')
part('RBH', 'Device:R', '100k', 660.4, 231.14,
     nets={1: 'HOLD_B', 2: 'PGND'}, fp=FP_R, status='VERIFY_STOCK',
     source='DESIGN.md S3',
     note='QH base-emitter pulldown; stays fitted when JH is open')
part('QH', 'Transistor_BJT:2N3904', '2N3904', 685.8, 203.2,
     nets={1: 'PGND', 2: 'HOLD_B', 3: 'QH_C'}, fp=FP_TO92,
     mpn='onsemi 2N3904', status='VERIFY_STOCK',
     source='DESIGN.md S3 / D2 / MAX_ON_CUTOFF HOLD-path section',
     note='firmware HOLD path. Its COLLECTOR NO LONGER GOES DIRECTLY TO '
          'SINK: QS now sits between them, which is where the independent '
          'cutoff interrupts the HOLD path (capture question Q6, closed). The '
          'emitter stays grounded; interrupting the emitter instead would '
          'couple fault voltage into the HOLD interface')
part('CIN', 'Device:C_Polarized', '100uF/50V', 635, 109.22,
     nets={1: 'VIN_SW', 2: 'PGND'}, fp='Capacitor_THT:CP_Radial_D8.0mm_P3.50mm',
     mpn='Panasonic EEUFR1H101', status='CONDITIONAL',
     source='COMPONENT_MARGIN_CLOSURE S1 / BOM_DELTA.csv',
     note='switched-input bulk, exact part now selected: 100 uF +/-20 % 50 V, '
          '8 x 11.5 mm radial on 3.5 mm pitch, 0.870 A RMS at 100 kHz/105 C, '
          'impedance <=0.061 ohm at 100 kHz/20 C. Temperature impedance and '
          'inrush remain qualification gates. POLARITY: pin 1 is + and goes '
          'to VIN_SW')
part('CIB', 'Device:C', '100nF/63V', 660.4, 109.22,
     nets={1: 'VIN_SW', 2: 'PGND'}, fp=FP_C_DISC, status='VERIFY_OR_SOURCE',
     source='DESIGN.md S3', note='local switched-input bypass; keep the loop short')
part('RBIN', 'Device:R', '10k', 685.8, 109.22,
     nets={1: 'VIN_SW', 2: 'PGND'}, fp=FP_R, status='VERIFY_STOCK',
     source='DESIGN.md S3', note='switched-input bleeder')
part('UREG', 'Custom:LM2678T-5.0', 'LM2678T-5.0', 754.38, 139.7,
     nets={2: 'VIN_SW', 4: 'PGND', 1: 'SW', 3: 'BOOST', 6: 'B5'},
     nc=(7,),
     fp='Package_TO_SOT_THT:TO-220-7_P2.54x3.7mm_StaggerEven_Lead3.8mm_Vertical',
     mpn='TI LM2678T-5.0/NOPB', status='MISSING_OR_VERIFY_SPARE',
     source='DESIGN.md S3 / D-POWER-03',
     note='symbol copied from keyless/hardware/Custom.kicad_sym. The same '
          'regulator, in the same role, runs in service on the keyless board '
          'in this car on a permanent 12 V feed, through cranking. Pin 7 '
          'ON/OFF left open and pin 5 NC unconnected, as DESIGN.md S3 '
          'specifies. Do not remove the installed keyless regulator')
part('CBOOST', 'Device:C', '10nF/50V', 797.56, 127, rot=90,
     nets={1: 'SW', 2: 'BOOST'}, fp=FP_C_DISC, status='VERIFY_OR_SOURCE',
     source='DESIGN.md S3', note='between SW and BOOST; keep short')
part('DCATCH', 'Device:D_Schottky', 'SB360-E3/54', 716.28, 190.5, rot=270,
     nets={1: 'SW', 2: 'PGND'}, fp=FP_DO201_A, mpn='Vishay SB360-E3/54',
     status='MISSING_OR_VERIFY_SPARE', source='DESIGN.md S3',
     note='catch diode; a tight local loop with CIN is a layout requirement')
part('L1', 'Device:L', '22uH', 754.38, 190.5, rot=90,
     nets={1: 'SW', 2: 'B5'},
     fp='Inductor_THT:L_Radial_D8.7mm_P5.00mm_Fastron_07HCP',
     mpn='Bourns RLB0912-220KL', status='MISSING',
     source='DESIGN.md S3 / D-POWER-03 consequence 4',
     note='normal-load margin only: the LM2678 fault current limit exceeds '
          'its 2.5 A saturation rating. Keyless runs a physically larger 2 A '
          '22 uH part in the same role, which is the comparison to make '
          'before accepting this one for the vehicle')
part('RB5', 'Device:R', '1k', 749.3, 215.9,
     nets={1: 'B5', 2: 'PGND'}, fp=FP_R, status='VERIFY_STOCK',
     source='DESIGN.md S3', note='B5 bleeder; supports the B07 decay measurement')
part('COB', 'Device:C', '100nF/50V', 774.7, 215.9,
     nets={1: 'B5', 2: 'PGND'}, fp=FP_C_DISC, status='VERIFY_OR_SOURCE',
     source='DESIGN.md S3', note='B5 local bypass')
part('COUT', 'Device:C_Polarized', '1000uF/16V', 800.1, 215.9,
     nets={1: 'B5', 2: 'PGND'},
     fp='Capacitor_THT:CP_Radial_D10.0mm_P5.00mm',
     mpn='Panasonic EEUFR1C102', status='CONDITIONAL',
     source='COMPONENT_MARGIN_CLOSURE S1 / BOM_DELTA.csv',
     note='buck output bulk, exact part now selected, replacing the '
          'unspecified 820 uF: 1000 uF +/-20 % 16 V, 10 x 16 mm radial on '
          '5 mm pitch, 1.790 A RMS at 100 kHz/105 C, impedance <=0.028 ohm '
          'at 100 kHz/20 C. Two gates travel with it: LM2678 loop stability '
          'is not established by a ripple rating, and the larger stored '
          'charge pushes the bleeder-only decay screen to about 5.39 s '
          'against the 5 s criterion, so the assembled decay must be '
          'measured rather than inherited. POLARITY: pin 1 is + and goes '
          'to B5')
part('DOR', 'Diode:1N4004', '1N4004-E3/54', 754.38, 248.92, rot=180,
     nets={2: 'B5', 1: 'VSYS'}, fp=FP_DO41_K, mpn='Vishay 1N4004-E3/54',
     status='MISSING', source='REV_A_INTERFACES D13',
     note='D13 replaces the power BOM 1N5819 with the 1N4004 candidate for '
          'its specified reverse-current maxima, 5 uA at 25 C and 50 uA at '
          '125 C; B5 anode to VSYS cathode. Blocks USB back into B5 apart '
          'from leakage. Do not use this slow rectifier as the buck catch '
          'diode')

# ============================== X8: independent maximum-on cutoff, A5 domain
# MAX_ON_CUTOFF.md's connection table, with the clock block of
# CUTOFF_MARGIN_REVIEW.md S1. Equations, verbatim from that table:
#   BASE_RESET   = BAD OR IGN_Q
#   COUNT1_RESET = BASE_RESET OR NARM
#   ARM_RESET    = BAD OR EXPIRED OR HOLD_N
#   RESET_N      = NOT ARM_RESET
#   SET_N        = NOT (IGN_Q AND RESET_N)
#   ARM          = NAND(SET_N, NARM)
#   NARM         = NAND(RESET_N, ARM)
g = Grid(40.64, 700.0, 300.0)
x, y = g.next()
part('RCLK', 'Device:R', '1k', x, y, nets={1: 'A5', 2: 'VCLK'},
     fp=FP_R, status='VERIFY_STOCK', source='CUTOFF_MARGIN_REVIEW S1',
     note='1 %. With CCLK this is the oscillator supply filter. The '
          'oscillator specifies a 0.5 V/ms maximum supply slew; for a 5.11 V '
          'step and minimum RC the contribution is 0.235 V/ms, and a 100 uA '
          'VCLK load allowance adds 0.0046 V/ms on falling ramps and at most '
          '0.101 V of static drop')
x, y = g.next()
part('CCLK', 'Device:C_Polarized', '33uF/16V', x, y,
     nets={1: 'VCLK', 2: 'PGND'}, fp=FP_CP_TANT_D,
     mpn='KEMET T491D336K016AT', status='CONDITIONAL',
     source='COMPONENT_MARGIN_CLOSURE S1 / BOM_DELTA.csv',
     note='oscillator rail reservoir. 33 uF +/-10 % 16 V tantalum, EIA '
          '7343-31 D case, selected against an effective 22-60 uF '
          'requirement; the supporting engineering stack is 24.057-43.923 uF '
          'and combined-stress bounds are still required. POLARITY: pin 1 is '
          'the + terminal and goes to VCLK - a reversed tantalum fails '
          'short, and this one sits on the always-on rail')
x, y = g.next()
part('C_CLK', 'Device:C', '10nF', x, y, nets={1: 'VCLK', 2: 'PGND'},
     fp=FP_C_DISC, status='VERIFY_OR_SOURCE',
     source='CUTOFF_MARGIN_REVIEW S1', note='local oscillator bypass')
x, y = g.next(dx=63.5)
part('UXO', 'Custom:OV-7604-C7', 'OV-7604-C7-32.768KHZ-20PPM-TA-QC', x, y,
     nets={4: 'VCLK', 3: 'CLKOE', 2: 'PGND', 1: 'XO_OUT'}, fp=FP_OSC,
     mpn='Micro Crystal OV-7604-C7-32.768KHZ-20PPM-TA-QC',
     status='SELECTED', source='CUTOFF_MARGIN_REVIEW S1',
     note='the independent timebase. Integrated crystal and oscillator, so '
          'XTAL, RF, RS, CX1 and CX2 of the earlier bare-crystal candidate '
          'are gone. +/-20 ppm initial, TA = -40 to +85 C, 0.3/0.5 uA at '
          '3.0 V with CLKOE low, 0.5 s maximum startup at the datasheet '
          'default conditions. The +/-220 ppm first-year envelope used for '
          'the cutoff arithmetic is assembled from 20 ppm initial, 188.65 ppm '
          'of -0.035 ppm/K^2 curvature at -40 C against a 30 C turnover, '
          '3.75 ppm of voltage coefficient and 3 ppm aging: an engineering '
          'envelope, not a combined manufacturer guarantee. Keep total '
          'XO_OUT load at or below 10 pF. Note the ordering code: QC is '
          'commercial grade - AEC-Q200 is available as QA and is a '
          'procurement decision, not a redesign')
x, y = g.next(dx=63.5)
part('UOE', '74xGxx:74LVC1G17', '74AHC1G17GV', x, y,
     nets={2: 'ARM', 3: 'PGND', 4: 'CLKOE', 5: 'VCLK'}, fp=FP_SOT353,
     mpn='Nexperia 74AHC1G17GV', status='CONDITIONAL',
     source='COMPONENT_MARGIN_CLOSURE S2 / BOM_DELTA.csv',
     note='translates ARM to the filtered oscillator rail without injecting '
          'A5 into the enable pin. The installed 74xGxx:74LVC1G17 symbol is '
          'used because the selected 74AHC1G17GV has the identical SOT-353 '
          'mapping (NC 1, A 2, GND 3, Y 4, VCC 5) and function; the Value and '
          'MPN fields carry the part actually selected. Schmitt input, 0-5.5 V '
          'overvoltage-tolerant including VCC = 0, 1 uA / 10 uA unloaded ICC '
          'at 25/85 C. Two conditions travel with it: the minimum operating '
          'rail is 2.0 V, not 1.65 V, so startup while VCLK crosses 2 V must '
          'be checked, and its largest tabulated positive threshold is 3.85 V '
          'at 5.5 V, so loaded ARM must reach 4.0 V. Do not substitute a '
          'conventional CMOS gate with input-to-VCC clamps')
x, y = g.next()
part('C_OE', 'Device:C', '100nF', x, y, nets={1: 'VCLK', 2: 'PGND'},
     fp=FP_C_DISC, status='VERIFY_OR_SOURCE',
     source='CUTOFF_MARGIN_REVIEW S1',
     note='UOE bypass, across its own VCLK supply')
g.newline(dy=30.48)
x, y = g.next(dx=63.5)
part('UGCLK', '74xGxx:74LVC1G97', 'SN74LVC1G97DBVR', x, y,
     nets={1: 'PGND', 2: 'PGND', 3: 'XO_OUT', 4: 'CLK32', 5: 'A5',
           6: 'ARM'}, fp=FP_SOT23_6, mpn='TI SN74LVC1G97DBVR',
     status='RETAIN', source='CUTOFF_MARGIN_REVIEW S1 / '
                             'COMPONENT_MARGIN_CLOSURE S2',
     note='configurable gate wired as an AND, so disarmed means CLK32 = 0 '
          'and the counter chain stops rather than running on after '
          'shutdown. IN1 (1) to ground, IN0 (3) from the oscillator, IN2 (6) '
          'from ARM, Y (4) to the counter. Retained over a 74AHC1G08, which '
          'would save room current but removes the Schmitt input tolerance '
          'that lets this gate accept XO_OUT while A5 is collapsing and '
          'XO_OUT is temporarily higher than its own rail. Its output shares '
          'A5 with the counters')
x, y = g.next()
part('C_GCLK', 'Device:C', '100nF', x, y, nets={1: 'A5', 2: 'PGND'},
     fp=FP_C_DISC, status='VERIFY_OR_SOURCE',
     source='CUTOFF_MARGIN_REVIEW S1', note='UGCLK bypass')

# --- the counters, latch and reset logic
g = Grid(330.0, 700.0, 828.0, dx=76.2, dy=40.64)
x, y = g.next()
part('UCLK', 'Custom:CD74HC4060', 'CD74HC4060E', x, y,
     nets={16: 'A5', 8: 'PGND', 12: 'COUNT1_RESET', 11: 'CLK32',
           3: 'UCLK_Q14'},
     nc=(1, 2, 4, 5, 6, 7, 9, 10, 13, 14, 15), fp=FP_DIP16,
     mpn='TI CD74HC4060E', status='SELECTED', source='MAX_ON_CUTOFF table',
     note='first divider. Driven from the external clock on pin 11 with the '
          'internal oscillator pins 9 and 10 left open. Q14 gives 2 falling '
          'edges per second from 32768 Hz. MR on pin 12 is active high and '
          'comes from COUNT1_RESET, so the chain is stopped - not cleared - '
          'when disarmed. Retained as HC rather than HEF: the HEF parts '
          'specify 20/150 uA against HC 8/80 uA and would worsen the parked '
          'screen')
x, y = g.next()
part('UCOUNT', 'Custom:CD74HC4020', 'CD74HC4020E', x, y,
     nets={16: 'A5', 8: 'PGND', 10: 'UCLK_Q14', 11: 'BASE_RESET',
           2: 'CNT_Q13', 13: 'CNT_Q8'},
     nc=(1, 3, 4, 5, 6, 7, 9, 12, 14, 15), fp=FP_DIP16,
     mpn='TI CD74HC4020E', status='SELECTED', source='MAX_ON_CUTOFF table',
     note='second divider. Q13 on pin 2 first rises on edge 4096, which at '
          '2 edges per second is the nominal 2048 s production deadline; Q8 '
          'on pin 13 gives 64 s for the accelerated test. It is reset by '
          'BASE_RESET, which is BAD OR IGN_Q - deliberately NOT by NARM, '
          'because that would erase EXPIRED the moment it disarmed the latch')
x, y = g.next()
part('ULATCH', 'Custom:CD4011B', 'CD4011BE', x, y,
     nets={1: 'SET_N', 2: 'NARM', 3: 'ARM', 4: 'NARM', 5: 'RESET_N',
           6: 'ARM', 7: 'PGND', 8: 'QUAL_N', 9: 'QUAL_N', 10: 'IGN_Q',
           12: 'PGND', 13: 'PGND', 14: 'A5'},
     nc=(11,), fp=FP_DIP14, mpn='TI CD4011BE', status='SELECTED',
     source='MAX_ON_CUTOFF table / CUTOFF_MARGIN_REVIEW S2',
     note='reset-dominant ARM/NARM latch on gates A and B, and the QUAL_N '
          'inverter that produces IGN_Q on gate C. Gate D is unused, so its '
          'inputs 12 and 13 are tied to ground rather than left floating - an '
          'unused CMOS input at an intermediate level draws current and can '
          'oscillate. Pin 11 is its unused output')
x, y = g.next()
part('UOR', 'Custom:CD4071B', 'CD4071BE', x, y,
     nets={1: 'BAD', 2: 'IGN_Q', 3: 'BASE_RESET', 4: 'COUNT1_RESET',
           5: 'BASE_RESET', 6: 'NARM', 7: 'PGND', 8: 'BAD', 9: 'EXPIRED',
           10: 'FAULT_RESET', 11: 'ARM_RESET', 12: 'FAULT_RESET',
           13: 'HOLD_N', 14: 'A5'},
     fp=FP_DIP14, mpn='TI CD4071BE', status='SELECTED',
     source='MAX_ON_CUTOFF table',
     note='the reset tree: BASE_RESET = BAD OR IGN_Q, COUNT1_RESET = '
          'BASE_RESET OR NARM, FAULT_RESET = BAD OR EXPIRED, ARM_RESET = '
          'FAULT_RESET OR HOLD_N. All four gates are used')
x, y = g.next()
part('USCH', 'Custom:CD4093B', 'CD4093BE', x, y,
     nets={1: 'IGN_RC', 2: 'A5', 3: 'QUAL_N', 4: 'BAD', 5: 'PGOOD',
           6: 'PGOOD', 7: 'PGND', 8: 'ARM_RESET', 9: 'ARM_RESET',
           10: 'RESET_N', 11: 'SET_N', 12: 'IGN_Q', 13: 'RESET_N',
           14: 'A5'},
     fp=FP_DIP14, mpn='TI CD4093BE', status='SELECTED',
     source='MAX_ON_CUTOFF table / CUTOFF_MARGIN_REVIEW S2',
     note='Schmitt NANDs. Gate A qualifies the ignition RC filter against '
          'single-input thresholds VP 2.2-3.6 V and VN 0.9-2.8 V at a 5 V '
          'rail, which with the filter gives roughly 104-376 ms ON and '
          '119-590 ms OFF qualification from SETTLED endpoints - not a bound '
          'across the whole A5 range, because that datasheet does not '
          'tabulate every intermediate supply. Gate B inverts the supervisor '
          'to BAD. Gates C and D form RESET_N and SET_N. All four gates used')
g.newline(dy=36.0)
g.dx, g.dy = 44.45, 20.32
for ref, net in (('C_UCLK', 'A5'), ('C_UCOUNT', 'A5'), ('C_ULATCH', 'A5'),
                 ('C_UOR', 'A5'), ('C_USCH', 'A5')):
    x, y = g.next()
    part(ref, 'Device:C', '100nF', x, y, nets={1: net, 2: 'PGND'},
         fp=FP_C_DISC, status='VERIFY_OR_SOURCE', source='MAX_ON_CUTOFF table',
         note='local bypass, one per package, directly across its own supply '
              'pins - a layout requirement as much as a BOM line')
x, y = g.next()
part('R_EXPP', 'Device:R', '0R', x, y, nets={1: 'CNT_Q13', 2: 'EXPIRED'},
     fp=FP_R, status='SELECTED', source='LAYOUT_CLOSURE S5',
     note='PRODUCTION cutoff period selector, fitted: takes EXPIRED from Q13, '
          'the nominal 2048 s terminal count. FIT EXACTLY ONE of R_EXPP and '
          'R_EXPT - they are two counter outputs and must never be shorted '
          'together. A link option rather than a jumper header so the '
          'production state cannot be changed by something falling off')
x, y = g.next()
part('R_EXPT', 'Device:R', '0R', x, y, nets={1: 'CNT_Q8', 2: 'EXPIRED'},
     fp=FP_R, status='DNP', dnp=True, source='LAYOUT_CLOSURE S5',
     note='ACCELERATED TEST cutoff selector, DO NOT POPULATE in production: '
          'takes EXPIRED from Q8 instead, giving 128/2 = 64 s so a full '
          'cutoff sequence can be exercised on the bench without a 34 minute '
          'wait. Clearly distinguished from the production selection, as the '
          'packet requires, and from JH, which is the maintenance HOLD link. '
          'An accelerated run does not substitute for one full-duration test')
x, y = g.next()
part('R_EXP', 'Device:R', '100k', x, y, nets={1: 'EXPIRED', 2: 'PGND'},
     fp=FP_R, status='SELECTED', source='LAYOUT_CLOSURE S5',
     note='defines EXPIRED if neither selector link is fitted, so a CMOS '
          'input is never left floating. It costs nothing while parked: '
          'EXPIRED is LOW until the deadline, and only then does the counter '
          'output source 50 uA into it')
x, y = g.next()
part('QS', 'Transistor_FET:BSS138', 'BSS138P', x, y,
     nets={1: 'ARM_G', 2: 'QH_C', 3: 'SINK'}, fp=FP_SOT23_3,
     mpn='Nexperia BSS138P', status='VERIFY_STOCK',
     source='MAX_ON_CUTOFF HOLD-path permission switch',
     note='the series interruption in the HOLD path, and the answer to '
          'capture question Q6: drain to SINK, source to the QH collector, '
          'so the body diode points from the QH collector toward SINK and '
          'blocks the sink direction when off. It grants permission only - it '
          'cannot sink without QH - and QI stays wired directly to SINK, so '
          'raw ignition still overrides. 60 V VDS, 2 ohm maximum at '
          'VGS = 5 V, drain leakage 1 uA at 25 C and 10 uA at 150 C at 60 V, '
          'which is what favours it over a 2N7000 here. gate 1, source 2, '
          'drain 3. Its gate drive is reduced by the divider and by the QH '
          'collector voltage, so no RDS claim rests on exactly 5 V')
x, y = g.next()
part('R_QSG', 'Device:R', '1k', x, y, nets={1: 'ARM', 2: 'ARM_G'},
     fp=FP_R, status='VERIFY_STOCK',
     source='MAX_ON_CUTOFF HOLD-path permission switch',
     note='QS gate series resistor')
x, y = g.next()
part('R_QSPD', 'Device:R', '100k', x, y, nets={1: 'ARM_G', 2: 'PGND'},
     fp=FP_R, status='VERIFY_STOCK',
     source='MAX_ON_CUTOFF HOLD-path permission switch',
     note='QS gate pulldown; the switch is open with A5 absent, so loss of '
          'the timer supply defaults to inhibit')
x, y = g.next()
part('QMON', 'Transistor_BJT:2N3904', '2N3904', x, y,
     nets={1: 'PGND', 2: 'MON_B', 3: 'HOLD_N'}, fp=FP_TO92,
     mpn='onsemi 2N3904', status='VERIFY_STOCK',
     source='MAX_ON_CUTOFF HOLD sense section',
     note='senses HOLD without putting a 5 V pullup on a GPIO. Collector is '
          'HOLD_N, so LOW means HOLD_RAW asserted. It taps HOLD_RAW BEFORE '
          'JH, so opening the maintenance link still releases QH but does '
          'not change what the monitor sees. Adds roughly 50 uA of GPIO base '
          'load while HOLD is asserted, and that is not a timer refresh '
          'path. Third 2N3904 beyond QI and QH; verify spare quantity rather '
          'than assuming two cover three. E/B/C = 1/2/3')
x, y = g.next()
part('R_MONB', 'Device:R', '47k', x, y, nets={1: 'HOLD_RAW', 2: 'MON_B'},
     fp=FP_R, status='VERIFY_STOCK', source='MAX_ON_CUTOFF HOLD sense section',
     note='QMON base resistor from HOLD_RAW, ahead of JH')
x, y = g.next()
part('R_MONPD', 'Device:R', '100k', x, y, nets={1: 'MON_B', 2: 'PGND'},
     fp=FP_R, status='VERIFY_STOCK', source='MAX_ON_CUTOFF HOLD sense section',
     note='QMON base-emitter pulldown')
x, y = g.next()
part('R_MONC', 'Device:R', '100k', x, y, nets={1: 'HOLD_N', 2: 'A5'},
     fp=FP_R, status='VERIFY_STOCK', source='MAX_ON_CUTOFF HOLD sense section',
     note='HOLD_N collector pullup to A5. 1 uA of QMON collector leakage '
          'moves this node 0.101 V, so it is not ideal isolation and belongs '
          'in the parked accounting')

# ======================================================= test points (S5.3)
TPS1 = [('TP_P12', 'P12'), ('TP_GATE', 'GATE'), ('TP_VINSW', 'VIN_SW'),
        ('TP_SW', 'SW'), ('TP_B5', 'B5'), ('TP_VSYS', 'VSYS'),
        ('TP_3V3', 'P3V3_SW'), ('TP_PAON', 'P_AON'), ('TP_A5', 'A5'),
        ('TP_VCLK', 'VCLK')]
TPS2 = [('TP_QUALN', 'QUAL_N_REPORT'), ('TP_IGNRC', 'IGN_RC'),
        ('TP_IGNQ', 'IGN_Q'), ('TP_CLK32', 'CLK32'), ('TP_ARM', 'ARM'),
        ('TP_EXPIRED', 'EXPIRED'), ('TP_PGOOD', 'PGOOD'),
        ('TP_HOLDN', 'HOLD_N'), ('TP_HOLD', 'HOLD_RAW'),
        ('TP_ISOEN', 'ISO_EN')]
TPS3 = [('TP_GND_BUCK', 'PGND'), ('TP_GND_PICO', 'PGND'),
        ('TP_GND_HARNESS', 'AGND'), ('TP_GP11', 'SPARE_GP11'),
        ('TP_GP12', 'SPARE_GP12')]
TP_NOTE = {
    'TP_ARM': 'A5-domain cutoff logic; no GPIO connection',
    'TP_EXPIRED': 'A5-domain cutoff logic; no GPIO connection',
    'TP_PGOOD': 'A5-domain cutoff logic; no GPIO connection. Also the source '
                'of the hardware isolation permission',
    'TP_HOLDN': 'A5-domain cutoff logic; no GPIO connection',
    'TP_GND_BUCK': 'buck return loop',
    'TP_GND_PICO': 'Pico return loop',
    'TP_GND_HARNESS': 'harness-end loop on the bonded B16 / AGND sense node',
    'TP_GP11': 'unassigned GPIO brought to a pad (S1)',
    'TP_GP12': 'unassigned GPIO brought to a pad (S1)',
    'TP_GATE': 'QP gate: the -14 to +1 V acceptance band is measured here '
               'against TP_P12',
    'TP_SW': 'from the power BOM TP row, additional to S5.3',
    'TP_PAON': 'A5 regulator input, after the second-stage clamp: the <=28 V '
               'protected-rail criterion is measured here, not at P12',
    'TP_IGNRC': 'ignition filter node; B02 asks for it scoped with partially '
                'charged starting conditions',
    'TP_IGNQ': 'the hardware qualification decision itself, before QREPORT',
    'TP_CLK32': 'gated 32.768 kHz clock into the counter chain; carries the '
                'frequency and startup measurements the 2048 s arithmetic '
                'depends on',
    'TP_ISOEN': 'B2 isolation enable, for the isolate-then-release ordering',
}
for row, Y in ((TPS1, 520.7), (TPS2, 545.0), (TPS3, 569.3)):
    for i, (ref, net) in enumerate(row):
        part(ref, 'Connector:TestPoint', 'TestPoint', 546.1 + i * 28.0, Y,
             nets={1: net}, fp=FP_TP, hide_value=True,
             status='VERIFY_OR_SOURCE', source='REV_A_INTERFACES S5.3',
             note=TP_NOTE.get(ref, 'insulated test loop'))

# Power flags: these nets reach a power-input pin through passive parts only,
# so ERC needs an explicit driver on each.
part('#FLG1', 'power:PWR_FLAG', 'PWR_FLAG', 711.2, 109.22,
     nets={1: 'VIN_SW'}, bom=False, hide_value=True)
part('#FLG2', 'power:PWR_FLAG', 'PWR_FLAG', 800.1, 248.92,
     nets={1: 'VSYS'}, bom=False, hide_value=True)
part('#FLG3', 'power:PWR_FLAG', 'PWR_FLAG', 320.0, 655.0,
     nets={1: 'P_AON'}, bom=False, hide_value=True)
part('#FLG4', 'power:PWR_FLAG', 'PWR_FLAG', 260.0, 745.0,
     nets={1: 'VCLK'}, bom=False, hide_value=True)

# ======================================================= annotation
# KiCad requires a reference of the form <prefix><number>; the descriptive and
# source-document names are kept in a Source_designator field and the BOM so a
# reviewer can still diff against the written sources. Diodes are numbered from
# 101 so that schematic designators can never be read as the delta IDs D1-D15.
KEEP = {'U1', 'U2', 'J1', 'J2', 'J3', 'J4', 'J5'}
PREFIX = [
    ('Custom:PLACEHOLDER_', 'X', 1),
    ('Connector:TestPoint', 'TP', 1),
    ('Connector_Generic:', 'J', 1),
    ('Jumper:', 'JP', 1),
    ('MCU_Module:', 'U', 1),
    ('Isolator:', 'U', 1),
    ('Power_Supervisor:', 'U', 1),
    ('74xGxx:', 'U', 1),
    ('Custom:LM2678T', 'U', 1),
    ('Custom:CD', 'U', 1),
    ('Custom:TPS', 'U', 1),
    ('Custom:OV-', 'U', 1),
    ('Custom:ASSR', 'U', 1),
    ('Transistor_', 'Q', 1),
    ('Transistor_FET:Q_', 'Q', 1),
    ('Device:R', 'R', 1),
    ('Device:C', 'C', 1),
    ('Device:L', 'L', 1),
    ('Device:Fuse', 'F', 1),
    ('Device:D_', 'D', 101),
    ('Diode:', 'D', 101),
]
# U1/U2 and J1-J5 are fixed by the written sources, so start after them.
counters = {'U': 2, 'J': 5}
for p in P:
    p['srcref'] = p['ref']
    if p['ref'] in KEEP or not p['bom']:
        continue
    for pat, pre, start in PREFIX:
        if p['lib_id'].startswith(pat):
            n = counters.get(pre)
            n = start if n is None else n + 1
            counters[pre] = n
            p['ref'] = f'{pre}{n}'
            break
    else:
        raise SystemExit('no reference prefix for ' + p['lib_id'])
taken = [p['ref'] for p in P]
assert len(taken) == len(set(taken)), 'duplicate reference'

# ================================================================== build
sh = schgen.Sheet(
    'Accord logger Rev A - complete electrical design for layout (LRA-12)',
    'A-layout', paper='A0',
    comments=('Electrical design complete for owner placement and routing; '
              'not frozen, not ordered, not fabricated',
              'Claude logger-electrical, session '
              'b690946d-3a88-4626-8e7b-b321126a3d16 (LRA-12)',
              'Built on the LRA-06 capture by Claude logger-schematic, '
              'session 73d7d954-f82a-4038-8ff3-546a23fc5fa9',
              'Decisions and calculations: power/LAYOUT_CLOSURE.md; '
              'residual gates: LRA12_HANDOFF.md'))
sh.lib = schgen.Lib(extra={'Custom': CUSTOM})

for p in P:
    fields = {}
    if p['status']:
        fields['Status'] = p['status']
    if p['source']:
        fields['Source'] = p['source']
    if p['mpn']:
        fields['MPN'] = p['mpn']
    if p['srcref'] != p['ref']:
        fields['Source_designator'] = p['srcref']
    sh.symbol(p['ref'], p['lib_id'], p['value'], p['x'], p['y'],
              nets=p['nets'], rot=p['rot'], footprint=p['fp'],
              fields=fields, nc=p['nc'], in_bom=p['bom'],
              hide_value=p['hide_value'], dnp=p['dnp'])

# ------------------------------------------------------------- block frames
BLOCKS = [
    (17.78, 20.32, 360.68, 460.0,
     'VEHICLE INPUTS  -  AS_BUILT S2, ratios and clamps unchanged; '
     'B2 series isolation fitted, other four branches bypassed'),
    (373.38, 20.32, 510.54, 200.66, 'PICO W  -  REV_A_INTERFACES S1 Rev A column'),
    (373.38, 213.36, 510.54, 320.04, 'HOLD DRIVER  -  delta D2'),
    (373.38, 332.74, 510.54, 410.0, 'SD  -  AS_BUILT S3.5, delta D6'),
    (373.38, 420.0, 510.54, 571.5,
     'EXPANSION (DNP BUS) AND RESET  -  LRA-04 bounded provision'),
    (17.78, 470.0, 360.68, 571.5,
     'IGNITION OPTO CELL, VEHICLE SIDE  -  AS_BUILT S3.4; LED return moved '
     'to PGND'),
    (523.24, 20.32, 828.04, 290.0,
     'ONBOARD SWITCHED POWER  -  power/DESIGN.md S3, deltas D7 and D13, '
     'X7 entry clamp resolved'),
    (523.24, 500.0, 828.04, 583.0,
     'TEST POINTS AND GROUND LOOPS  -  REV_A_INTERFACES S5.3, delta D8'),
    (17.78, 585.0, 310.0, 668.0,
     'X6 RESOLVED: QUALIFIED IGNITION, A5 DOMAIN  -  CUTOFF_MARGIN_REVIEW S2'),
    (318.0, 585.0, 583.0, 668.0,
     'X7 SECOND STAGE: ALWAYS-ON A5 SUPPLY AND SUPERVISOR  -  '
     'CUTOFF_MARGIN_REVIEW S3 + LAYOUT_CLOSURE S3'),
    (591.0, 585.0, 828.04, 668.0,
     'X1 ENABLE: GPIO PLUS HARDWARE PGOOD PERMISSION  -  LAYOUT_CLOSURE S4'),
    (17.78, 676.0, 310.0, 790.0,
     'INDEPENDENT CLOCK BLOCK  -  CUTOFF_MARGIN_REVIEW S1'),
    (318.0, 676.0, 828.04, 833.12,
     'X8 RESOLVED: INDEPENDENT MAXIMUM-ON CUTOFF, 2048 s  -  MAX_ON_CUTOFF'),
]
for x1, y1, x2, y2, title in BLOCKS:
    sh.rect(x1, y1, x2, y2, dash=False, width=0.3)
    sh.text(title, x1 + 2.54, y1 + 1.27, size=2.0, bold=True)

# -------------------------------------------------------------- text notes
NOTES = [
    ('LRA-12 - what changed, and the one thing to read first',
     'This is the LRA-06 capture with its eight electrical placeholders\n'
     'resolved. Every populated part now carries a checked footprint and\n'
     'no dashed NOT SELECTED body remains. The decisions, their\n'
     'calculations and the residual gates are in power/LAYOUT_CLOSURE.md\n'
     'and LRA12_HANDOFF.md; read those before changing anything here.\n'
     'X1  B2 series isolation      -> ASSR-601JV + 2-FET enable\n'
     'X2-X5 other four branches    -> justified bypass, see below\n'
     'X6  qualified IGN / QREPORT  -> captured from CUTOFF_MARGIN_REVIEW S2\n'
     'X7  vehicle entry protection -> 1.5KE20A + second-stage A5 clamp\n'
     'X8  independent cutoff       -> captured from MAX_ON_CUTOFF\n'
     'J1/J2 connectors             -> Molex Mini-Fit Jr., family in service\n'
     'Q2/R06-REV-2 opto LED return -> moved from B16 to PGND\n'
     'Q4 onboard FIGN              -> dropped; fuse belongs at the tap\n'
     'Q5 J4 service UART           -> dropped; J4 is the reset pair only\n'
     'Q6 where MAX_ON cuts HOLD    -> QS between SINK and the QH collector'),
    ('The voltage envelope, which is one chain and not five choices',
     'The selected QP is the only P-channel switch the record found with a\n'
     'HOT zero-gate leakage maximum (70 uA at 125 C) that fits the 200 uA\n'
     'parked allocation; the IRF4905 screen is 250 uA and cannot. That part\n'
     'is rated -40 V VDS, so the entry clamp has to hold below 40 V, which\n'
     'rules out the inherited 1.5KE30A at 41.4 V - the same 41.4 V that\n'
     'already exceeded QI/QH VCEO and the LM2678 operating ceiling. The\n'
     '1.5KE20A clamps at 27.7 V, 29.19 V at 85 C using its own 0.090 %/K\n'
     'coefficient, leaving 10.8 V to every 40 V part.\n'
     '29.19 V is still above the contract 28 V protected-rail target, so\n'
     'the A5 regulator gets its own second stage: R_AON 330R and a BZX55C22\n'
     'hold P_AON at or below 25.4 V at 85 C, 4.6 V inside the TPS709 30 V\n'
     'recommended maximum. The <=28 V criterion is therefore measured at\n'
     'TP_PAON, not at P12.\n'
     'SUSTAINED P12 must stay at or below 17.1 V, the clamp standoff. No\n'
     'single clamp can both stand off a 24 V jump start and limit to 28 V,\n'
     'so that exposure is declared excluded rather than quietly assumed\n'
     'survivable. See LAYOUT_CLOSURE S3 for the two alternatives and\n'
     'what each would cost.'),
    ('Vehicle inputs: one switch, four justified bypasses',
     'Five fitted cells, carried forward with no value changed (AS_BUILT S2).\n'
     'B2 is the only branch energized with the key out - 4.669 V open\n'
     'circuit, 4.140 V loaded, drawing 140.8 uA of which 109.2 uA was being\n'
     'back-fed into the unpowered 3V3 rail through a forward-biased clamp.\n'
     'It gets the series switch, upstream of the divider top as required.\n'
     'B1, C14, C11 and B11 are all ignition-fed and measured or logged dead\n'
     'with the key out, so they meet the parked criterion with no device and\n'
     'no device leakage. Reaching the board-off-and-energized criterion\n'
     'needs the key on AND an upstream power fault, because ignition\n'
     'present turns QI on and powers the board; in that fault state the\n'
     'fitted 7.5k-22k series resistance bounds each branch below 0.7 mA.\n'
     'Four more relays would cost 41 mA of awake LED current and four\n'
     '10.4 x 7.5 mm packages against a fault-only benefit. Full reachable-\n'
     'state table in LAYOUT_CLOSURE S4.\n'
     'Because no series element enters the fuel or supply top leg, the\n'
     'card header calibration (log.adc.fuel div=7500/4700) still has every\n'
     'term it needs and REV_A_INTERFACES S8.2 needs no change.\n'
     'Digital divider bottoms return to PGND. Both ADC divider bottoms,\n'
     'their filter and clamp returns, J2.6 (B16) and Pico AGND are ONE\n'
     'node. AGND and PGND are already joined INSIDE the Pico module, so\n'
     'that junction is the single point: layout must NOT add a second\n'
     'board-level bond between them.'),
    ('The opto LED return - R06-REV-2 decided',
     'The fitted cell returned the ignition LED cathode to the B16 cluster\n'
     'conductor with nothing in series, putting 4.7-5.8 mA of signal-\n'
     'dependent current through the node both ADC channels reference, which\n'
     'REV_A_INTERFACES S4 says must never become a power return. D5 and\n'
     'that return cannot both stand. LRA-12 moves the cathode to PGND, the\n'
     'arrangement DESIGN.md S3 already specified.\n'
     'What B16 still carries is the two divider return currents, at most\n'
     'about 0.65 mA combined and only while the cluster is energized; those\n'
     'are intrinsic to a ratio measurement referenced to cluster ground.\n'
     'The LED current was not.\n'
     'Consequence recorded rather than hidden: the LED now returns into the\n'
     'board instead of off-board. It cannot reach any switched rail - the\n'
     'opto output side is in the A5 domain and galvanically separate from\n'
     'the LED - so this removes an injection path rather than moving one.\n'
     'CTR margin at the measured 2.2k: 3.39 mA of LED current at the 9 V\n'
     'characterization point against 96 uA of emitter load, 15x on the\n'
     '>=50 % CTR at 5 mA. Hot CTR and the 4.5 V ON endpoint stay open.'),
    ('Pico W pin map',
     'GP0/GP1, GP14/GP15, GP20-GP22 and GP28 are deliberately unconnected.\n'
     'GP7 is now ISO_EN, the B2 isolation enable, confirmed free in S1.\n'
     'GP8/GP9 (UART1) and GP10 (tied DE//RE) go to the DNP expansion\n'
     'header, with GP13 offered there as a spare - offers, not reservations.\n'
     'ARM, EXPIRED, PGOOD and HOLD_N stay off the GPIOs: A5-domain test\n'
     'points only, and firmware has no ARM feedback in this revision.\n'
     'GP11 and GP12 are brought to pads per S1. ADC_VREF, 3V3_EN and VBUS\n'
     'are unconnected as fitted; VBUS has no buck connection.\n'
     'No GPIO carries a pullup to any rail but switched 3V3.'),
    ('HOLD driver and the cutoff path',
     'GP6 HOLD_RAW with a 47k external pulldown and the JH MAINTENANCE\n'
     'link. Firmware latches it LOW before output enable; 4 mA drive,\n'
     '2.6 V loaded qualification target.\n'
     'QS is the series interruption the independent timer uses: drain to\n'
     'SINK, source to the QH collector, body diode blocking the sink\n'
     'direction when off. QI remains wired straight to SINK, so raw\n'
     'ignition still overrides everything. QMON senses HOLD_RAW ahead of\n'
     'JH, so opening JH releases QH without blinding the monitor.\n'
     'JH, R_EXPP/R_EXPT and the accelerated 64 s tap are three different\n'
     'things and are labelled as such: JH is maintenance, R_EXPP is the\n'
     'production 2048 s selection, R_EXPT is the bench test selection and\n'
     'is DNP. Fit exactly one of R_EXPP and R_EXPT: they are two counter\n'
     'outputs and must never be shorted together.'),
    ('SD and expansion',
     'SPI0 at 12 MHz on switched 3V3 only (GP16 MISO, GP17 CS, GP18 SCK,\n'
     'GP19 MOSI). D6 bulk is now a selected 47 uF: a 200 mA write spike for\n'
     '1 ms inside 100 mV of droop needs 2 uF, so this is an order of\n'
     'margin without an oversized can. Any move of this module to a 5 V\n'
     'rail re-opens the MISO clearance gate of AS_BUILT S3.5.\n'
     'J3 is a passive expansion header for a DNP daughterboard. There is\n'
     'no transceiver, bias or termination on this board, which is why no\n'
     'off-state current claim is needed. A daughterboard may take power\n'
     'only from J3.1 (B5) or J3.3 (switched 3V3), both switched; an\n'
     'externally powered adapter on this header breaks the off-state\n'
     'contract. No bus interoperability is claimed.\n'
     'J4 is the RUN-to-GND reset pair and nothing else.'),
    ('Onboard switched power',
     'Reuses the existing power candidate as DESIGN.md S3 lists it\n'
     '(D-POWER-02), with the reviewed deltas D7 and D13 and the LRA-02\n'
     'component selections. The LM2678, its TVS role, bulk capacitors,\n'
     'boost cap, inductor value and both Schottky positions all have\n'
     'in-service precedent on the keyless board in this car (D-POWER-03);\n'
     'the logger adds QP, QI/QH, DZ, DOR, the A5 rail and MAX_ON.\n'
     'Rail nets: P12 always-on, P_AON the clamped A5 feed, A5 always-on 5 V,\n'
     'VCLK the filtered oscillator rail, VIN_SW switched, B5 buck output,\n'
     'VSYS through DOR, P3V3_SW from the Pico regulator.\n'
     'RGS is 10k, not the 100k of DESIGN.md S3: the MAX_ON revision needs\n'
     'it so that the 0.2 V off-gate limit allows 19.80 uA of total sink\n'
     'leakage instead of 2 uA.\n'
     'QP body diode is drain-to-source: it blocks P12 to VIN_SW when off\n'
     'but does not block reverse energy, so USB backfeed testing has to\n'
     'cover VIN_SW as well as B5. The DPAK tab is DRAIN and carries\n'
     'switched battery voltage - a clearance and thermal item for layout.\n'
     'For every diode, check the NET rather than the footprint name.'),
    ('Independent cutoff - what it does and does not cover',
     'Nominal 2048 s from qualified ignition loss, on its own always-on\n'
     'supply and its own clock. The Pico cannot refresh it with HOLD,\n'
     'resets, network traffic or watchdog servicing; releasing HOLD disarms\n'
     'it, and only a qualified ignition assertion can grant it again.\n'
     'Reset dominates set in the settled Boolean model. UCOUNT is reset by\n'
     'BAD OR IGN_Q and deliberately NOT by NARM, which would erase EXPIRED\n'
     'as it disarmed the latch; instead the clock stops when disarmed.\n'
     'Not covered, and stated here so nobody reads more into it: a stopped\n'
     'clock, failed timer logic, a shorted QS or QP, an ignition line stuck\n'
     'high, repeated raw pulses that energize QI, or external backfeed. A5\n'
     'faults can remove power before the deadline. No SD integrity claim\n'
     'survives a forced cutoff.\n'
     'Every unused CMOS input is tied to a rail (ULATCH 12 and 13 to\n'
     'ground) and every package has its own 100 nF across its own supply\n'
     'pins - both are layout requirements as much as BOM lines.'),
    ('Test points and ground loops',
     'Twenty-five test loops. Three separate ground loops follow the\n'
     'keyless pattern: buck, Pico and harness end, the last on the bonded\n'
     'B16/AGND sense node. J4 shorts RUN to GND for a reset without\n'
     'cutting power.\n'
     'TP_PAON is where the <=28 V protected-rail criterion is measured.\n'
     'TP_GATE against TP_P12 is where the QP -14 to +1 V gate acceptance\n'
     'band is measured. TP_CLK32 carries the clock frequency and startup\n'
     'measurements the whole 2048 s arithmetic rests on.\n'
     'Current-sensitive nodes must be measurable without the instrument\n'
     'supplying the current being measured, and probes must be removable\n'
     'for the final leakage reading - a layout requirement, not only a\n'
     'procedure.'),
    ('What is still open - none of it a layout blocker',
     'Classified in full in LRA12_HANDOFF.md. In short:\n'
     'ORDER GATE   ASSR-601JV availability (fallback AQY221N2S specified,\n'
     '             strictly smaller, same keepout); exact fuse family and\n'
     '             curve; capacitor approval-sheet bias/aging/IR data.\n'
     'BRING-UP     A5 ground current below 100 uA load; hot leakage of QP,\n'
     '             QI, QH, QMON, QS, QREPORT and the opto; clock startup\n'
     '             and loaded ramps; opto ON/OFF endpoints; ASSR turn-on\n'
     '             against a 55k rather than the specified 20k test load;\n'
     '             assembled rail decay with the larger COUT; LM2678 loop\n'
     '             stability with the selected output capacitor.\n'
     'VEHICLE      sustained-overvoltage and jump-start exposure; load\n'
     '             dump; harness impedance and fuse clearing; long-duration\n'
     '             hot and cold operation.\n'
     'FIRMWARE     ISO_EN sequencing contract - assert and wait 20 ms before\n'
     '             trusting VSS edges, deassert and wait 5 ms before\n'
     '             releasing HOLD; GP5 now means hardware-qualified\n'
     '             ignition; the 1770/1800/1801 s policy is unchanged.\n'
     'Nothing here is frozen, ordered or fabricated. A complete, routable\n'
     'design is not an approved board.'),
]
NOTE_X = 845.82
sh.rect(840.74, 20.32, 1176.02, 833.12, dash=False, width=0.3)
sh.text('NOTES  -  LRA-12 electrical closure', NOTE_X, 21.59, size=2.8,
        bold=True)
ny = 30.48
for heading, body in NOTES:
    sh.text(heading, NOTE_X, ny, size=2.2, bold=True)
    ny += 5.08
    sh.text(body, NOTE_X, ny, size=1.8)
    ny += 2.54 * (body.count('\n') + 1) + 4.0

sh.write(OUTDIR + '/accord-logger.kicad_sch')
print('schematic:', OUTDIR + '/accord-logger.kicad_sch')

# ----------------------------------------------------------------- BOM.csv
rows = []
for p in P:
    if not p['bom']:
        continue
    rows.append(dict(
        reference=p['ref'], source_designator=p['srcref'],
        value=p['value'], symbol=p['lib_id'],
        manufacturer_part_or_type=p['mpn'],
        footprint=p['fp'] or '(none assigned)',
        population='DNP' if p['dnp'] else 'FIT',
        status=p['status'], source=p['source'], notes=p['note']))
with open(OUTDIR + '/BOM.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print('bom:', OUTDIR + '/BOM.csv', len(rows), 'rows')
nofp = [r['reference'] for r in rows if r['footprint'] == '(none assigned)']
print('parts without a footprint:', nofp or 'none')
