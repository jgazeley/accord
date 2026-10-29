"""Generate the Rev A logger schematic and its BOM from one parts table.

Sources, and nothing else (LRA-06 packet, "Minimum context"):
  REV_A_INTERFACES.md  S1 pin map, S4 grounds, S5 connectors/test points,
                       S7 deltas D1-D15, S3.4 for the D4 requirement
  AS_BUILT.md          S2 circuit matrix, S3.4/S3.4a ignition, S3.5 SD
  power/DESIGN.md      S3 component-level connection list, with BOM.csv
  keyless/validation/kicad-20261027/README.md   validation method

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
FP_R = 'Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal'
FP_R_HALFW = 'Resistor_THT:R_Axial_DIN0414_L11.9mm_D4.5mm_P15.24mm_Horizontal'
FP_C_DISC = 'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm'
FP_DO41 = 'Diode_THT:D_DO-41_SOD81_P7.62mm_Horizontal'
FP_DO35 = 'Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal'
FP_DO201 = 'Diode_THT:D_DO-201AD_P12.70mm_Horizontal'
FP_TP = 'TestPoint:TestPoint_Loop_D2.50mm_Drill1.0mm'
FP_HDR2 = 'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical'
FP_HDR4 = 'Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical'
FP_HDR6 = 'Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical'
FP_FUSE = ('Fuse:Fuseholder_Clip-5x20mm_Bel_FC-203-22_Lateral'
           '_P17.80x5.00mm_D1.17mm_Horizontal')

# Why a part carries no footprint. Acceptance allows assigned-or-explained.
NOFP_CONN = ('connector family not selected; envelope and harness unknown '
             '(U-11), REV_A_INTERFACES S5.2')
NOFP_PLACE = 'placeholder: no part selected by LRA-06'

P = []          # placed parts, in BOM order


def part(ref, lib_id, value, x, y, nets=None, rot=0, fp='', nc=(),
         status='', source='', note='', bom=True, mpn='', hide_value=False):
    P.append(dict(ref=ref, lib_id=lib_id, value=value, x=x, y=y, rot=rot,
                  nets=nets or {}, fp=fp, nc=tuple(nc), status=status,
                  source=source, note=note, bom=bom, mpn=mpn,
                  hide_value=hide_value))


# ======================================================== vehicle input cells
# J2 is the 8-way cluster harness connector of REV_A_INTERFACES S5.1: the six
# recorded taps plus the two spare contacts that section asks for.
part('J2', 'Connector_Generic:Conn_01x08', 'Cluster harness 8-way',
     40.64, 48.26, rot=180, fp='', nc=(7, 8),
     nets={1: 'B2_TAP', 2: 'B1_TAP', 3: 'C14_TAP', 4: 'C11_TAP',
           5: 'B11_TAP', 6: 'B16'},
     status='PART_SELECTION_OPEN', source='REV_A_INTERFACES S5.1',
     note=NOFP_CONN + '; pins 7-8 are the two spare contacts, unconnected')

# AS_BUILT S2 rows 1-5a. Ratios, clamps and the fitted ADC protection are
# carried forward with no value changed; D4 adds the isolation placeholder.
# D-OFFSTATE-01, owner measurement October 29: of the five vehicle branches
# only B2 is energized with the key out. All five placeholder positions stay;
# B2's carries the measured requirement, the other four are under analog review
# with the parked-drain justification withdrawn.
ISO_REQ = ('Custom:PLACEHOLDER_SIGNAL_ISO_REQ', 'SIGNAL_ISOLATION (required)',
           'REQUIRED_BEFORE_INTEGRATION',
           'required on measured evidence (D-OFFSTATE-01, as corrected): key '
           'out, B2 reads 4.140 V loaded against 4.669 V open-circuit and '
           'draws 134-141 uA, of which 99-110 uA is back-fed into the Pico\'s '
           'unpowered 3V3 rail through a forward-biased clamp measured at '
           '0.883 V on the clamp cathodes. One branch alone exceeds the 100 uA '
           'whole-system parked budget, against an 8/20 uA allocation for all '
           'five. This is not only a current budget: the branch partially '
           'energizes a board that is meant to be off. ' + NOFP_PLACE)
ISO_REVIEW = ('Custom:PLACEHOLDER_SIGNAL_ISO_REVIEW',
              'SIGNAL_ISOLATION (under review)',
              'REQUIRED_BEFORE_INTEGRATION_UNDER_REVIEW',
              'position retained, parked-drain justification withdrawn: this '
              'branch measures 0 V or was already recorded dead with the key '
              'out (D-OFFSTATE-01). Whether a fault or transient reason keeps '
              'it is the analog reviewer\'s call. ' + NOFP_PLACE)
ISO = {'VSS': ISO_REQ}


def iso_part(key, Y, tap, iso):
    lib_id, value, status, note = ISO.get(key, ISO_REVIEW)
    part(f'XISO_{key}', lib_id, value, 109.22, Y, nets={1: tap, 2: iso}, fp='',
         status=status, source='REV_A_INTERFACES D4/S3.4, D-OFFSTATE-01',
         note=note)


DIG = [
    # key, label, Y, Rtop, Rbot, tap, iso, sig, gpio-net, matrix row
    ('VSS',  'B2 vehicle speed', 93.98,  '22k', '33k',  'B2_TAP',  'B2_ISO',  'VSS_IN'),
    ('TACH', 'B1 tachometer',   172.72,  '22k', '6.8k', 'B1_TAP',  'B1_ISO',  'TACH_IN'),
    ('BRK',  'C14 brake warning', 251.46, '22k', '6.8k', 'C14_TAP', 'C14_ISO', 'BRAKE_IN'),
]
for key, desc, Y, rt, rb, tap, iso, sig in DIG:
    iso_part(key, Y, tap, iso)
    part(f'R_{key}_T', 'Device:R', rt, 162.56, Y, nets={1: iso, 2: sig},
         fp=FP_R, status='VERIFY_STOCK', source='AS_BUILT S2',
         note='fitted divider top, value unchanged')
    part(f'R_{key}_B', 'Device:R', rb, 203.2, Y, nets={1: sig, 2: 'PGND'},
         fp=FP_R, status='VERIFY_STOCK', source='AS_BUILT S2',
         note='fitted divider bottom, value unchanged')
    part(f'D_{key}', 'Diode:1N5819', '1N5819', 248.92, Y, rot=180,
         nets={2: sig, 1: 'P3V3_SW'}, fp=FP_DO41, mpn='Chanzon 1N5819',
         status='VERIFY_STOCK', source='AS_BUILT S2/S3.4a',
         note='fitted clamp, anode at the pin, cathode to switched 3V3')

ADC = [
    ('FUEL', 'C11 fuel sender', 330.2, '7.5k', '4.7k', 'C11_TAP', 'C11_ISO',
     'FUEL_DIV', 'FUEL_ADC'),
    ('SUP', 'B11 cluster supply', 408.94, '22k', '4.7k', 'B11_TAP', 'B11_ISO',
     'SUPPLY_DIV', 'SUPPLY_ADC'),
]
for key, desc, Y, rt, rb, tap, iso, div, adc in ADC:
    iso_part(key, Y, tap, iso)
    part(f'R_{key}_T', 'Device:R', rt, 162.56, Y, nets={1: iso, 2: div},
         fp=FP_R, status='VERIFY_STOCK', source='AS_BUILT S2',
         note='fitted divider top, value unchanged')
    part(f'R_{key}_B', 'Device:R', rb, 203.2, Y, nets={1: div, 2: 'AGND'},
         fp=FP_R, status='VERIFY_STOCK', source='AS_BUILT S2/S3.3',
         note='fitted divider bottom; returns to the single B16 sense node')
    part(f'R_{key}_S', 'Device:R', '1k', 287.02, Y, rot=90,
         nets={1: div, 2: adc}, fp=FP_R, status='VERIFY_STOCK',
         source='AS_BUILT S2 rows 4a/5a', note='fitted series resistor at the pin')
    part(f'C_{key}', 'Device:C', '1uF', 312.42, Y, nets={1: adc, 2: 'AGND'},
         fp=FP_C_DISC, status='VERIFY_OR_SOURCE',
         source='AS_BUILT S2 rows 4a/5a',
         note='fitted filter capacitor; exact dielectric/rating not recorded')
    part(f'D_{key}_H', 'Diode:1N5819', '1N5819', 337.82, Y - 10.16, rot=180,
         nets={2: adc, 1: 'P3V3_SW'}, fp=FP_DO41, mpn='Chanzon 1N5819',
         status='VERIFY_STOCK', source='AS_BUILT S2 rows 4a/5a',
         note='fitted upper clamp')
    part(f'D_{key}_L', 'Diode:1N5819', '1N5819', 337.82, Y + 10.16,
         nets={1: adc, 2: 'AGND'}, fp=FP_DO41, mpn='Chanzon 1N5819',
         status='VERIFY_STOCK', source='AS_BUILT S2 rows 4a/5a',
         note='fitted lower clamp')

# ================================================================= Pico W
PICO_NC = (1, 2, 10, 11, 12, 14, 17, 19, 20, 26, 27, 29, 34, 35, 37, 40)
part('U1', 'MCU_Module:RaspberryPi_Pico_W', 'RaspberryPi_Pico_W',
     431.8, 101.6, fp='Module:RaspberryPi_Pico_W_SMD_HandSolder',
     nc=PICO_NC, mpn='Raspberry Pi Pico W (RP2040 + CYW43439)',
     status='FITTED', source='REV_A_INTERFACES S1',
     note='fitted module; Rev A column of the pin map',
     nets={4: 'VSS_IN', 5: 'TACH_IN', 6: 'BRAKE_IN', 7: 'QUAL_N_REPORT',
           9: 'HOLD_RAW', 15: 'SPARE_GP11', 16: 'SPARE_GP12',
           21: 'SD_MISO', 22: 'SD_CS', 24: 'SD_SCK', 25: 'SD_MOSI',
           30: 'RUN', 31: 'FUEL_ADC', 32: 'SUPPLY_ADC', 33: 'AGND',
           36: 'P3V3_SW', 39: 'VSYS', 3: 'PGND'})

# ====================================================== ignition / opto cell
# AS_BUILT S3.4: B11 -> 1N5819 -> 2.2k -> LED anode, LED cathode -> B16;
# collector/emitter with the fitted 100 nF across the output.
part('FIGN', 'Device:Fuse', '100mA', 60.96, 490.22, rot=90,
     nets={1: 'B11_TAP', 2: 'IGN_FUSED'}, fp=FP_FUSE,
     status='PART_SELECTION_OPEN', source='DESIGN.md S3 / AS_BUILT S2 row 6',
     note='ignition-sense fuse; REV_A_INTERFACES S5.1 places per-branch fuses '
          'at the tap end, DESIGN.md S3 places this one on the board - '
          'see CAPTURE_NOTES question Q4')
part('DI', 'Diode:1N5819', '1N5819', 99.06, 490.22, rot=180,
     nets={2: 'IGN_FUSED', 1: 'IGN_POS'}, fp=FP_DO41, mpn='Chanzon 1N5819',
     status='VERIFY_STOCK', source='AS_BUILT S2 row 6 / S3.4',
     note='fitted series diode; owner reported 1N5819, not the 1N4148 of '
          'DESIGN.md S3')
part('RLED', 'Device:R', '2.2k', 139.7, 490.22, rot=90,
     nets={1: 'IGN_POS', 2: 'IGN_LED_A'}, fp=FP_R_HALFW,
     status='VERIFY_STOCK', source='AS_BUILT S3.4a, measured 2026-10-29',
     note='measured 2.2k carried forward (D15); replaces the 1k of the power '
          'BOM, whose 28 V upper sizing exceeds a 0.5 W rating. Fitted wattage '
          'rating is not recorded')
part('DR', 'Diode:1N4148', '1N4148', 177.8, 500.38, rot=270,
     nets={1: 'IGN_LED_A', 2: 'PGND'}, fp=FP_DO35, mpn='Vishay 1N4148-TAP',
     status='MISSING', source='DESIGN.md S3',
     note='LED reverse clamp from the power candidate; not in the fitted cell')
part('U2', 'Isolator:PC817', 'PC817', 228.6, 490.22,
     nets={1: 'IGN_LED_A', 2: 'B16', 4: 'IGN_N', 3: 'PGND'},
     fp='Package_DIP:DIP-4_W7.62mm', mpn='Sharp PC817XNNSZ1B or qualified equiv',
     status='VERIFY_STOCK', source='AS_BUILT S2 rows 6-7 / S3.4',
     note='fitted PC817-class part, identity and hot CTR unproved. LED cathode '
          'returns to B16 as fitted, not to PGND as in DESIGN.md S3 - see '
          'CAPTURE_NOTES question Q2')
part('C_IGN', 'Device:C', '100nF', 266.7, 490.22,
     nets={1: 'IGN_N', 2: 'PGND'}, fp=FP_C_DISC,
     status='VERIFY_OR_SOURCE', source='AS_BUILT S2 row 7 / S3.4',
     note='fitted capacitor across the opto output; retention and report-node '
          'timing are conditional under D1')
part('XQUAL', 'Custom:PLACEHOLDER_IGN_QUAL', 'IGN_QUALIFICATION',
     320.04, 490.22, fp='',
     nets={1: 'IGN_N', 2: 'A5', 3: 'PGND', 4: 'QUAL_N_REPORT'},
     status='REQUIRED_BEFORE_INTEGRATION', source='REV_A_INTERFACES S1 (D1)',
     note=NOFP_PLACE + '; the A5-domain stage that drains GP5 in Rev A - see '
          'CAPTURE_NOTES question Q1')
part('RIGN', 'Device:R', '10k', 320.04, 530.86,
     nets={1: 'P3V3_SW', 2: 'QUAL_N_REPORT'}, fp=FP_R,
     status='VERIFY_STOCK', source='REV_A_INTERFACES S1 / DESIGN.md S3',
     note='GP5 report-node pull-up to switched 3V3 (D1)')

# ======================================================== HOLD driver (D2)
part('RPD', 'Device:R', '47k', 396.24, 251.46,
     nets={1: 'HOLD_RAW', 2: 'PGND'}, fp=FP_R, status='VERIFY_STOCK',
     source='REV_A_INTERFACES D2 / DESIGN.md S3',
     note='external GP6 pulldown; holds the driver off before output enable')
part('JH', 'Jumper:Jumper_2_Open', 'HOLD link', 441.96, 238.76,
     nets={1: 'HOLD_RAW', 2: 'HOLD_JH'}, fp=FP_HDR2,
     status='VERIFY_OR_SOURCE', source='DESIGN.md S3 / REV_A_INTERFACES S5.3',
     note='open for USB maintenance; RH and RBH stay on the driver side')
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
part('C_SD', 'Device:C_Polarized', '10-100uF', 474.98, 381,
     nets={1: 'P3V3_SW', 2: 'PGND'}, fp='Capacitor_THT:CP_Radial_D6.3mm_P2.50mm',
     status='PART_SELECTION_OPEN', source='REV_A_INTERFACES D6 / AS_BUILT S3.5',
     note='D6 bulk at the SD supply, confirmed absent 2026-10-29. D6 states a '
          '10-100 uF range; no single value is selected here')

# ===================================================== J3 bus, J4 service
part('J3', 'Connector_Generic:Conn_01x06', 'Bus / expansion (unpopulated)',
     403.86, 492.76, rot=180, fp=FP_HDR6, nc=(1, 2, 3, 4, 5, 6),
     status='REQUIRED_BEFORE_INTEGRATION', source='REV_A_INTERFACES S5.1',
     note='unpopulated: LRA-04 returned with revisions required and selected '
          'no bus. All pins unconnected; GP8/GP9/GP10 stay unconnected on U1. '
          'The contact count is provisional - see CAPTURE_NOTES question Q3')
part('J4', 'Connector_Generic:Conn_01x04', 'Service 4-way',
     403.86, 541.02, rot=180, fp=FP_HDR4, nc=(3, 4),
     nets={1: 'RUN', 2: 'PGND'},
     status='VERIFY_OR_SOURCE', source='REV_A_INTERFACES S5.1',
     note='RUN-to-GND reset pair. Pins 3-4 are reserved for the UART0 service '
          'pair of S5.1 but are left unconnected because GP0/GP1 must stay '
          'free - see CAPTURE_NOTES question Q5. Must be power-off-safe: no '
          'externally powered pull-up into an off GPIO')
part('JR', 'Jumper:Jumper_2_Open', 'RUN reset link', 474.98, 530.86,
     nets={1: 'RUN', 2: 'PGND'}, fp=FP_HDR2,
     status='VERIFY_OR_SOURCE', source='LRA-06 packet convention table',
     note='shorting jumper for a reset without cutting power, following the '
          'keyless J7 pattern')

# ============================================== onboard power (DESIGN.md S3)
part('J1', 'Connector_Generic:Conn_01x02', 'Power 2-way',
     546.1, 48.26, rot=180, fp='', nets={1: 'BATT_IN', 2: 'PGND'},
     status='PART_SELECTION_OPEN', source='REV_A_INTERFACES S5.1 / DESIGN.md S3',
     note=NOFP_CONN + '; protected +12 V from the auxiliary battery and its return')
part('F1', 'Device:Fuse', '1A', 584.2, 48.26, rot=90,
     nets={1: 'BATT_IN', 2: 'BATT_F'}, fp=FP_FUSE,
     status='PART_SELECTION_OPEN', source='DESIGN.md S3',
     note='bench branch fuse; DC interrupt rating, curve and wire size open')
part('DREV', 'Device:D_Schottky', 'SB360-E3/54', 622.3, 48.26, rot=180,
     nets={2: 'BATT_F', 1: 'P12'}, fp=FP_DO201, mpn='Vishay SB360-E3/54',
     status='MISSING_OR_VERIFY_SPARE', source='DESIGN.md S3',
     note='input reverse-blocking diode; no part borrowed from the live keyless board')
part('TVS', 'Device:D_TVS', '1.5KE30A-E3/54', 660.4, 68.58, rot=90,
     nets={2: 'P12', 1: 'PGND'}, fp=FP_DO201, mpn='Vishay 1.5KE30A-E3/54',
     status='CANDIDATE_NOT_VEHICLE_APPROVED', source='DESIGN.md S3',
     note='inherited protection candidate only; energy and voltage coordination '
          'open (R02). Check the cathode net, not the footprint orientation - '
          'the keyless TVS reversal history makes that essential')
part('C0', 'Device:C', '100nF/63V', 685.8, 68.58,
     nets={1: 'P12', 2: 'PGND'}, fp=FP_C_DISC, status='VERIFY_OR_SOURCE',
     source='DESIGN.md S3', note='always-on input ceramic')
part('XVP', 'Custom:PLACEHOLDER_VEHICLE_PROT', 'VEHICLE_PROTECTION',
     731.52, 55.88, fp='', nets={1: 'P12', 2: 'PGND'},
     status='REQUIRED_BEFORE_VEHICLE_USE', source='power/BOM.csv',
     note=NOFP_PLACE + '; coordinated input/IGN protection and fault limiting. '
          'The reference keyless stage is not logger qualification')
part('RGS', 'Device:R', '100k', 546.1, 109.22,
     nets={1: 'P12', 2: 'GATE'}, fp=FP_R, status='VERIFY_STOCK',
     source='DESIGN.md S3', note='gate-source pull-up, keeps QP off at rest')
part('DZ', 'Device:D_Zener', 'BZX55C12', 546.1, 139.7, rot=270,
     nets={1: 'P12', 2: 'GATE'}, fp=FP_DO35, mpn='Vishay BZX55C12-TAP',
     status='MISSING', source='DESIGN.md S3',
     note='12 V gate-source clamp; do not substitute a low-voltage kit zener '
          'without recalculating gate enhancement')
part('RG', 'Device:R', '1k', 546.1, 177.8,
     nets={1: 'GATE', 2: 'SINK'}, fp=FP_R_HALFW, status='VERIFY_STOCK',
     source='DESIGN.md S3', note='gate sink resistor, 0.5 W position')
part('QP', 'Transistor_FET:IRF4905', 'IRF4905PbF', 584.2, 109.22,
     nets={1: 'GATE', 2: 'VIN_SW', 3: 'P12'},
     fp='Package_TO_SOT_THT:TO-220-3_Vertical', mpn='Infineon IRF4905PbF',
     status='MISSING', source='DESIGN.md S3',
     note='first bench switch; automotive selection not frozen. Body diode is '
          'drain-to-source: it blocks P12 to VIN_SW when off but not reverse energy')
part('RI', 'Device:R', '2.2k', 571.5, 203.2, rot=90,
     nets={1: 'IGN_POS', 2: 'IGN_B'}, fp=FP_R, status='VERIFY_STOCK',
     source='DESIGN.md S3', note='IGN transistor base drive')
part('RBI', 'Device:R', '100k', 584.2, 231.14,
     nets={1: 'IGN_B', 2: 'PGND'}, fp=FP_R, status='VERIFY_STOCK',
     source='DESIGN.md S3', note='QI base-emitter pulldown')
part('QI', 'Transistor_BJT:2N3904', '2N3904', 609.6, 203.2,
     nets={1: 'PGND', 2: 'IGN_B', 3: 'SINK'},
     fp='Package_TO_SOT_THT:TO-92_Inline', mpn='onsemi 2N3904',
     status='VERIFY_STOCK', source='DESIGN.md S3',
     note='direct ignition start path. Bench 12-16 V only; a higher-voltage '
          'replacement is needed before the vehicle transient envelope')
part('RBH', 'Device:R', '100k', 660.4, 231.14,
     nets={1: 'HOLD_B', 2: 'PGND'}, fp=FP_R, status='VERIFY_STOCK',
     source='DESIGN.md S3', note='QH base-emitter pulldown; stays fitted when JH is open')
part('QH', 'Transistor_BJT:2N3904', '2N3904', 685.8, 203.2,
     nets={1: 'PGND', 2: 'HOLD_B', 3: 'SINK'},
     fp='Package_TO_SOT_THT:TO-92_Inline', mpn='onsemi 2N3904',
     status='VERIFY_STOCK', source='DESIGN.md S3 / D2',
     note='firmware HOLD path. Bench 12-16 V only')
part('CIN', 'Device:C_Polarized', '100uF/50V', 635, 109.22,
     nets={1: 'VIN_SW', 2: 'PGND'}, fp='Capacitor_THT:CP_Radial_D10.0mm_P5.00mm',
     status='PART_SELECTION_OPEN', source='DESIGN.md S3',
     note='switched-input bulk; exact series, ESR and ripple rating open')
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
     source='DESIGN.md S3',
     note='symbol copied from keyless/hardware/Custom.kicad_sym per the packet. '
          'Pin 7 ON/OFF left open and pin 5 NC unconnected, as DESIGN.md S3 '
          'specifies. Do not remove the installed keyless regulator')
part('CBOOST', 'Device:C', '10nF/50V', 797.56, 127, rot=90,
     nets={1: 'SW', 2: 'BOOST'}, fp=FP_C_DISC, status='VERIFY_OR_SOURCE',
     source='DESIGN.md S3', note='between SW and BOOST; keep short')
part('DCATCH', 'Device:D_Schottky', 'SB360-E3/54', 716.28, 190.5, rot=270,
     nets={1: 'SW', 2: 'PGND'}, fp=FP_DO201, mpn='Vishay SB360-E3/54',
     status='MISSING_OR_VERIFY_SPARE', source='DESIGN.md S3',
     note='catch diode; local loop with CIN is a layout requirement (LRA-08)')
part('L1', 'Device:L', '22uH', 754.38, 190.5, rot=90,
     nets={1: 'SW', 2: 'B5'},
     fp='Inductor_THT:L_Radial_D8.7mm_P5.00mm_Fastron_07HCP',
     mpn='Bourns RLB0912-220KL', status='MISSING', source='DESIGN.md S3',
     note='normal-load margin only; the LM2678 fault limit exceeds its '
          '2.5 A saturation rating')
part('RB5', 'Device:R', '1k', 749.3, 215.9,
     nets={1: 'B5', 2: 'PGND'}, fp=FP_R, status='VERIFY_STOCK',
     source='DESIGN.md S3', note='B5 bleeder; supports the B07 decay measurement')
part('COB', 'Device:C', '100nF/50V', 774.7, 215.9,
     nets={1: 'B5', 2: 'PGND'}, fp=FP_C_DISC, status='VERIFY_OR_SOURCE',
     source='DESIGN.md S3', note='B5 local bypass')
part('COUT', 'Device:C_Polarized', '820uF/16V', 800.1, 215.9,
     nets={1: 'B5', 2: 'PGND'}, fp='Capacitor_THT:CP_Radial_D12.5mm_P5.00mm',
     status='PART_SELECTION_OPEN', source='DESIGN.md S3',
     note='820 uF is a starting value, not a complete capacitor specification; '
          'low ESR must be characterised for the LM2678')
part('DOR', 'Diode:1N4004', '1N4004-E3/54', 754.38, 248.92, rot=180,
     nets={2: 'B5', 1: 'VSYS'}, fp=FP_DO41, mpn='Vishay 1N4004-E3/54',
     status='MISSING', source='REV_A_INTERFACES D13',
     note='D13 replaces the power BOM 1N5819 with the 1N4004 candidate for its '
          'specified reverse-current maxima; B5 anode to VSYS cathode. Blocks '
          'USB back into B5 apart from leakage')

# MAX_ON: an unimplemented block, captured so layout cannot lose its interface.
part('XMAXON', 'Custom:PLACEHOLDER_MAX_ON', 'MAX_ON', 660.4, 416.56, fp='',
     nets={1: 'P12', 2: 'HOLD_RAW', 3: 'PGND', 4: 'A5', 5: 'VCLK',
           6: 'PGOOD', 7: 'ARM', 8: 'EXPIRED', 9: 'HOLD_N'},
     status='REQUIRED_BEFORE_UNATTENDED_USE', source='power/BOM.csv',
     note=NOFP_PLACE + '; independent 32-40 min timer plus latched HOLD-path '
          'inhibit, not implemented in revision A. HOLD_N is brought only to '
          'its test point: this capture does not insert the inhibit into the '
          'HOLD path - see CAPTURE_NOTES question Q6')

# ======================================================= test points (S5.3)
TPS1 = [('TP_P12', 'P12'), ('TP_GATE', 'GATE'), ('TP_VINSW', 'VIN_SW'),
        ('TP_SW', 'SW'), ('TP_B5', 'B5'), ('TP_VSYS', 'VSYS'),
        ('TP_3V3', 'P3V3_SW'), ('TP_A5', 'A5'), ('TP_VCLK', 'VCLK'),
        ('TP_QUALN', 'QUAL_N_REPORT')]
TPS2 = [('TP_ARM', 'ARM'), ('TP_EXPIRED', 'EXPIRED'), ('TP_PGOOD', 'PGOOD'),
        ('TP_HOLDN', 'HOLD_N'), ('TP_HOLD', 'HOLD_RAW'),
        ('TP_GND_BUCK', 'PGND'), ('TP_GND_PICO', 'PGND'),
        ('TP_GND_HARNESS', 'AGND'), ('TP_GP11', 'SPARE_GP11'),
        ('TP_GP12', 'SPARE_GP12')]
TP_NOTE = {
    'TP_ARM': 'A5-domain cutoff logic; no GPIO connection',
    'TP_EXPIRED': 'A5-domain cutoff logic; no GPIO connection',
    'TP_PGOOD': 'A5-domain cutoff logic; no GPIO connection',
    'TP_HOLDN': 'A5-domain cutoff logic; no GPIO connection',
    'TP_GND_BUCK': 'buck return loop',
    'TP_GND_PICO': 'Pico return loop',
    'TP_GND_HARNESS': 'harness-end loop on the B16 sense node - see Q7',
    'TP_GP11': 'unassigned GPIO brought to a pad (S1)',
    'TP_GP12': 'unassigned GPIO brought to a pad (S1)',
    'TP_GATE': 'from the power BOM TP row, additional to S5.3',
    'TP_SW': 'from the power BOM TP row, additional to S5.3',
}
for row, Y in ((TPS1, 520.7), (TPS2, 556.26)):
    for i, (ref, net) in enumerate(row):
        part(ref, 'Connector:TestPoint', 'TestPoint', 546.1 + i * 30.48, Y,
             nets={1: net}, fp=FP_TP, hide_value=True,
             status='VERIFY_OR_SOURCE',
             source='REV_A_INTERFACES S5.3',
             note=TP_NOTE.get(ref, 'insulated test loop'))

# Power flags: VIN_SW and VSYS reach their power-input pins through passive
# parts only, so ERC needs an explicit driver on each.
part('#FLG1', 'power:PWR_FLAG', 'PWR_FLAG', 711.2, 109.22,
     nets={1: 'VIN_SW'}, bom=False, hide_value=True)
part('#FLG2', 'power:PWR_FLAG', 'PWR_FLAG', 800.1, 248.92,
     nets={1: 'VSYS'}, bom=False, hide_value=True)

# ======================================================= annotation
# KiCad requires a reference of the form <prefix><number>; the descriptive and
# DESIGN.md S3 names are kept in a Source_designator field and the BOM so a
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
    ('Custom:LM2678T', 'U', 1),
    ('Transistor_', 'Q', 1),
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
    'Accord logger Rev A - schematic capture (LRA-06)', 'A-draft', paper='A0',
    comments=('Capture only: not frozen, not accepted, not for fabrication',
              'Claude logger-schematic, session 73d7d954-f82a-4038-8ff3-546a23fc5fa9',
              'Sources: REV_A_INTERFACES S1/S4/S5/S7, AS_BUILT S2/S3.4/S3.5, power/DESIGN.md S3',
              'Dashed blocks marked NOT SELECTED are placeholders with no part chosen'))
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
              hide_value=p['hide_value'])

# ------------------------------------------------------------- block frames
BLOCKS = [
    (17.78, 20.32, 360.68, 441.96, 'VEHICLE INPUTS  -  AS_BUILT S2, ratios and clamps unchanged'),
    (373.38, 20.32, 510.54, 200.66, 'PICO W  -  REV_A_INTERFACES S1 Rev A column'),
    (373.38, 213.36, 510.54, 320.04, 'HOLD DRIVER  -  delta D2'),
    (373.38, 332.74, 510.54, 441.96, 'SD  -  AS_BUILT S3.5, delta D6'),
    (373.38, 454.66, 510.54, 571.5, 'J3 BUS / J4 SERVICE  -  REV_A_INTERFACES S5.1'),
    (17.78, 454.66, 360.68, 571.5, 'IGNITION OPTO CELL  -  AS_BUILT S3.4, delta D1'),
    (523.24, 20.32, 828.04, 350.52, 'ONBOARD SWITCHED POWER  -  power/DESIGN.md S3, deltas D7 and D13'),
    (523.24, 363.22, 828.04, 469.9, 'MAX_ON  -  power BOM row, not implemented in revision A'),
    (523.24, 482.6, 828.04, 571.5, 'TEST POINTS AND RESET  -  REV_A_INTERFACES S5.3, delta D8'),
]
for x1, y1, x2, y2, title in BLOCKS:
    sh.rect(x1, y1, x2, y2, dash=False, width=0.3)
    sh.text(title, x1 + 2.54, y1 + 1.27, size=2.0, bold=True)

# -------------------------------------------------------------- text notes
NOTES = [
    ('Vehicle inputs',
     'Five fitted cells, carried forward with no value changed (AS_BUILT S2).\n'
     'Digital divider bottoms return to PGND; both ADC divider bottoms and the\n'
     'B16 cluster sense land on ONE common node, then Pico AGND (S4, delta D5).\n'
     'B16 must never become a power return: see the ignition note and Q2/Q7.\n'
     'Both ADC channels already carry 1k + 1uF + two 1N5819 - fitted, not new (D3 closed).'),
    ('Placeholders, and delta D4',
     'PLACEHOLDER (dashed, "?", NOT SELECTED) = a block LRA-06 captures but does\n'
     'not resolve. X1-X5 are delta D4: normally-open, power-off-safe isolation\n'
     'upstream of a divider top. Five positions, one per branch, in two states\n'
     'after the owner key-out measurement of October 29 (D-OFFSTATE-01):\n'
     '  REQUIRED  - B2 only, and on a back-feed path rather than only a drain.\n'
     '              Key out, B2 reads 4.140 V loaded against 4.669 V open-\n'
     '              circuit and draws 134-141 uA. The divider is not the only\n'
     '              load: a clamp is forward-biased, its cathodes measure\n'
     '              0.883 V to chassis, and 99-110 uA of that current is\n'
     '              back-fed into the Pico 3V3 rail while the board is off.\n'
     '              One branch alone exceeds the whole 100 uA system parked\n'
     '              budget, against 8/20 uA allocated to all five together,\n'
     '              and it partially energizes a board meant to be dead.\n'
     '              This is the one row of the S6 off-state matrix that is\n'
     '              established by measurement rather than by nothing.\n'
     '  UNDER REVIEW - B1 and C11 measure 0 V key out, and C14 and B11 were\n'
     '              already recorded dead. The parked-drain justification is\n'
     '              withdrawn for these four; whether a fault or transient\n'
     '              reason keeps them is the analog reviewer\'s call. The\n'
     '              positions are kept so neither outcome needs a redraw.\n'
     'The other standing requirement is unchanged: with the board off and the\n'
     'inputs energized, 3V3/B5 must stay <=0.3 V against about 2.78 mA of\n'
     'present injection (S3.1). No part is selected and selecting one is not\n'
     'this task: it is the analog reviewer and LRA-02. Isolation after the\n'
     'divider does not qualify; series limiting and firmware high-Z are not\n'
     'isolation.'),
    ('Ignition opto cell',
     'Fitted cell (AS_BUILT S3.4): B11 -> 1N5819 -> measured 2.2k -> LED anode;\n'
     'LED cathode returns to B16 with nothing in series; collector to the report\n'
     'path, emitter to PGND, fitted 100 nF across the output. No input capacitor.\n'
     'DESIGN.md S3 instead returns the LED to PGND and uses 1k/1N4148 - this\n'
     'capture follows the fitted cell, per the packet. Q2 raises the consequence:\n'
     'the fitted return puts 4.7-5.8 mA of LED current in B16, which S4 declares\n'
     'reference-only with no current intended.\n'
     'Rev A does not take the opto collector to GP5 (D-RA-03 forbids mixing the\n'
     'old raw-GP5 rule with the qualified proposal). GP5 is QUAL_N_REPORT, drained\n'
     'by XQUAL and pulled up by RIGN to switched 3V3. XQUAL has no component-level\n'
     'design in this task input - Q1.'),
    ('Pico W pin map',
     'GP0/GP1, GP7, GP8-GP10 and GP28 are deliberately unconnected (X markers).\n'
     'GP8-GP10 are offers to LRA-04, not reservations. ARM, EXPIRED, PGOOD and\n'
     'HOLD_N stay off the GPIOs: they are A5-domain test points only.\n'
     'GP11 and GP12 are brought to pads per S1. ADC_VREF, 3V3_EN and VBUS are\n'
     'unconnected as fitted; VBUS has no buck connection (DESIGN.md S3).'),
    ('HOLD driver',
     'GP6 HOLD_RAW with a 47k external pulldown and the JH maintenance link.\n'
     'Firmware latches it LOW before output enable; 4 mA drive, 2.6 V loaded\n'
     'qualification target. Open JH for USB maintenance - RBH stays fitted.'),
    ('SD',
     'SPI0 at 12 MHz on switched 3V3 only (GP16 MISO, GP17 CS, GP18 SCK,\n'
     'GP19 MOSI). D6 adds bulk at the SD supply: write spikes of 100-200 mA\n'
     'otherwise land directly on the Pico\'s shared ~300 mA regulator.\n'
     'Any move of this module to a 5 V rail re-opens the MISO clearance gate\n'
     'of AS_BUILT S3.5 and must not be done in layout.'),
    ('J3 bus and J4 service',
     'J3 is unpopulated with every pin unconnected: LRA-04 selected no bus and\n'
     'reserved no pin. Do not capture a transceiver here.\n'
     'J4 carries the RUN-to-GND reset pair. Its UART0 pins are present but\n'
     'unconnected (Q5). It must be power-off-safe: no externally powered\n'
     'pull-up into an off GPIO.'),
    ('Onboard switched power',
     'Reuses the existing 9527a14 power candidate exactly as DESIGN.md S3 lists\n'
     'it (D-POWER-02), with two reviewed deltas: D7 onboard switched supply and\n'
     'D13 the 1N4004 DOR. Rail nets: P12 always-on, VIN_SW switched, B5 buck\n'
     'output, VSYS through DOR, P3V3_SW from the Pico regulator.\n'
     'QP body diode is drain-to-source: it blocks P12 to VIN_SW when off but\n'
     'does not block reverse energy. For every diode, check the net rather than\n'
     'the footprint - the keyless TVS reversal history makes that essential.\n'
     'TVS and XVP are distinct: TVS is a named inherited candidate, XVP is the\n'
     'unselected VEHICLE_PROTECTION BOM row. Neither is vehicle-approved.\n'
     'Bench only: QI and QH are 2N3904 for a 12-16 V bench, and F1 assumes a\n'
     'current-limited supply. This is not a vehicle-qualified power stage.'),
    ('MAX_ON',
     'Independent maximum-on timer plus latched HOLD-path inhibit: 32-40 min\n'
     'after IGN fall, non-retriggerable by HOLD, <=40 uA room allocation.\n'
     'Not designed and not in stock record; required before unattended use.\n'
     'Its A5 and VCLK rails and its ARM/EXPIRED/PGOOD/HOLD_N status nodes are\n'
     'captured so layout cannot lose them. A5 also supplies XQUAL. HOLD_N is\n'
     'NOT inserted into the HOLD path by this capture - Q6.'),
    ('Test points and reset',
     'Test loops per S5.3, plus TP_GATE and TP_SW from the power BOM TP row.\n'
     'Three separate ground loops, following the keyless pattern: buck, Pico and\n'
     'harness end. JR shorts RUN to GND for a reset without cutting power.\n'
     'Current-sensitive nodes must be measurable without the instrument supplying\n'
     'the current being measured, and probes must be removable for the final\n'
     'leakage reading - a layout requirement (LRA-08), not only a procedure.'),
]
NOTE_X = 845.82
sh.rect(840.74, 20.32, 1176.02, 833.12, dash=False, width=0.3)
sh.text('NOTES', NOTE_X, 21.59, size=2.8, bold=True)
ny = 30.48
for heading, body in NOTES:
    sh.text(heading, NOTE_X, ny, size=2.2, bold=True)
    ny += 5.08
    sh.text(body, NOTE_X, ny, size=1.8)
    ny += 2.54 * (body.count('\n') + 1) + 5.08

sh.text('LRA-06 CAPTURE - NOT FROZEN, NOT ACCEPTED, NOT FOR FABRICATION.\n'
        'Placeholders D4 (five instances), J3, MAX_ON and VEHICLE_PROTECTION carry no\n'
        'selected part. Open questions Q1-Q7 are in validation/../CAPTURE_NOTES.md.',
        17.78, 576.58, size=2.2, bold=True)

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
        status=p['status'], source=p['source'], notes=p['note']))
with open(OUTDIR + '/BOM.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print('bom:', OUTDIR + '/BOM.csv', len(rows), 'rows')
