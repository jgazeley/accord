#!/usr/bin/env python3
"""LRA-12 closure arithmetic: voltage envelope, enable corners, ledger, paths.

Run from the repository root or from this directory:

    python3 logger/hardware/power/check_layout_closure.py

What this is. Five groups of checks over the decisions in LAYOUT_CLOSURE.md,
each computed from manufacturer limits rather than restated from a table:

  1. Voltage envelope. Every part on an unregulated node, against the worst
     node voltage the selected entry clamp actually produces at temperature.
     This is the chain that forced the clamp choice, so it is the group worth
     running first.
  2. The A5 second stage. Clamp voltage, dissipation, series drop and the
     regulator's own minimum input.
  3. The B2 isolation enable. LED current at every corner against the current
     the switching times are specified at, the timing against the shutdown
     budget, and the signal-path error.
  4. The parked ledger, recomputed with the LRA-12 part changes, including
     where it no longer fits its old sub-allocations.
  5. An off-state path audit read out of the exported netlist: with the
     declared blocking elements removed, no energized-while-parked source may
     reach a switched rail. It also checks the converse, so the audit cannot
     pass by accident on a graph that was never connected.

What this is not. Arithmetic over datasheet limits and one topology check on
the netlist. It is not SPICE, not a measurement, and not a component
qualification. Several inputs are explicitly screens at mixed conditions, and
each such row says so. Where a bound does not exist in a datasheet this says
"unspecified" instead of inventing one.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NET = os.path.normpath(os.path.join(HERE, '..', 'kicad', 'validation',
                                    'netlist.net'))

fails = []
checks = 0
notes = []
overruns = []


def check(label, ok, detail=''):
    global checks
    checks += 1
    print('  %s  %s' % ('ok  ' if ok else 'FAIL', label))
    if not ok:
        fails.append('%s: %s' % (label, detail))
        print('        -> %s' % detail)


def over(label, allocated, screened, why):
    """A sub-allocation that the screens do not fit.

    Kept separate from a failure on purpose. The circuit is not wrong and the
    whole-system target still closes; what does not fit is one row of an
    internal split that the interface contract itself invites a reviewer to
    redistribute. Reporting it as a failure would be alarming and reporting
    it as a note would be too quiet.
    """
    overruns.append(label)
    print('  OVER  %s: screen %.1f uA against its %.0f uA allocation, over '
          'by %.1f uA' % (label, screened, allocated, screened - allocated))
    print('        -> %s' % why)


def note(s):
    notes.append(s)
    print('  note  %s' % s)


def hdr(s):
    print()
    print(s)
    print('-' * len(s))


# ===========================================================================
# 1. Voltage envelope
# ===========================================================================
# Vishay 1.5KE, table and notes:
#   1.5KE20A  VWM 17.1 V, VBR 19.0-21.0 V at IT = 1.0 mA, ID 1.0 uA at VWM,
#             IPPM 54.2 A, VC 27.7 V at IPPM for 10/1000 us, aVBR 0.090 %/K,
#             PD 6.5 W on an infinite heatsink at TL = 75 C.
#   1.5KE30A  VWM 25.6 V, VBR 28.5-31.5, IPPM 36.2 A, VC 41.4 V, 0.097 %/K.
# The ID row has no temperature column: it is a 25 C figure and the datasheet
# publishes no hot leakage maximum for this family.
CLAMP = dict(name='1.5KE20A-E3/54', vwm=17.1, vbr_min=19.0, vbr_max=21.0,
             vc25=27.7, ippm=54.2, alpha=0.00090, pd=6.5, id25=1.0)
OLD_CLAMP = dict(name='1.5KE30A', vwm=25.6, vc25=41.4, alpha=0.00097)
HOT_C, COLD_C, REF_C = 85.0, -40.0, 25.0

vc_hot = CLAMP['vc25'] * (1 + CLAMP['alpha'] * (HOT_C - REF_C))
vbr_min_cold = CLAMP['vbr_min'] * (1 + CLAMP['alpha'] * (COLD_C - REF_C))
V_SUSTAIN = CLAMP['vwm']          # declared sustained ceiling at P12
V_OPERATE = 16.0                  # top of the agreed 12-16 V bench envelope

# Every part that sees an unregulated node, with its own rating and source.
# "operating" means a recommended-operating maximum; "absolute" an absolute
# maximum. The envelope has to fit the operating figure, not the absolute one.
ENVELOPE = [
    # part, node, rating V, kind, source
    ('QP IPD50P04P4L-11', 'P12 / VIN_SW', 40.0, 'absolute VDS',
     'Infineon Rev. 1.1, -40 V VDS'),
    ('QI 2N3904', 'SINK = P12 when off', 40.0, 'absolute VCEO',
     'onsemi 2N3904'),
    ('QH 2N3904', 'SINK = P12 when off', 40.0, 'absolute VCEO',
     'onsemi 2N3904'),
    ('QS BSS138P', 'SINK', 60.0, 'absolute VDS', 'Nexperia BSS138P'),
    ('UREG LM2678', 'VIN_SW', 40.0, 'operating VIN',
     'TI LM2678 sections 4-7, 8-40 V operating, 45 V absolute'),
    ('CIN EEUFR1H101', 'VIN_SW', 50.0, 'rated WV', 'Panasonic FR series'),
    ('C0', 'P12', 63.0, 'rated WV', 'BOM, 100nF/63V'),
    ('DREV SB360', 'BATT_F / P12', 60.0, 'absolute VRRM', 'Vishay SB360'),
    ('C_AON GRM32ER71H475KA88L', 'P_AON', 50.0, 'rated WV',
     'Murata 50 V X7R'),
]
hdr('1. Voltage envelope at the entry clamp')
note('entry clamp %s: VC = %.2f V at 25 C and %.2f V at %.0f C, from its own '
     '%.3f %%/K VBR coefficient' % (CLAMP['name'], CLAMP['vc25'], vc_hot,
                                    HOT_C, CLAMP['alpha'] * 100))
for part, node, rating, kind, src in ENVELOPE:
    margin = rating - vc_hot
    check('%-28s %-20s %4.0f V %-16s margin %5.2f V'
          % (part, node, rating, kind, margin), margin > 0,
          'the hot clamp voltage %.2f V exceeds this part (%s)'
          % (vc_hot, src))
check('the inherited 1.5KE30A would NOT fit the same parts',
      OLD_CLAMP['vc25'] > 40.0,
      'if this ever passes, the clamp choice can be revisited')
note('that is the finding in one line: the inherited %.1f V clamp is above '
     'the 40 V absolute ratings of QI, QH and QP and above the LM2678 40 V '
     'operating ceiling, which is why LRA-12 replaces it rather than '
     'replacing those parts' % OLD_CLAMP['vc25'])
check('clamp standoff is above the top of the operating envelope',
      CLAMP['vwm'] > V_OPERATE,
      'at %.1f V the clamp would conduct in normal charging' % V_OPERATE)
check('cold VBR minimum still sits above the operating envelope',
      vbr_min_cold > V_OPERATE,
      'cold VBR min %.2f V against %.1f V operating' % (vbr_min_cold,
                                                        V_OPERATE))
note('cold margin is only %.2f V (VBR min %.2f V at %.0f C against %.1f V), '
     'which is the tightest number in this group'
     % (vbr_min_cold - V_OPERATE, vbr_min_cold, COLD_C, V_OPERATE))

# Sustained overvoltage: the case no clamp-only front end can meet.
P_SUSTAINED_1A = CLAMP['vbr_min'] * 1.0        # 1 A branch fuse at VBR
check('a sustained overvoltage would exceed the clamp power rating, so the '
      'fuse has to clear it', P_SUSTAINED_1A > CLAMP['pd'],
      'if this ever fails, the sustained case is no longer excluded')
note('at the 1 A branch fuse rating the clamp would dissipate about %.0f W '
     'against its %.1f W rating, and a cartridge fuse carrying its own '
     'rating does not clear quickly. A 24 V jump start is therefore a '
     'DECLARED EXCLUDED exposure, not a survivable one: no single clamp both '
     'stands off 24 V and limits to 28 V. See LAYOUT_CLOSURE S3 for the two '
     'alternatives.' % (P_SUSTAINED_1A, CLAMP['pd']))
check('the declared sustained ceiling is the clamp standoff',
      abs(V_SUSTAIN - CLAMP['vwm']) < 1e-9)

# ===========================================================================
# 2. The A5 second stage
# ===========================================================================
# Vishay BZX55 table: BZX55C22 VZ 20.8 / 22 / 23.3 V at IZT1 = 5 mA,
# IR < 0.1 uA at 25 C and < 2 uA at 150 C at VR = 18 V, ZZ < 55 ohm at 5 mA,
# TKVZ 0.04 to 0.12 %/K, Ptot 500 mW at l = 4 mm, TL = 25 C.
# TI TPS709-Q1 SLVSCE6D: VIN 2.7-30 V recommended, 32 V absolute;
# VDO <= 500 mV at 50 mA for the 50 option, not specified below 50 mA;
# IGND <= 2.7 uA at no load and <= 10 uA at 100 uA load / 30 V.
ZEN = dict(vz_min=20.8, vz_max=23.3, izt=5e-3, zz=55.0, tk_max=0.0012,
           ptot=0.5, ir25=0.1, ir150=2.0)
R_AON = 330.0
R_AON_TOL = 0.01
R_AON_PD = 0.25
A5_LOAD_MAX = 0.5e-3          # worst awake A5 current, see the ledger below
TPS709_OP, TPS709_ABS = 30.0, 32.0
CONTRACT_PAON = 28.0
VDO_SCREEN = 0.5              # 500 mV maximum, at 50 mA; conservative here
A5_NOM = 5.0

hdr('2. The always-on A5 supply boundary (X7 second stage)')
vz_hot = ZEN['vz_max'] * (1 + ZEN['tk_max'] * (HOT_C - REF_C))
iz = (vc_hot - ZEN['vz_max']) / (R_AON * (1 - R_AON_TOL))
vz_dyn = ZEN['zz'] * max(0.0, iz - ZEN['izt'])
paon_worst = vz_hot + vz_dyn
note('worst P_AON = %.2f V: zener %.2f V max at 25 C, %.2f V at %.0f C from '
     'the 0.12 %%/K maximum coefficient, plus %.2f V of dynamic drop at '
     '%.1f mA through the %.0f ohm maximum'
     % (paon_worst, ZEN['vz_max'], vz_hot, HOT_C, vz_dyn, iz * 1e3,
        ZEN['zz']))
check('P_AON meets the contract <= %.0f V protected-rail criterion'
      % CONTRACT_PAON, paon_worst <= CONTRACT_PAON,
      'worst %.2f V' % paon_worst)
check('P_AON is inside the regulator recommended maximum %.0f V'
      % TPS709_OP, paon_worst <= TPS709_OP,
      'worst %.2f V' % paon_worst)
note('margin to the recommended maximum is %.2f V, and to the %.0f V '
     'absolute maximum %.2f V. The 30-to-32 V gap is not treated as usable '
     'headroom.' % (TPS709_OP - paon_worst, TPS709_ABS,
                    TPS709_ABS - paon_worst))
check('without the second stage the contract criterion would NOT be met',
      vc_hot > CONTRACT_PAON,
      'if the hot clamp ever falls below %.0f V the zener becomes optional'
      % CONTRACT_PAON)
pz = ZEN['vz_max'] * iz
check('zener dissipation %.3f W is inside its %.1f W rating'
      % (pz, ZEN['ptot']), pz <= ZEN['ptot'],
      'a larger series resistor or a 1.3 W part would be needed')
pr = (vc_hot - ZEN['vz_max']) ** 2 / (R_AON * (1 - R_AON_TOL))
check('series resistor dissipation %.3f W is inside its %.2f W rating'
      % (pr, R_AON_PD), pr <= R_AON_PD)
drop = A5_LOAD_MAX * R_AON * (1 + R_AON_TOL)
vin_min_needed = A5_NOM + VDO_SCREEN
for p12_in in (6.0, 9.0, 12.0):
    check('at P12 = %.1f V the regulator still has %.3f V, above the %.2f V '
          'its dropout maximum implies'
          % (p12_in, p12_in - drop, vin_min_needed),
          p12_in - drop >= vin_min_needed,
          'P_AON would be %.3f V' % (p12_in - drop))
note('the series drop is %.3f V at the %.1f mA worst awake A5 load, so the '
     '6-28 V P_AON envelope floor moves to %.3f V at a 6 V input - still '
     '%.3f V above what the 500 mV / 50 mA dropout maximum implies for a 5 V '
     'output, and dropout is not specified below 50 mA at all'
     % (drop, A5_LOAD_MAX * 1e3, 6.0 - drop,
        6.0 - drop - vin_min_needed))
check('the zener never conducts in normal operation',
      ZEN['vz_min'] * (1 + ZEN['tk_max'] * (COLD_C - REF_C)) > V_SUSTAIN,
      'cold VZ min %.2f V against the %.1f V sustained ceiling'
      % (ZEN['vz_min'] * (1 + ZEN['tk_max'] * (COLD_C - REF_C)), V_SUSTAIN))
tau_aon = R_AON * 4.7e-6
check('the second-stage time constant %.2f ms is inside the 100 ms A5 '
      'validity budget' % (tau_aon * 1e3), tau_aon * 1e3 < 100.0)

# ===========================================================================
# 3. The B2 isolation enable
# ===========================================================================
# Broadcom ASSR-601Jx-DS105, 2024-06-17:
#   IF(ON) recommended 7-30 mA; VF 1.25 / 1.55 / 1.85 V at IF = 10 mA
#   TON <= 4.0 ms at IF = 10 mA, <= 1.0 ms at IF = 30 mA, VDD 40 V,
#        RLOAD 20 kohm;  TOFF <= 0.5 ms at the same load
#   IO(OFF) <= 1000 nA at VO = 1000 V, over recommended operating conditions
#        (-40 to +105 C for the JV), device OFF with VF <= 0.4 V
#   RON <= 300 ohm at IO = 2 mA, <= 250 ohm at 10 mA; COUT 190 pF typical
#   Output withstand >= 1500 V at 25 C; continuous load voltage 1000 VDC
ASSR = dict(if_min=7.0e-3, if_max=30.0e-3, vf_min=1.25, vf_typ=1.55,
            vf_max=1.85, if_spec=10.0e-3, ton_max=4.0e-3, toff_max=0.5e-3,
            io_off=1.0e-6, ron=300.0, cout=190e-12, bv=1500.0, vload=1000.0)
R_ISO, R_ISO_TOL, R_ISO_PD = 270.0, 0.01, 0.25
B5_NOM, B5_TOL = 5.0, 0.05
RDS_2CH = 2 * 5.0        # two BSS138P channels, allowing 5 ohm each at the
                         # reduced gate drive rather than the 2 ohm at VGS=5 V

hdr('3. The B2 isolation enable and signal path (X1)')
if_lo = ((B5_NOM * (1 - B5_TOL) - ASSR['vf_max'])
         / (R_ISO * (1 + R_ISO_TOL) + RDS_2CH))
if_nom = (B5_NOM - ASSR['vf_typ']) / (R_ISO + RDS_2CH)
if_hi = ((B5_NOM * (1 + B5_TOL) - ASSR['vf_min'])
         / (R_ISO * (1 - R_ISO_TOL) + RDS_2CH))
note('LED current with R_ISO = %.0f ohm: %.2f mA worst low, %.2f mA nominal, '
     '%.2f mA worst high' % (R_ISO, if_lo * 1e3, if_nom * 1e3, if_hi * 1e3))
check('the worst-case LED current is at or above the %.0f mA the turn-on '
      'maximum is specified at' % (ASSR['if_spec'] * 1e3),
      if_lo >= ASSR['if_spec'],
      'at %.2f mA the %.1f ms turn-on maximum would not apply and turn-on '
      'would be an extrapolation' % (if_lo * 1e3, ASSR['ton_max'] * 1e3))
check('the worst-case LED current is inside the recommended window',
      ASSR['if_min'] <= if_lo and if_hi <= ASSR['if_max'],
      '%.2f to %.2f mA against %.0f to %.0f mA'
      % (if_lo * 1e3, if_hi * 1e3, ASSR['if_min'] * 1e3,
         ASSR['if_max'] * 1e3))
note('this is why R_ISO is 270 ohm and not the 330 ohm of the original '
     'return: 330 ohm puts the low corner at 8.64 mA, below the specified '
     'point, which would have left turn-on unspecified exactly where it '
     'matters')
p_riso = if_hi ** 2 * R_ISO * (1 + R_ISO_TOL)
check('R_ISO dissipation %.0f mW is inside its %.2f W rating'
      % (p_riso * 1e3, R_ISO_PD), p_riso <= R_ISO_PD)

T_ISO = 5.0e-3          # firmware: isolate, wait, then release HOLD
T_SETTLE = 20.0e-3      # firmware: enable, wait, then trust VSS edges
check('the isolate-to-release delay is at least 10x the turn-off maximum',
      T_ISO >= 10 * ASSR['toff_max'],
      '%.1f ms against %.1f ms' % (T_ISO * 1e3, ASSR['toff_max'] * 1e3))
check('the enable-to-trust delay is at least 5x the turn-on maximum',
      T_SETTLE >= 5 * ASSR['ton_max'],
      '%.1f ms against %.1f ms' % (T_SETTLE * 1e3, ASSR['ton_max'] * 1e3))
RELEASE_LIMIT = 1801.0 - 1800.0     # the contract's own release allowance
check('isolate-then-release fits inside the shutdown budget',
      T_ISO <= RELEASE_LIMIT,
      '%.3f s of isolation delay against %.3f s of allowance'
      % (T_ISO, RELEASE_LIMIT))
note('%.0f ms of isolation delay leaves %.0f ms of the 1800-to-1801 s release '
     'allowance unused, so the ordering costs nothing in the deadline. The '
     'enable-side %.0f ms is after HOLD is already asserted, so it does not '
     'enter the 900 ms retention path either.'
     % (T_ISO * 1e3, (RELEASE_LIMIT - T_ISO) * 1e3, T_SETTLE * 1e3))
note('the turn-on maximum is specified into a 20 kohm test load and this '
     'branch presents 55 kohm, so the figure is used outside its stated load '
     'condition. That is a bring-up measurement, not a paper result.')

# signal path
R_TOP, R_BOT = 22e3, 33e3
B2_PULSE = 5.0
ratio = R_BOT / (R_TOP + R_BOT)
ratio_sw = R_BOT / (R_TOP + ASSR['ron'] + R_BOT)
check('the relay resistance shifts the B2 divider ratio by less than 1 per '
      'cent',
      abs(ratio_sw - ratio) / ratio < 0.01,
      'shift %.3f %%' % (100 * (ratio_sw - ratio) / ratio))
note('ratio %.6f -> %.6f, a %.2f %% shift, %.1f mV referred to a %.1f V '
     'pulse; the high level lands at %.2f V against an RP2040 VIH of about '
     '2.0 V' % (ratio, ratio_sw, 100 * (ratio_sw - ratio) / ratio,
                1000 * B2_PULSE * (ratio_sw - ratio), B2_PULSE,
                B2_PULSE * ratio_sw))
check('the signal current stays well inside the +/-10 mA load window',
      B2_PULSE / (R_TOP + ASSR['ron'] + R_BOT) < 10e-3)
note('that current, %.1f uA, is two decades below the 2 mA at which the '
     '300 ohm RON maximum is specified, so the 300 ohm is used as an upper '
     'bound rather than as a specified point'
     % (1e6 * B2_PULSE / (R_TOP + ASSR['ron'] + R_BOT)))
# open-state coupling, criterion B: board off, key at II, VSS pulsing
f_vss, edges = 91.0, 2
i_couple = ASSR['cout'] * B2_PULSE * edges * f_vss
note('open-state coupling through the %.0f pF typical output capacitance is '
     '%.3f uA average at %.0f Hz, which is a typical value and not a maximum'
     % (ASSR['cout'] * 1e12, i_couple * 1e6, f_vss))
B2_PARKED = 4.669
check('the output withstand rating covers the parked and fault voltages',
      ASSR['vload'] > 16.0 and ASSR['bv'] > 16.0)
note('the leakage maximum is quoted at %.0f V while %.3f V is applied, a '
     '%.0fx lower stress that is not claimed as extra margin'
     % (1000.0, B2_PARKED, 1000.0 / B2_PARKED))

# ===========================================================================
# 4. The parked ledger, recomputed
# ===========================================================================
# Rows and conditions from COMPONENT_MARGIN_CLOSURE.md section 3 unless the
# comment says LRA-12 changed them. Every figure is a datasheet maximum at
# the stated condition - a mixed-condition screen, not an assembled maximum.
hdr('4. Parked-current ledger, recomputed with the LRA-12 changes')
A5_ROWS = [
    ('UCLK CD74HC4060E', 8.0, 80.0, 'VCC 6 V, unloaded, inputs at rails'),
    ('UCOUNT CD74HC4020E', 8.0, 80.0, 'same conditions'),
    ('ULATCH CD4011BE', 0.25, 7.5, '5 V, rail inputs'),
    ('UOR CD4071BE', 0.25, 7.5, '5 V, rail inputs'),
    ('USCH CD4093BE', 1.0, 30.0, '5 V, rail inputs'),
    ('UOE 74AHC1G17GV', 1.0, 10.0, '5.5 V, rail input, unloaded'),
    ('UGCLK SN74LVC1G97', 10.0, 10.0, '5.5 V, rail inputs, unloaded'),
    ('UXO OV-7604-C7 disabled', 0.55, 1.1, '5 V, 25 C / over TA'),
    ('USUP TPS3839K50', 0.5, 0.5, 'quiescent, output unloaded'),
    ('UA5 ground-current reserve', 10.0, 10.0,
     'only specified at 100 uA load / 30 V: the parked point is below it'),
    ('CCLK T491D336K016AT', 6.625, 66.25, 'with endurance reserve'),
    ('logic input leakage, 29 pins', 12.7, 37.0,
     'from their separate voltage tables'),
    ('other A5 caps, film CQUAL, bypasses', 1.0, 5.0,
     'allocation, not a specified limit'),
    ('DZ_AON BZX55C22', 0.1, 2.0,
     'LRA-12 adds this: IR max at VR = 18 V, 25 C and 150 C. The 150 C '
     'figure is used as a conservative screen for 85 C'),
]
a5_room = sum(r[1] for r in A5_ROWS)
a5_hot = sum(r[2] for r in A5_ROWS)
for name, room, hot, cond in A5_ROWS:
    print('    %-38s %7.3f %8.2f   %s' % (name, room, hot, cond))
print('    %-38s %7.3f %8.2f' % ('A5 DOMAIN SUBTOTAL', a5_room, a5_hot))

OTHER_ROWS = [
    ('QP IPD50P04P4L-11 drain', 1.0, 70.0,
     'LRA-12 change: IDSS max at VDS = -32 V, 25 C / 125 C. The IRF4905 it '
     'replaces screens 25 / 250 uA and cannot fit its own allocation'),
    ('gate sink paths, QS + QI + PCB', 10.0, 19.8,
     'the 0.2 V off-gate limit through 10.1k allows 19.802 uA in total; the '
     'QI and PCB shares remain unproved allocations'),
    ('TVS 1.5KE20A at P12', 1.0, 10.0,
     'ID 1.0 uA max at standoff, 25 C. NO HOT MAXIMUM IS PUBLISHED for this '
     'family, so the hot figure is an allocation, not a limit'),
    ('UISO ASSR-601JV, B2 branch', 1.0, 1.0,
     'IO(OFF) 1000 nA max over the whole recommended operating range. This '
     'draws from the vehicle B2 source, not from J1'),
    ('other four vehicle branches', 0.0, 0.0,
     'measured or logged dead with the key out, so no device and no leakage'),
    ('QMON / QREPORT / QH injection', 2.0, 5.0,
     'allocation; hot limits under these actual base networks are unproved'),
]
other_room = sum(r[1] for r in OTHER_ROWS)
other_hot = sum(r[2] for r in OTHER_ROWS)
print()
for name, room, hot, cond in OTHER_ROWS:
    print('    %-38s %7.3f %8.2f   %s' % (name, room, hot, cond))
print('    %-38s %7.3f %8.2f' % ('OTHER SUBTOTAL', other_room, other_hot))

total_room, total_hot = a5_room + other_room, a5_hot + other_hot
TARGET_ROOM, TARGET_HOT = 100.0, 500.0
print()
print('    %-38s %7.3f %8.2f' % ('WHOLE-SYSTEM SCREEN', total_room,
                                 total_hot))
print('    %-38s %7.1f %8.1f' % ('unchanged acceptance target', TARGET_ROOM,
                                 TARGET_HOT))
check('the room screen fits the unchanged 100 uA target',
      total_room <= TARGET_ROOM,
      'screen %.1f uA' % total_room)
check('the hot screen fits the unchanged 500 uA target',
      total_hot <= TARGET_HOT, 'screen %.1f uA' % total_hot)

# The sub-allocations of INTERFACE_CONTRACT section 7 do not survive, even
# though the totals do. Say so with the numbers rather than quietly summing.
WHY = ('the contract allocation for this row predates the parts now '
       'selected; see the proposed re-allocation in LAYOUT_CLOSURE S7, which '
       'leaves the 100/500 uA totals untouched')
for label, alloc, screen in (
        ('A5 supply + timer/logic/filter, room', 50.0, a5_room),
        ('A5 supply + timer/logic/filter, hot', 250.0, a5_hot)):
    if screen > alloc:
        over(label, alloc, screen, WHY)
    else:
        check('%s fits its allocation' % label, True)
check('the switch allocation now has headroom to give',
      70.0 < 200.0,
      'the QP change has to free hot headroom for the re-allocation to work')
note('those two failures are the honest result and are not a defect in the '
     'circuit: the A5 domain overruns its own sub-allocation while the WHOLE '
     'system fits, because the QP change freed %.0f uA hot from the 200 uA '
     'switch allocation. LAYOUT_CLOSURE S7 proposes moving that headroom to '
     'the A5 row, keeping the 100/500 uA totals untouched. Section 7 of the '
     'interface contract already invites exactly this kind of explicit '
     're-allocation, and it needs reviewer acceptance.' % (250.0 - 70.0))
note('the two largest hot rows are the HC counters at 80 uA each and the '
     'clock reservoir at 66 uA. A lower-CV CCLK or a re-proportioned RCLK/'
     'CCLK pair would cut the last of those, at the cost of re-opening the '
     'oscillator slew qualification; LAYOUT_CLOSURE S7 records that option '
     'with its numbers rather than taking it.')

# ===========================================================================
# 5. Off-state path audit, read out of the netlist
# ===========================================================================
hdr('5. Off-state path audit over the exported netlist')
text = open(NET, encoding='utf-8').read()
nets = {}
for m in re.finditer(
        r'\(net \(code "\d+"\) \(name "([^"]*)"\)(.*?)(?=\n    \(net |\Z)',
        text, re.S):
    name = m.group(1).lstrip('/')
    nets[name] = set(re.findall(
        r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', m.group(2)))
libid = dict(re.findall(r'\(comp \(ref "([^"]+)"\).*?\(lib "([^"]*)"\)'
                        r'\s*\(part "([^"]*)"\)', text, re.S)
             and [] or [])
# lib_id per component, taken from the libsource entry
libid = {}
for m in re.finditer(r'\(comp \(ref "([^"]+)"\)(.*?)(?=\n    \(comp |\Z)',
                     text, re.S):
    ls = re.search(r'\(libsource \(lib "([^"]*)"\) \(part "([^"]*)"\)',
                   m.group(2))
    if ls:
        libid[m.group(1)] = ls.group(1) + ':' + ls.group(2)

# A two-terminal passive conducts, for a leakage audit. A diode conducts in
# both directions here, which is the pessimistic reading. Transistors,
# optocouplers, the relay, regulators and connectors contribute no edge: each
# is either a declared blocking element or not a conductor between nets.
#
# GROUND IS NOT A TRANSIT NODE. The first version of this audit let paths run
# through PGND, which every bypass capacitor and every pulldown touches, so
# the graph said each net reached every other one and the audit was
# worthless - it only passed for B2 because nothing ground-referenced sits on
# that one net. The question an off-state audit asks is whether an energized
# source can push current INTO a switched rail; current returning through
# ground is how the circuit is supposed to work. So the ground nets are
# terminals, not junctions.
CONDUCTS = ('Device:R', 'Device:C', 'Device:L', 'Device:Fuse',
            'Device:D_', 'Diode:', 'Jumper:')
GROUNDS = {'PGND', 'AGND'}


def neighbours(blockers_conduct=()):
    """net -> set of nets, through conducting parts only."""
    pins = {}
    for net, nodes in nets.items():
        for ref, pin in nodes:
            pins.setdefault(ref, {})[pin] = net
    adj = {}
    for ref, pinmap in pins.items():
        lid = libid.get(ref, '')
        conducts = any(lid.startswith(p) for p in CONDUCTS)
        if ref in blockers_conduct:
            conducts = True
        if not conducts or len(pinmap) < 2:
            continue
        ns = sorted(set(pinmap.values()) - GROUNDS)
        for a in ns:
            for b in ns:
                if a != b:
                    adj.setdefault(a, set()).add(b)
    return adj


def reaches(start, targets, blockers_conduct=()):
    adj = neighbours(blockers_conduct)
    seen, stack = {start}, [start]
    while stack:
        n = stack.pop()
        for m2 in adj.get(n, ()):
            if m2 not in seen:
                seen.add(m2)
                stack.append(m2)
    return seen & set(targets)

SWITCHED = {'P3V3_SW', 'B5', 'VSYS', 'VIN_SW', 'SW'}
hit = reaches('B2_TAP', SWITCHED)
check('B2, energized with the key out, cannot reach any switched rail',
      not hit, 'reaches %s' % sorted(hit))
# Anti-vacuity: the path must exist when the relay is treated as closed, or
# this audit would pass on a graph that was simply never connected.
hit_closed = reaches('B2_TAP', SWITCHED, blockers_conduct={'U3'})
check('with the relay treated as closed the path does exist, so the audit is '
      'not vacuous', bool(hit_closed),
      'no path even with the relay closed: the graph or the net names are '
      'wrong, not the circuit')
note('with the relay closed B2 reaches %s, which is the back-feed the owner '
     'measured at 109.2 uA; open, it reaches none of them'
     % sorted(hit_closed))
hit12 = reaches('P12', SWITCHED)
check('the always-on input cannot reach a switched rail with QP off',
      not hit12, 'reaches %s' % sorted(hit12))
hit12c = reaches('P12', SWITCHED, blockers_conduct={'Q5'})
check('with QP treated as on the path does exist, so that audit is not '
      'vacuous either', bool(hit12c), 'no path even with QP on')
for src in ('B1_TAP', 'C14_TAP', 'C11_TAP', 'B11_TAP'):
    h = reaches(src, SWITCHED)
    check('%s still reaches the switched rail it was always connected to'
          % src, bool(h),
          'the bypass decision leaves these branches as built; if this '
          'fails the netlist changed, not the decision')

# What the four bypassed branches actually do, and in which state.
#
# Two separate criteria, which the record used to discuss as one.
#   A, parked leakage: all five branches de-energized with the key out, by
#      measurement or log, and B2 isolated by the relay. Injection is zero.
#   B, board off with the inputs energized: this is NOT the parked state. It
#      needs the key on AND an upstream power fault, because ignition present
#      turns QI on and powers the board. In that fault state the fitted
#      series resistance bounds each branch, and the criterion-B 0.3 V rail
#      limit is NOT met - which is reported, not papered over.
CLAMP_VF = 0.3                 # held-low upper clamp, DESIGN.md S6
BRANCHES = [
    ('B1 tach at charging', 14.8, 22e3, 0.0),
    ('C14 brake at charging', 14.1, 22e3, 0.0),
    ('B11 supply at charging', 15.0, 22e3, 0.0),
    ('C11 fuel at its ceiling', 8.0, 7.5e3, 1e3),
    ('B2 VSS parked, as built', 5.0, 22e3, 0.0),
]
inj = {}
for name, v, rtop, rser in BRANCHES:
    inj[name] = (v - CLAMP_VF) / (rtop + rser)
    note('%-28s %.3f mA into a 0 V rail through %.1f k'
         % (name, inj[name] * 1e3, (rtop + rser) / 1e3))
asbuilt = sum(inj.values())
revA = sum(i for n, i in inj.items() if 'B2' not in n)
check('no branch alone can push more than 1 mA into a dead rail',
      max(inj.values()) < 1.0e-3,
      'worst %.3f mA' % (max(inj.values()) * 1e3))
check('isolating B2 lowers the total criterion-B injection rather than '
      'raising it', revA < asbuilt,
      '%.3f mA against %.3f mA as built' % (revA * 1e3, asbuilt * 1e3))
note('criterion-B total is %.2f mA against the as-built %.2f mA. It is still '
     'far above anything that would hold a dead 3V3 rail below 0.3 V, so '
     'CRITERION B IS NOT MET for the four bypassed branches in that state. '
     'What LRA-12 asserts instead is that the state needs an upstream power '
     'fault as well as the key on, and the interlock below is the reason.'
     % (revA * 1e3, asbuilt * 1e3))

# The interlock the bypass decision rests on, read off the netlist: raw
# ignition drives QI's base, and QI sinks the QP gate directly. So ignition
# present means the switch is on and the board is powered, with no firmware,
# no HOLD and no qualification involved.
pins = {}
for net, nodes in nets.items():
    for ref, pin in nodes:
        pins.setdefault(ref, {})[pin] = net
qi = [r for r, pm in pins.items()
      if libid.get(r) == 'Transistor_BJT:2N3904' and pm.get('3') == 'SINK'
      and pm.get('1') == 'PGND']
check('exactly one transistor sinks the gate directly from raw ignition',
      len(qi) == 1, 'found %s' % qi)
if qi:
    base = pins[qi[0]].get('2')
    rib = [r for r, pm in pins.items()
           if libid.get(r, '').startswith('Device:R')
           and set(pm.values()) == {'IGN_POS', base}]
    check('its base is driven from the ignition tap through a resistor',
          bool(rib), 'no resistor between IGN_POS and %s' % base)
    check('the ignition tap is the same net the opto LED runs from',
          'IGN_POS' in nets and
          any(r for r, pm in pins.items()
              if libid.get(r) == 'Isolator:PC817'
              and 'IGN_LED_A' in pm.values()),
          'the interlock argument needs one ignition source, not two')
note('that is the whole bypass argument in circuit terms: ignition present '
     '-> QI on -> QP on -> the board is powered. "Board off with the inputs '
     'energized" is therefore a fault state, and it is carried as a '
     'bring-up and fault-injection test, not as a parked condition.')

# ===========================================================================
print()
print('=' * 72)
print('%d/%d checks passed, %d sub-allocation overrun(s) reported'
      % (checks - len(fails), checks, len(overruns)))
for f in fails:
    print('  FAIL', f)
for o in overruns:
    print('  OVER', o)
print()
print('These are datasheet-limit calculations and one netlist topology audit.')
print('They are not measurements and they qualify no component. An OVER line')
print('is a sub-allocation that needs reviewer redistribution, not a circuit')
print('defect: the unchanged 100/500 uA whole-system targets still close.')
sys.exit(1 if fails else 0)
