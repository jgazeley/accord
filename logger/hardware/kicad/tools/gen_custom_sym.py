"""Write logger/hardware/kicad/Custom.kicad_sym.

LM2678T-5.0 is copied from keyless/hardware/Custom.kicad_sym rather than
redrawn, per the LRA-06 packet. The placeholder symbols are new: each marks a
block whose part is deliberately not selected by this task.
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
    return f'''			(pin {etype} line
				(at {x} {y} {rot})
				(length {length})
				(name "{name}"
					(effects (font (size 1.27 1.27)))
				)
				(number "{num}"
					(effects (font (size 1.27 1.27)))
				)
			)'''


def placeholder(name, desc, keywords, pins, w, h, label):
    """A dashed box carrying a '?' so it cannot be mistaken for a real part."""
    body = '\n'.join(pins)
    return f'''	(symbol "{name}"
		(pin_names
			(offset 1.016)
		)
		(exclude_from_sim yes)
		(in_bom yes)
		(on_board yes)
		(property "Reference" "X"
			(at {-w} {h + 2.54} 0)
			(effects (font (size 1.27 1.27)) (justify left))
		)
		(property "Value" "{name}"
			(at {-w} {-h - 2.54} 0)
			(effects (font (size 1.27 1.27)) (justify left))
		)
		(property "Footprint" ""
			(at 0 0 0)
			(effects (font (size 1.27 1.27)) (hide yes))
		)
		(property "Datasheet" ""
			(at 0 0 0)
			(effects (font (size 1.27 1.27)) (hide yes))
		)
		(property "Description" "{desc}"
			(at 0 0 0)
			(effects (font (size 1.27 1.27)) (hide yes))
		)
		(property "ki_keywords" "{keywords}"
			(at 0 0 0)
			(effects (font (size 1.27 1.27)) (hide yes))
		)
		(symbol "{name}_0_1"
			(rectangle
				(start {-w} {h})
				(end {w} {-h})
				(stroke (width 0.381) (type dash))
				(fill (type none))
			)
			(text "?"
				(at 0 {h - 3.81} 0)
				(effects (font (size 3.81 3.81) (bold yes)))
			)
			(text "{label}"
				(at 0 {-h + 2.54} 0)
				(effects (font (size 1.27 1.27) (italic yes)))
			)
		)
		(symbol "{name}_1_1"
{body}
		)
	)'''


syms = [lm]

# D4 input isolation. Two variants so the SVG shows at a glance which branch
# has a measured case. D-OFFSTATE-01, October 29, as corrected: key out, B2
# reads 4.140 V loaded against 4.669 V open-circuit and draws 134-141 uA, of
# which 99-110 uA is back-fed into the Pico's unpowered 3V3 rail through a
# forward-biased clamp. B1 and C11 read 0 V, and C14 and B11 were already
# recorded dead with the key out. All five positions are kept; only the
# justification differs.
iso_pins = [pin('1', 'TAP', -15.24, 0, 0), pin('2', 'DIV', 15.24, 0, 180)]
syms.append(placeholder(
    'PLACEHOLDER_SIGNAL_ISO_REQ',
    'LRA-06 placeholder: normally-open, power-off-safe signal isolation '
    'upstream of the B2 divider top (delta D4). Required on measured evidence: '
    'key out, B2 draws 134-141 uA and back-feeds 99-110 uA into the unpowered '
    '3V3 rail through a forward-biased clamp, D-OFFSTATE-01. No part is '
    'selected.',
    'placeholder isolation D4 required B2 backfeed unselected',
    iso_pins, 11.43, 8.89, 'REQUIRED, NOT SELECTED (D4)'))
syms.append(placeholder(
    'PLACEHOLDER_SIGNAL_ISO_REVIEW',
    'LRA-06 placeholder: normally-open, power-off-safe signal isolation '
    'upstream of one divider top (delta D4). Position retained, but the '
    'parked-drain justification is withdrawn for this branch per '
    'D-OFFSTATE-01; it is under analog review. No part is selected.',
    'placeholder isolation D4 under review unselected',
    iso_pins, 11.43, 8.89, 'UNDER REVIEW, NOT SELECTED (D4)'))

# VEHICLE_PROTECTION BOM row.
syms.append(placeholder(
    'PLACEHOLDER_VEHICLE_PROT',
    'LRA-06 placeholder: coordinated vehicle input/IGN protection and fault '
    'limiting (power BOM row VEHICLE_PROTECTION). No part is selected.',
    'placeholder protection TVS unselected R02',
    [pin('1', 'LINE', -15.24, 0, 0), pin('2', 'GND', 0, -15.24, 90)],
    10.16, 7.62, 'NOT SELECTED (R02)'))

# MAX_ON BOM row: independent timer plus latched HOLD-path inhibit.
maxon_pins = [
    pin('1', 'P12', -27.94, 10.16, 0),
    pin('2', 'HOLD_SENSE', -27.94, 2.54, 0),
    pin('3', 'GND', -27.94, -10.16, 0),
    pin('4', 'A5', 27.94, 12.7, 180),
    pin('5', 'VCLK', 27.94, 7.62, 180),
    pin('6', 'PGOOD', 27.94, 2.54, 180),
    pin('7', 'ARM', 27.94, 0, 180),
    pin('8', 'EXPIRED', 27.94, -2.54, 180),
    pin('9', 'HOLD_N', 27.94, -7.62, 180),
]
syms.append(placeholder(
    'PLACEHOLDER_MAX_ON',
    'LRA-06 placeholder: independent maximum-on timer plus latched HOLD-path '
    'inhibit (power BOM row MAX_ON, not implemented in revision A). '
    'No part is selected.',
    'placeholder timer cutoff MAX_ON unselected',
    maxon_pins, 22.86, 17.78, 'NOT SELECTED (MAX_ON)'))

# The A5-domain qualified-IGN report stage that drives GP5 in Rev A.
qual_pins = [
    pin('1', 'IGN_N', -22.86, 5.08, 0),
    pin('2', 'A5', -22.86, 0, 0),
    pin('3', 'GND', -22.86, -7.62, 0),
    pin('4', 'QUAL_N_REPORT', 22.86, 5.08, 180),
]
syms.append(placeholder(
    'PLACEHOLDER_IGN_QUAL',
    'LRA-06 placeholder: A5-domain qualified-ignition stage whose open-drain '
    'QREPORT output is GP5 in REV_A_INTERFACES section 1. Its component-level '
    'design is not in this task input. No part is selected.',
    'placeholder qualification QREPORT unselected LRA-01',
    qual_pins, 17.78, 12.7, 'NOT SELECTED (QREPORT)'))

header = '''(kicad_symbol_lib
	(version 20241209)
	(generator "gen_custom_sym.py")
	(generator_version "9.0")
'''
open(OUT, 'w', encoding='utf-8').write(header + '\n'.join(syms) + '\n)\n')
print('wrote', OUT)
