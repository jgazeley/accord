"""Write logger/hardware/kicad/Custom.kicad_sym.

LM2678T-5.0 is copied from keyless/hardware/Custom.kicad_sym rather than
redrawn, per the LRA-06 packet.

LRA-12 adds the parts the installed libraries do not carry, and retires the
LRA-06 placeholders. The `placeholder()` helper is kept, because it is the
mechanism a future genuinely unresolved block should use, but LRA-12 emits
none: X1-X8 now each have a real circuit or a recorded, justified bypass, so
no dashed "NOT SELECTED" body remains in the drawing. See
`../../power/LAYOUT_CLOSURE.md` and `../CAPTURE_NOTES.md` section 2.

The glue logic is drawn as single-unit boxes carrying every package pin, not
as KiCad's multi-unit 4xxx symbols. This capture connects by placing a net
label on each pin, so one body per package keeps the drawing and the netlist
in step, and it puts the whole package - including the inputs that must be
tied off - in one place where a reviewer can see them at once.

Pin numbers and names below are taken from the manufacturer documents cited in
each symbol's Datasheet property, and are asserted again against the exported
netlist by `../check_capture.py`.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sexp

OUT = sys.argv[1]
REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     '..', '..', '..', '..'))
KEYLESS = os.path.join(REPO, 'keyless', 'hardware', 'Custom.kicad_sym')

lm = None
for s in sexp.getall(sexp.read(KEYLESS), 'symbol'):
    if s[1] == '"LM2678T-5.0':
        lm = sexp.dump(s, 1)
assert lm, 'LM2678T-5.0 not found in the keyless Custom library'


def pin(num, name, x, y, rot, length=5.08, etype='passive'):
    return (
        '\t\t\t(pin %s line\n'
        '\t\t\t\t(at %s %s %s)\n'
        '\t\t\t\t(length %s)\n'
        '\t\t\t\t(name "%s"\n'
        '\t\t\t\t\t(effects (font (size 1.27 1.27)))\n'
        '\t\t\t\t)\n'
        '\t\t\t\t(number "%s"\n'
        '\t\t\t\t\t(effects (font (size 1.27 1.27)))\n'
        '\t\t\t\t)\n'
        '\t\t\t)' % (etype, x, y, rot, length, name, num))


def placeholder(name, desc, keywords, pins, w, h, label):
    """A dashed box carrying a '?' so it cannot be mistaken for a real part.

    Retained as the mechanism for a future unresolved block. LRA-12 emits no
    placeholder; see the module docstring.
    """
    body = '\n'.join(pins)
    return '''\t(symbol "%s"
\t\t(pin_names
\t\t\t(offset 1.016)
\t\t)
\t\t(exclude_from_sim yes)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(property "Reference" "X"
\t\t\t(at %s %s 0)
\t\t\t(effects (font (size 1.27 1.27)) (justify left))
\t\t)
\t\t(property "Value" "%s"
\t\t\t(at %s %s 0)
\t\t\t(effects (font (size 1.27 1.27)) (justify left))
\t\t)
\t\t(property "Footprint" ""
\t\t\t(at 0 0 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Datasheet" ""
\t\t\t(at 0 0 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Description" "%s"
\t\t\t(at 0 0 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "ki_keywords" "%s"
\t\t\t(at 0 0 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(symbol "%s_0_1"
\t\t\t(rectangle
\t\t\t\t(start %s %s)
\t\t\t\t(end %s %s)
\t\t\t\t(stroke (width 0.381) (type dash))
\t\t\t\t(fill (type none))
\t\t\t)
\t\t\t(text "?"
\t\t\t\t(at 0 %s 0)
\t\t\t\t(effects (font (size 3.81 3.81) (bold yes)))
\t\t\t)
\t\t\t(text "%s"
\t\t\t\t(at 0 %s 0)
\t\t\t\t(effects (font (size 1.27 1.27) (italic yes)))
\t\t\t)
\t\t)
\t\t(symbol "%s_1_1"
%s
\t\t)
\t)''' % (name, -w, h + 2.54, name, -w, -h - 2.54, desc, keywords, name,
         -w, h, w, -h, h - 3.81, label, -h + 2.54, name, body)


def ic_box(name, desc, keywords, left, right, w=11.43, fp_filter='',
           datasheet='', note=''):
    """A single-unit IC body carrying every package pin.

    `left` and `right` are lists of (number, pinname, electrical_type) in
    physical package order, top to bottom; None leaves a row empty, which is
    how a package with missing leads is drawn.
    """
    rows = max(len(left), len(right))
    h = max(((rows - 1) * 2.54) / 2.0 + 3.81, 7.62)
    out = []
    for side, col in (('L', left), ('R', right)):
        y0 = ((len(col) - 1) * 2.54) / 2.0
        for i, item in enumerate(col):
            if item is None:
                continue
            num, nm, et = item
            y = y0 - i * 2.54
            if side == 'L':
                out.append(pin(num, nm, -(w + 5.08), y, 0, etype=et))
            else:
                out.append(pin(num, nm, w + 5.08, y, 180, etype=et))
    extra = ''
    if note:
        extra = ('\n\t\t\t(text "%s"\n\t\t\t\t(at 0 %s 0)\n'
                 '\t\t\t\t(effects (font (size 1.0 1.0) (italic yes)))\n'
                 '\t\t\t)' % (note, -h + 1.905))
    return '''\t(symbol "%s"
\t\t(pin_names
\t\t\t(offset 0.508)
\t\t)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(property "Reference" "U"
\t\t\t(at %s %s 0)
\t\t\t(effects (font (size 1.27 1.27)) (justify left))
\t\t)
\t\t(property "Value" "%s"
\t\t\t(at %s %s 0)
\t\t\t(effects (font (size 1.27 1.27)) (justify left))
\t\t)
\t\t(property "Footprint" ""
\t\t\t(at 0 0 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Datasheet" "%s"
\t\t\t(at 0 0 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Description" "%s"
\t\t\t(at 0 0 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "ki_keywords" "%s"
\t\t\t(at 0 0 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "ki_fp_filters" "%s"
\t\t\t(at 0 0 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(symbol "%s_0_1"
\t\t\t(rectangle
\t\t\t\t(start %s %s)
\t\t\t\t(end %s %s)
\t\t\t\t(stroke (width 0.254) (type solid))
\t\t\t\t(fill (type background))
\t\t\t)%s
\t\t)
\t\t(symbol "%s_1_1"
%s
\t\t)
\t)''' % (name, -w, h + 2.54, name, -w, -h - 2.54, datasheet, desc, keywords,
         fp_filter, name, -w, h, w, -h, extra, name, '\n'.join(out))


syms = [lm]


# ====================================================== 14-pin CMOS glue logic
# All three share the 4000-series quad two-input pinout: gate A inputs 1 and 2
# with output 3, gate B inputs 5 and 6 with output 4, gate C inputs 8 and 9
# with output 10, gate D inputs 12 and 13 with output 11, VSS on 7, VDD on 14.
# MAX_ON_CUTOFF.md's connection table uses exactly these numbers.
def quad14(a, b, c, d):
    left = [('1', a + '1', 'input'), ('2', a + '2', 'input'),
            ('3', a + 'Y', 'output'), ('4', b + 'Y', 'output'),
            ('5', b + '1', 'input'), ('6', b + '2', 'input'),
            ('7', 'VSS', 'power_in')]
    right = [('14', 'VDD', 'power_in'), ('13', d + '2', 'input'),
             ('12', d + '1', 'input'), ('11', d + 'Y', 'output'),
             ('10', c + 'Y', 'output'), ('9', c + '2', 'input'),
             ('8', c + '1', 'input')]
    return left, right


L14, R14 = quad14('A', 'B', 'C', 'D')
syms.append(ic_box(
    'CD4011B',
    'Quad 2-input NAND gate, CMOS, PDIP-14. Used as the reset-dominant '
    'ARM/NARM latch (gates A and B) and the QUAL_N inverter (gate C); gate D '
    'is unused and its inputs 12 and 13 must be tied to a rail.',
    'CMOS 4011 NAND quad latch', L14, R14, fp_filter='DIP*W7.62mm*',
    datasheet='https://www.ti.com/lit/ds/symlink/cd4011b.pdf',
    note='A,B = ARM latch   C = QUAL_N inverter   D unused'))

syms.append(ic_box(
    'CD4071B',
    'Quad 2-input OR gate, CMOS, PDIP-14. Forms BASE_RESET, COUNT1_RESET, '
    'FAULT_RESET and ARM_RESET in the independent cutoff logic.',
    'CMOS 4071 OR quad reset', L14, R14, fp_filter='DIP*W7.62mm*',
    datasheet='https://www.ti.com/lit/ds/symlink/cd4071b.pdf',
    note='reset OR tree: all four gates used'))

syms.append(ic_box(
    'CD4093B',
    'Quad 2-input Schmitt-trigger NAND gate, CMOS, PDIP-14. Qualifies the '
    'ignition RC filter (gate A), inverts the supervisor to BAD (gate B) and '
    'forms RESET_N and SET_N (gates C and D).',
    'CMOS 4093 Schmitt NAND quad qualification', L14, R14,
    fp_filter='DIP*W7.62mm*',
    datasheet='https://www.ti.com/lit/ds/symlink/cd4093b.pdf',
    note='Schmitt inputs: IGN filter, BAD, RESET_N, SET_N'))

# =========================================================== HC ripple counters
# CD74HC4060 is a 14-stage counter with an on-chip oscillator. Pins 9, 10 and 11
# are its oscillator terminals; this design drives pin 11 from the external
# clock block and leaves 9 and 10 open (CUTOFF_MARGIN_REVIEW.md section 1).
syms.append(ic_box(
    'CD74HC4060',
    '14-stage binary ripple counter with oscillator, high-speed CMOS, '
    'PDIP-16. Driven from an external 32.768 kHz clock on pin 11 with pins 9 '
    'and 10 open; Q14 on pin 3 supplies 2 falling edges per second.',
    'HC4060 counter divider oscillator 14-stage',
    [('1', 'Q12', 'output'), ('2', 'Q13', 'output'), ('3', 'Q14', 'output'),
     ('4', 'Q6', 'output'), ('5', 'Q5', 'output'), ('6', 'Q7', 'output'),
     ('7', 'Q4', 'output'), ('8', 'VSS', 'power_in')],
    [('16', 'VDD', 'power_in'), ('15', 'Q10', 'output'),
     ('14', 'Q8', 'output'), ('13', 'Q9', 'output'), ('12', 'MR', 'input'),
     ('11', 'CLK', 'input'), ('10', 'OSC1', 'input'),
     ('9', 'OSC2', 'output')],
    fp_filter='DIP*W7.62mm*',
    datasheet='https://www.ti.com/lit/ds/symlink/cd74hc4060.pdf',
    note='external clock on 11; 9 and 10 open; MR active high'))

syms.append(ic_box(
    'CD74HC4020',
    '14-stage binary ripple counter, high-speed CMOS, PDIP-16. Clocked from '
    'the HC4060 Q14 output; Q13 on pin 2 is the production 2048 s terminal '
    'count and Q8 on pin 13 the clearly labelled 64 s accelerated test tap.',
    'HC4020 counter divider 14-stage',
    [('1', 'Q12', 'output'), ('2', 'Q13', 'output'), ('3', 'Q14', 'output'),
     ('4', 'Q6', 'output'), ('5', 'Q5', 'output'), ('6', 'Q7', 'output'),
     ('7', 'Q4', 'output'), ('8', 'VSS', 'power_in')],
    [('16', 'VDD', 'power_in'), ('15', 'Q11', 'output'),
     ('14', 'Q10', 'output'), ('13', 'Q8', 'output'), ('12', 'Q9', 'output'),
     ('11', 'MR', 'input'), ('10', 'CLK', 'input'), ('9', 'Q1', 'output')],
    fp_filter='DIP*W7.62mm*',
    datasheet='https://www.ti.com/lit/ds/symlink/cd74hc4020.pdf',
    note='negative-edge clock on 10; MR active high'))

# ================================================================= A5 regulator
# TI TPS709-Q1, SLVSCE6D (December 2013, revised August 2025), Table 4-1:
# DBV (SOT-23-5) is IN 1, GND 2, EN 3, NC 4, OUT 5. EN may float to enable and
# its absolute maximum is 7 V, so it is never tied to the battery rail.
syms.append(ic_box(
    'TPS70950-Q1_DBV',
    'TPS70950QDBVRQ1 150 mA 30 V low-quiescent LDO with reverse-current '
    'protection, SOT-23-5 (DBV). EN left open to enable; its absolute maximum '
    'is 7 V, so it must never be tied to an unregulated rail.',
    'LDO regulator 5V always-on TPS709 automotive',
    [('1', 'IN', 'power_in'), ('2', 'GND', 'power_in'), ('3', 'EN', 'input')],
    [('5', 'OUT', 'power_out'), ('4', 'NC', 'free')],
    w=8.89, fp_filter='SOT?23*',
    datasheet='https://www.ti.com/lit/ds/symlink/tps709-q1.pdf',
    note='EN open = enabled'))

# =================================================================== oscillator
# Micro Crystal OV-7604-C7 datasheet version 4.5/08.2023, PIN CONNECTIONS:
# 1 CLKOUT, 2 GND, 3 CLKOE, 4 VDD. CLKOE low makes CLKOUT low while the
# internal oscillator keeps running.
syms.append(ic_box(
    'OV-7604-C7',
    'Micro Crystal OV-7604-C7 32.768 kHz low-power clock oscillator, SON-4 '
    'ceramic 3.2 x 1.5 x 1.0 mm. VDD 1.2-5.5 V; CLKOE enables the output.',
    'oscillator 32.768kHz clock SON-4 micro crystal',
    [('4', 'VDD', 'power_in'), ('3', 'CLKOE', 'input'),
     ('2', 'GND', 'power_in')],
    [('1', 'CLKOUT', 'output')],
    w=8.89, fp_filter='Oscillator*OV-7604*',
    datasheet='https://www.microcrystal.com/fileadmin/Media/Products/kHzOSC/'
              'Datasheet/OV-7604-C7.pdf',
    note='CLKOE low = output low, oscillator still running'))

# ===================================================== B2 isolation photo-MOSFET
# Broadcom ASSR-601Jx-DS105 (June 17, 2024), Pin Description: 1, 2, 6, 7 and 8
# are NC; 3 is "Do not connect (internally connected to Pin 5)"; 4 is AN; 5 is
# CA; 9 and 10 are D2, internally connected; 15 and 16 are D1, internally
# connected. Pins 11 to 14 do not exist - that gap carries the drain-to-drain
# creepage, which is why a stock full-lead SOIC-16 footprint is wrong here.
syms.append(ic_box(
    'ASSR-601JV',
    'Broadcom ASSR-601JV automotive photo-MOSFET relay, 1 Form A, 300 mil '
    'SO-16 with 12 populated leads. The output is a back-to-back avalanche '
    'MOSFET pair with no supply of its own, so the LED-dark state is open by '
    'construction. Pin 3 must be left unconnected: it is internally tied to '
    'the LED cathode. Pins 11-14 do not exist.',
    'photomos relay solid state isolation automotive AEC-Q101 ASSR',
    [('1', 'NC', 'free'), ('2', 'NC', 'free'),
     ('3', 'NC_DNC', 'free'), ('4', 'AN', 'passive'),
     ('5', 'CA', 'passive'), ('6', 'NC', 'free'), ('7', 'NC', 'free'),
     ('8', 'NC', 'free')],
    [('16', 'D1', 'passive'), ('15', 'D1', 'passive'), None, None, None, None,
     ('10', 'D2', 'passive'), ('9', 'D2', 'passive')],
    fp_filter='ASSR-601Jx*',
    datasheet='https://docs.broadcom.com/doc/ASSR-601Jx-DS',
    note='1 Form A   pin 3 do not connect   no pins 11-14'))

header = '''(kicad_symbol_lib
\t(version 20241209)
\t(generator "gen_custom_sym.py")
\t(generator_version "9.0")
'''
open(OUT, 'w', encoding='utf-8').write(header + '\n'.join(syms) + '\n)\n')
print('wrote', OUT, len(syms), 'symbols')
