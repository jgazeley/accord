# Project footprints for parts with no installed-library equivalent.

Two, both created by LRA-12 from the manufacturer drawing rather than from a
summary, and both measured by `../fp_area.py`:

- `ASSR-601Jx_SO-16-12Lead_11.634x10.363mm_P1.27mm` — Broadcom ASSR-601JV
  photo-MOSFET relay. A 300 mil SO-16 body with only **12 populated leads**:
  pins 11-14 do not exist and the gap carries the drain-to-drain creepage, so
  a stock `SOIC-16W_7.5x10.3mm_P1.27mm` is wrong here - it would place pads
  where there are no leads. Land pattern from ASSR-601Jx-DS105, 2024-06-17:
  11.634 mm overall span, 8.763 mm between pad centres, 1.270 mm pitch,
  0.635 mm minimum pad width. **Pin 3 is "do not connect"** - internally tied
  to pin 5, the LED cathode - and `../check_capture.py` asserts it carries no
  net. The pin 11-14 gap is marked keep-clear on User.9.

- `Oscillator_SMD_MicroCrystal_OV-7604-C7_SON-4_3.2x1.5mm` — Micro Crystal
  OV-7604-C7 32.768 kHz oscillator, SON-4 ceramic. Recommended solder pad from
  the datasheet version 4.5/08.2023: 1.0 x 0.8 mm pads at +/-1.35, +/-0.6 mm.
  Pin 1 CLKOUT, 2 GND, 3 CLKOE, 4 VDD, with 4 and 3 on the upper row in top
  view.

- `JAE_IL-AG5-14P-D3L2-A`: JAE IL-AG5 14-contact right-angle pin header,
  the board connector J1. **Generated** by `../tools/gen_fp_ilag5.py 14`
  from the JAE IL-AG5 catalogue's right-angle "PCB Hole Pattern (Ref.)"
  (A 20.0, B 26.5, C1 12.5 mm; 2.5 mm pitch; rows 6.0 mm apart; outer row
  6 contacts, near row 8; 1.1 mm holes; two 2.2 mm NPTH board guides).
  Regenerate rather than edit. The generator also reproduces the keyless
  22P footprint exactly, which `../check_capture.py` asserts. Pin numbering
  follows the keyless convention; check it against the housing.

Every other part in this design resolves in an installed KiCad library. See
`../CAPTURE_NOTES.md` and `../../power/LAYOUT_CLOSURE.md`.
