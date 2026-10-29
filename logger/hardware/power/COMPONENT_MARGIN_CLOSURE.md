# LRA-02 component and current margin package

October 28, 2026 — Codex `logger-power`, electrical lead.
Session `01a18463-5ed7-7041-ad90-ec3a7480c4e6`;
resume `codex resume 01a18463-5ed7-7041-ad90-ec3a7480c4e6`.

**Disposition: conditional component selections; parked-current guarantee remains
unresolved.** This is the first bounded LRA-02 return authorized by the packet
published in main at `1d9e07d`. Parent candidate is `a85f185`; underlying circuit
is `9527a14`. Neither parent nor this return is accepted, built or tested hardware.
The input switch, buck, independent latch/counters, shared IGN and HOLD topology
remain. [BOM_DELTA.csv](BOM_DELTA.csv) is a delta, not a replacement merged BOM.
Only the four files allowed by the packet are added. Contract corrections below
are proposals for its reviewers; `INTERFACE_CONTRACT.md` remains untouched.

“Supported” below means the cited calculation/part property at its stated
conditions. “Conditional” means selected for the next reviewed prototype with
named qualifications. “Unresolved” means a specification or physical result is
missing. No nominal value, typical curve or passing Python model fills that gap.

## 1. Capacitor selections

Use the following exact candidates. Procurement, stock, fabrication and operation
are not authorized by this paper return. All added adapters need short local
connections; a solderless breadboard is not a qualified buck layout.

| Ref / exact manufacturer part | Selection and package | Supported specification; remaining condition |
|---|---|---|
| CCLK: KEMET **T491D336K016AT**, one | 33 µF, ±10%, 16 V, polarized D/7343-31 | Conditional selection replacing unspecified nominal 47 µF; positive to VCLK. See calculation below |
| A5 input: Murata **GRM32ER71H475KA88L**, one | 4.7 µF, ±10%, 50 V X7R, 1210, 3.2 × 2.5 × 2.5 mm nominal | Conditional selection at P_AON 6–28 V; effective C must remain >=1 µF |
| A5 output: same **GRM32ER71H475KA88L**, two parallel | Nominal 9.4 µF, 50 V X7R; replaces unspecified 10 µF/16 V | Conditional selection at A5 4.89–5.11 V; effective sum must remain >=2.2 µF. Common part simplifies qualification; parallel parts do not average worst-case tolerance |
| CIN: Panasonic **EEUFR1H101**, one | 100 µF, ±20%, 50 V; radial Ø8 × 11.5 mm, 3.5 mm pitch | Conditional selection; positive to VIN_SW. 0.870 A RMS at 100 kHz/105 C; impedance <=0.061 Ω at 100 kHz/20 C |
| COUT: Panasonic **EEUFR1C102**, one (not the L suffix) | 1000 µF, ±20%, 16 V; radial Ø10 × 16 mm, 5 mm pitch | Conditional selection replacing unspecified 820 µF. 1.790 A RMS at 100 kHz/105 C; impedance <=0.028 Ω at 100 kHz/20 C. Buck stability is not established by these ratings |

### Clock reservoir

[KEMET T491, T2005_T491, 2026-07-08](https://content.kemet.com/datasheets/KEM_T2005_T491.pdf),
pp.2–3, 9, 14: selected row has ESR <=0.8 Ω at 100 kHz/25 C,
ripple 433/390 mA RMS at 25/85 C, leakage 5.3 µA at rated voltage/25 C after
five minutes. Temperature qualification allows ±10% C at -55/+85 C and
10 times initial leakage at +85 C; endurance allows ±10% C and 1.25 times leakage.
Use **6.625/66.25 µA** as room/hot *screening reserves*, including that endurance
factor, without claiming combined lifetime qualification or a 30 C maximum.
The 16 V rating gives 5.11/16=31.94% voltage utilization, below the 50% guideline.

Engineering stack: 33 × 0.9³ = **24.057 µF** minimum and 33 × 1.1³ =
**43.923 µF** maximum (initial tolerance, temperature, endurance). This fits
22–60 µF and leaves 2.057 µF lower margin. Actual low-frequency DC transient C,
combined stress and bias retention must be confirmed; separate qualification
rows are not a combined guarantee. Do not infer effective C from 100 kHz ESR.

With the retained 1k ±1% RCLK, the stacked minimum and a 5.11 V step give
0.21456 V/ms; adding the existing 100 µA load envelope gives **0.21871 V/ms**
falling slew, below 0.5 V/ms. Initial charging is <=5.162 mA. The nominal
steady rail floor remains 4.89 − 100 µA × 1010 = **4.789 V**. The hot reservoir
reserve plus UOE 10 µA and disabled UXO 1.1 µA consumes **77.35 µA** of the
100 µA envelope. The remaining 22.65 µA must cover other VCLK losses and
startup/enabled-clock demand; it is not proof of that demand. Capacitor-short
faults and input steps beyond the declared envelope are excluded.

A 47 µF ±10% alternative with the same three +10% factors reaches 62.557 µF,
above the existing upper limit. This is the reason to choose 33 µF, not merely
its smaller leakage. The discarded Vishay 293D option has its thermal guidance
in [document 40192, 2025-11-05](https://www.vishay.com/docs/40192/typperfmoldchipcaps.pdf)
headed “Typical Performance Characteristics”; KEMET's explicit qualification
limits provide a clearer starting point. Neither grants unlimited service life.

### A5 capacitors

[Murata product data](https://www.murata.com/en-eu/api/pdfdownloadapi?cate=luCeramicCapacitorsSMD&partno=GRM32ER71H475KA88L),
product-search sheet updated 2025-08-23, pp.1–2, identifies the above part and
X7R ±15% temperature class. It explicitly defers detailed guarantees to the
approval specification. Before DC bias and aging, one part screens to
4.7 × .9 × .85 = **3.5955 µF**. Define k as the *combined remaining retention*
after bias, aging and other unaccounted effects, relative to this value.
Input requires **k >=0.278126** at 28 V; the two-part output requires
**k >=0.305938** at 5.11 V. These are qualification thresholds, not claimed
Murata DC-bias figures. Avoid multiplying independent typical curves and calling
the result a guaranteed minimum. Both parts must pass at -40/25/85 C after the
specified aging/de-aging procedure; obtain the approval sheet or qualify lots.

No guaranteed hot insulation-resistance, ESR-versus-frequency or ripple-current
limit for this exact assembly was obtained. Reserve 1/5 µA for all other A5
capacitors/bypasses at room/85 C; **unproved allocation**. Measure each branch's
DC leakage and A5 startup/load-step stability. No series ESR is intentionally
added. TPS709 requires effective >=1/2.2 µF input/output and an appropriate
low-ESR output; exact-part nominal capacitance alone does not close this.
[TI TPS709-Q1, SLVSCE6D, August 2025](https://www.ti.com/lit/ds/symlink/tps709-q1.pdf),
pp.5, 17–19. Local bypass values and CQUAL film topology stay as inherited;
those unspecified parts also remain part of the leakage/temperature inventory.

### Switched buck capacitors

[Panasonic FR-A, ABA0000C1259, 2025-09-01](https://industrial.panasonic.com/cdbs/www-data/pdf/RDF0000/ABA0000C1259.pdf),
pp.1, 4, 6: the selected parts' initial 20 C/120 Hz C ranges are
80–120 µF and 800–1200 µF. Applying the published ±25% post-endurance change
screens to **60–150 µF / 600–1500 µF** at the return-to-20 C test condition;
these are not hot/cold in-circuit minima. Rated-voltage leakage screens are
50/160 µA at 20 C after two minutes. They are behind QP, not additional
always-on loads to add to QP drain leakage. Temperature-dependent C/ESR,
startup and ripple still need qualification. Impedance is not a guaranteed
ESR interval or an ESR minimum. Do not extrapolate a 100 kHz impedance limit
to 260 kHz without evidence.

At B5 <=5.25 V, VIN_SW <=16 V, Lmin=19.8 µH and fmin=225 kHz, ideal CCM
inductor ripple is <=**0.792 A p-p**, hence output-capacitor ripple <=0.229 A
RMS. CIN's baseline 0.375 A RMS requirement (0.75 A output/2 approximation)
fits its 0.870 A catalog rating. These are nominal-topology sizing screens,
not DCM, startup, fault or full-frequency qualification. The 0.75 A sizing
point is not permission to operate the retained inductor at the LM2678 fault
limit. Test powered output at <=0.5 A first, after review.

[TI LM2678, SNVS029L, June 2025](https://www.ti.com/lit/ds/symlink/lm2678.pdf),
sections 7.1.3/7.2, tables 7-2/7-6, pp.12–13, 16, 20: the 5 V/22 µH row
specifies particular series, e.g. Sanyo MV-GX 680 µF/35 V, not any capacitor
above a single capacitance threshold. EEUFR1C102 is **not a listed equivalent**.
Its +22% nominal C versus 820 µF is a bounded standard-value substitution;
retaining wet aluminum avoids an unsupported all-ceramic output substitution.
Obtain a loop model/ESR envelope or regulator-vendor disposition, followed by
load-step/loop verification over temperature. TI's <=40 kHz crossover guidance
is not itself a phase-margin proof. If FR cannot qualify, revisit a listed
series equivalent before changing the inductor or regulator. COUT freeze remains open.

## 2. Bounded semiconductor decisions

**Retain the HC counters.** HEF4060B/HEF4020B replacements each specify
20/150 µA at 5 V/25/85 C versus the existing HC 8/80 µA at 6 V. They worsen
this screen; no division or latch redesign is justified. Sources:
[Nexperia HEF4060B Rev.11, 2024-09-03, static table](https://assets.nexperia.com/documents/data-sheet/HEF4060B.pdf),
[HEF4020B Rev.12, 2024-08-08](https://assets.nexperia.com/documents/data-sheet/HEF4020B.pdf).

**Select UOE Nexperia 74AHC1G17GV as a conditional replacement for
SN74LVC1G17DBVR**, powered by VCLK. SOT753 pin mapping remains NC1, A2,
GND3, Y4, VCC5; verify adapter footprint. It retains Schmitt action and
0–5.5 V overvoltage-tolerant input behavior, including VCC=0. Unloaded ICC
at VCC=5.5 V, inputs at rails: 1 µA at 25 C, 10 µA through 85 C; input
leakage 0.1/1 µA. Minimum operating supply is now **2.0 V**, not 1.65 V.
Its largest tabulated positive threshold is 3.85 V at 5.5 V. Require loaded
ARM >=4.0 V and verify startup/brownout while VCLK crosses 2 V. This saves
9 µA in the room screen; no hot saving is claimed. Its 4.4 V minimum
VOH at VCC=4.5 V/50 µA screens above CLKOE's 0.8×5.11=4.088 V
HIGH requirement; confirm actual OE load and output levels over the rail range.
[Nexperia Rev.5, 2025-03-14, pp.2–5](https://assets.nexperia.com/documents/data-sheet/74AHC_AHCT1G17.pdf).

Retain UGCLK SN74LVC1G97DBVR. A 74AHC1G08 AND would save room ICC but removes
Schmitt input tolerance and introduces a new edge-rate qualification at XO_OUT.
The existing oscillator load/startup gap does not justify that additional change.
[TI SCES416N, January 2017, pp.4–6](https://www.ti.com/lit/ds/symlink/sn74lvc1g97.pdf).

**Propose QP IPD50P04P4L-11 (order IPD50P04P4L11ATMA2) plus DZ
BZX55C10-TAP as a paired conditional change**, not an independent drop-in.
DPAK/PG-TO252-3: gate1, drain2/tab, source3; keep existing source/drain polarity.
IDSS is 1 µA at 25 C and 70 µA at 125 C, VDS=-32 V, VGS=0; the hot value is
specified by design, not production tested. RDS(on) <=17.2 mΩ at -4.5 V/25 C.
**Absolute VGS is +5/-16 V, not ±16 V.** Require measured/proven gate transients
within **-14 to +1 V**, replacing the old 18 V magnitude check for this option.
40 V VDS fits the <=28 V protected-input requirement only after overshoot is
closed. No guarantee is supplied for VGS=-0.2 V at 85 C. Inrush/SOA and hot
resistance remain qualification gates.
[Infineon Rev.1.1, 2019-07-04, pp.1–4](https://www.infineon.com/assets/row/public/documents/10/49/infineon-ipd50p04p4l-11-datasheet-en.pdf).

The lower DZ changes only the existing gate clamp, not topology. BZX55C10
specifies 9.4–10.6 V at 5 mA/25 C; that is not its entire hot I-V curve.
With the retained 10k RGS/1k RG, nominal clamp current at 12/16 V is about
(12−10)/1k−10/10k=1 mA / 5 mA before sink drop. Therefore low-current and
thermal voltage bounds must be established; dynamic impedance at one test
point is not a DC bound. Do not populate the new QP with the old acceptance
criterion. [Vishay BZX55 Rev.2.0, 2024-11-07, pp.1–2](https://www.vishay.com/docs/85604/bzx55.pdf).
Retain IRF4905 for any separately reviewed baseline comparison; it cannot close
the proposed 200 µA hot allocation using its 250 µA/150 C screen.

Nexperia PXP062-60QL and Diodes DMP6023LE were screened but not selected:
their 1 µA IDSS entries are at 25 C; neither reviewed table supplies a hot IDSS
maximum. A better room value is not hot closure.
[PXP062-60QL, 2025-05-20, static characteristics](https://assets.nexperia.com/documents/data-sheet/PXP062-60QL.pdf),
[DMP6023LE DS37199 Rev.3-2, p.2](https://www.diodes.com/assets/Datasheets/DMP6023LE.pdf).

**Retain TPS70950QDBVRQ1 pending low-load qualification.** Its 2.7 µA no-load
and 10 µA at 100 µA load/30 V limits do not bound every load. Its load-regulation
table starts at 100 µA, whereas parked loads may be below that. Require
4.89–5.11 V and <=10 µA ground current over the actual parked load interval,
6–28 V input, -40/25/85 C; obtain manufacturer bounds or documented component
qualification. A permanent 100 µA preload violates the room target.
TPS7B8150QKVURQ1 is not selected: 40 V tolerance does not repair other exposed
parts, and its 3.5 µA no-load/4.5 µA at 0.2 mA specifications do not establish
an all-load bound or equivalent reverse-output protection.
[TI TPS7B81-Q1, SBVS370F, September 2025, p.6](https://www.ti.com/lit/ds/symlink/tps7b81-q1.pdf).

## 3. Condition-specific parked ledger

Acceptance stays **100 µA at 20–30 C / 500 µA at 85 C**, IGN OFF, USB absent,
after cutoff and settling, summed over battery and all separately energized
harness inputs. Table entries below are µA. A5 is an LDO: do not multiply its
load by 5/12. Count current by the entry branch once; QP's drain current already
includes everything subsequently consumed on VIN_SW/B5.

| A5 item | 25 C screen | Hot screen | Conditions / status |
|---|---:|---:|---|
| UCLK CD74HC4060E | 8 | 80 | VCC=6 V, unloaded, inputs at rails, hot -40..85 C [S1] |
| UCOUNT CD74HC4020E | 8 | 80 | Same conditions [S2] |
| ULATCH CD4011BE | 0.25 | 7.5 | 5 V, rail inputs, 85 C [S3] |
| UOR CD4071BE | 0.25 | 7.5 | 5 V, rail inputs, 85 C [S4] |
| USCH CD4093BE | 1 | 30 | 5 V, rail inputs, 85 C [S5] |
| UOE replacement | 1 | 10 | 5.5 V, rail input, unloaded; source above |
| UGCLK retained | 10 | 10 | 5.5 V, rail inputs, unloaded; source above |
| UXO disabled | 0.55 | 1.1 | 5 V, 25 C / TA; not 5.11 V or startup [S6] |
| USUP | 0.5 | 0.5 | Quiescent, no output load [S7] |
| UA5 ground-current reserve | 10 | 10 | Only specified at 100 µA load/30 V; all-load gap |
| CCLK with endurance reserve | 6.625 | 66.25 | Different test conditions, see section 1 |
| **Subtotal, excluding rows below** | **46.175** | **302.85** | Mixed-condition screen, not assembled maximum |

The three CD packages total **1.5/45 µA**: the inherited aggregate is unchanged,
but equal 0.5/15 µA allowances per package would be wrong. The CD4093 is
1/30; the other two are each 0.25/7.5. The old **48.55/236.6** total excludes
CCLK; after UOE's 9 µA room saving and CCLK it becomes the subtotal above.
At A5=5.11 V the 5 V CD table is not a literal bound. Using their next tabulated
10 V values as an engineering screen adds **1.5/45 µA**, giving
**47.675/347.85 µA**. Monotonic interpolation still requires justification;
this is sensitivity analysis, not a supplier guarantee.

| Additional path | Allocation or screen; what prevents closure |
|---|---|
| Logic input leakage | After excluding hard-grounded pins, 26 HC/CD inputs ×0.1/1, two UGCLK inputs ×5/5, UOE ×0.1/1 = **12.7/37 µA**. See connection audit below. Pin limits come from their separate voltage tables; this remains conservative across internal current paths. No incremental mid-level ICC is covered |
| Other A5 capacitors, film CQUAL and bypasses | **1/5 µA allocation**, not specified limits; exact approvals/IR and hot measurements required |
| QMON and UIGN | Pullup/opto leakage plus GPIO backfeed consume A5 current. HOLD_N has 100k to A5; 1 µA leakage drops 0.101 V. IGN_A has 47k down; 0.3 V endpoint permits only **6.320 µA** into that node before filter/input effects. Hot PC817 leakage/CTR at actual LED current is unproved; generic stock does not inherit Sharp specifications |
| QRESET | Off collector leakage can move IGN_RC; on base drive loads BAD. Its share is not silently zero; inspect actual base network, saturation and temperature |
| QP drain/gate | Original IDSS screen **25/250**, replacement **1/70** at different stated conditions. Gate leakage is distinct from drain leakage; replacement's 100 nA gate limit at -16 V/25 C is not a hot bound. Actual off bias must be qualified |
| QI / QS / RGS / RG | Gate-sink allowance **19 µA hot** = QS10 + QI5 + PCB4, the latter two unproved. Through 10.1k, bias is 0.1919 V; absolute budget from 0.2 V is **19.802 µA**. Do not add this same sink current again as QP drain current |
| DZ / entry protection / PCB | DZ across gate-source modifies gate balance, not an independent full-battery parallel drain; TVS-to-ground is a separate battery drain. Include opto insulation, reverse diode paths, flux, connector surfaces and humidity. No chosen TVS has a qualified whole-envelope leakage/energy allocation |
| Interfaces / QREPORT / QH / DOR | Reserve **10/25 µA aggregate** for independent energized signal/service sources; account QH/QMON injection by source. USB absent defines parked test; DOR USB reverse-current test is a separate state. See section 5 |

Connection audit against `MAX_ON_CUTOFF.md` plus its revised clock/filter wiring:
exclude ULATCH12/13 and UGCLK1, which are hard grounded. The remaining
**22 CD inputs +4 HC inputs +2 LVC inputs +1 AHC input =29 pins** are
covered by the allowance. Fanout ownership below prevents forgetting a load
or charging the same input twice. Gate/base resistor currents are separate.

| Driven node | Receiving logic pins (package-local names) |
|---|---|
| ARM | ULATCH6; UGCLK6; UOE2 |
| NARM / SET_N / RESET_N | ULATCH2 + UOR6 / ULATCH1 / ULATCH5 + USCH13 |
| QUAL_N / IGN_Q / BAD | ULATCH8,9 / UOR2 + USCH12 / UOR1,8 |
| BASE_RESET / COUNT1_RESET | UOR5 + UCOUNT11 / UCLK12 |
| EXPIRED / FAULT_RESET / HOLD_N | UOR9 / UOR12 / UOR13 |
| ARM_RESET / IGN_RC / A5 | USCH8,9 / USCH1 / USCH2 |
| PGOOD / CLK32 / UCLK-Q14 / XO_OUT | USCH5,6 / UCLK11 / UCOUNT10 / UGCLK3 |

Normal settled parked states (HOLD released) have ARM=0, NARM=1, IGN_Q=0, QUAL_N=1, BAD=0,
HOLD_N=1, ARM_RESET=1, RESET_N=0, SET_N=1, BASE_RESET=0,
COUNT1_RESET=1 and CLK32=0. EXPIRED may be 0 after cold reset or 1 after
cutoff; cover both. No gate pulldown/base resistor is intentionally driven
HIGH in this state. UIGN/QMON/QRESET leakage and loaded-level ICC are still
extra. IGN_RC/HOLD_N input and discrete leakage can share a current path;
retaining both allowances is conservative until actual-device limits permit
a tighter circuit solution. Measurement instrumentation must not supply them.

The initial all-pin sum was 17.9/44 µA; excluding the three grounded inputs
removes 5.2/7 µA. Corrected A5 screens including the other-cap reserve are
46.175+12.7+1 = **59.875 µA room** and 302.85+37+5 = **344.85 µA hot**,
*before* discrete/opto leakage and mid-level ICC. With the 10 V CD sensitivity
screen these become **61.375/389.85 µA**. LRA-01's A5 allocations 50/250
are **not closed**. These are not lower bounds proving every physical board
fails; they show that this specification-accounting method cannot prove passage.

A possible review envelope is A5 **65/375**, QP **5/75**, gate/protection/PCB
**20/25**, interfaces **10/25** = **100/500 µA**. It requires the replacement
QP and actual low-load/rail limits. The 5 V screen leaves 5.125/30.15 µA for
remaining A5 terms; the 10 V hot sensitivity exceeds that allocation by 14.85 µA.
**Do not adopt this allocation as achieved or overwrite the parent contract.**
The next useful work is obtaining bounds for the identified nodes/parts, not
an unbounded topology search or a relaxed whole-system target.

Sources for retained ledger entries:

- S1: [TI CD74HC4060 SCHS207G, October 2003, pp.3–4](https://www.ti.com/lit/ds/symlink/cd74hc4060.pdf).
- S2: [TI CD74HC4020 SCHS201D, August 2022, p.5](https://www.ti.com/lit/ds/symlink/cd74hc4020.pdf).
- S3: [TI CD4011B SCHS021D, September 2003, PDF p.2 / printed 3-27](https://www.ti.com/lit/ds/symlink/cd4011b.pdf).
- S4: [TI CD4071B SCHS056D, August 2003, PDF p.1](https://www.ti.com/lit/ds/symlink/cd4071b.pdf).
- S5: [TI CD4093B SCHS115D, September 2003, PDF pp.2–3](https://www.ti.com/lit/ds/symlink/cd4093b.pdf).
- S6: [Micro Crystal OV-7604-C7 application manual Rev.1.4, August 2023, pp.5–9](https://www.microcrystal.com/fileadmin/Media/Products/kHzOSC/App.Manual/OV-7604-C7_App-Manual.pdf); conditions carried from the parent review; startup 500 ms is at 3 V/25 C, not all-temperature 5 V.
- S7: [TI TPS3839 SBVS193D, July 2015, p.7](https://www.ti.com/lit/ds/symlink/tps3839.pdf).

## 4. Loaded logic and transistor drive

At the **5 V table point**, CD4011/4071/4093 can source/sink at least
0.42 mA at 85 C for VOH=4.6 / VOL=0.4 V (0.36 mA at 125 C). Unloaded
4.95 V output limits cannot be used for loaded outputs. [S3–S5].

| Node | Demand and disposition |
|---|---|
| ARM → QS 1k/100k, UOE and logic | Resistive load <=51.11 µA at A5=5.11 plus input leakage. 4.6 V at the 5 V table point screens above UOE's 3.85 V threshold. QS gate minimum is reduced by divider and QH collector voltage: no RDS claim based on exactly 5 V gate drive |
| IGN_Q → QREPORT 1k/100k and logic | Same <=51.11 µA resistor load; include all fanout leakage. QREPORT must sink switched GP5 pullup current while preserving LOW |
| BAD → QRESET through 22k | Conservative resistor-only maximum 5.11/21.78k =234.62 µA plus logic inputs, below 420 µA at the 5 V/85 C table point. Initial reset demand ~1.1 mA collector; VBE, saturation and actual A5-min drive remain conditional |
| QH from HOLD | Keep LRA-01 4 mA GPIO allocation / 2.6 V qualification target. Conditional base drive 1.624 mA at VBE=.95 V against forced-beta-10 demand 1.616 mA at 16 V: only ~8 µA margin, not a robust hot proof |
| QMON | At HOLD=2.6 V, VBE=.95 V, base >=25.16 µA versus <=51.62 µA collector pullup demand. Off-state HIGH and injection into released/unpowered HOLD need hot qualification |
| QI | At 12 V raw IGN, assumed DI=.8 V/VBE=.95 V, base >=4.60 mA through 2.2k; ample nominal sink drive. 40 V VCEO and base-resistor dissipation still constrain transient exposure; off leakage under 100k base pulldown is unspecified hot |

Thus at the 5 V point the loads do not justify replacing the CD output stages.
Between 4.89 and 5.11 V, during collapse and with non-rail input voltages,
logic levels **and additional supply current** need bounds. Valid logical HIGH
is not equivalent to the rail-input condition used in ICC tests.

Do not substitute BC846B and call QI/QMON leakage closed: its 5 µA maximum
at 150 C is **ICBO with emitter open**, not ICE with these base pulldowns.
A different package and stronger base pulldown could improve behavior but need
new drive/injection proof; no such change is selected here.
[Nexperia BC846 Rev.9, 2012-09-25, pp.2–4](https://assets.nexperia.com/documents/data-sheet/BC846_SER.pdf).
Retain identified onsemi 2N3904 for characterization, not anonymous kit equivalents.
[onsemi 2N3904, electrical table](https://www.onsemi.com/pdf/datasheet/2n3904-d.pdf).

Oscillator supply startup peak, start time at actual VCLK/-40..85 C, and total
XO_OUT capacitance remain unresolved. Retain <=10 pF specified-edge test load
and <=15 pF specified module load maximum, including adapter, buffer and probe. Enabled
C×V×f at 10 pF/5.11 V/32768 Hz is **1.674 µA**, excluding internal dynamic and
startup current. It cannot certify the 100 µA VCLK envelope. Obtain manufacturer
maximums where possible, then measure ramps and clock with a low-C probe.

## 5. Protection, isolation and bounded fixture

R02 stays open: P12/P_AON **<=28 V including overshoot**, nonnegative at UA5;
TPS709 recommended maximum 30 V/absolute 32 V. Reject the old 1.5KE30A's 41.4 V
clamp as sole protection. 1.5KE20A's 27.7 V table point leaves only 0.3 V to target;
it is not selected as a completed protection solution. Keep controlled 12–16 V
operation as the planning envelope. Required owner inputs for eventual vehicle
qualification: exact feed, source/harness impedance and inductance, expected
jump-start/crank behavior, pulse amplitudes/durations/repetition/temperature,
wire sizing and fuse interrupt/clearing curves. No invented automotive pulse
standard or TVS wattage label resolves these inputs. IGN needs separate
coordination; 28²/990=0.792 W exceeds the inherited 0.5 W RLED.
[Vishay 1.5KE, clamp table/pulse derating](https://www.vishay.com/docs/88301/15ke.pdf).

LRA-03/04 requirements remain **aggregate <=10/25 µA** from all independently
energized interface sources, including off-state divider loading and leakage
through unpowered I/O. Tentatively reserve 8/20 µA for the five vehicle branches
and 2/5 µA for future bus/service; reviewers may redistribute within the total.
An equal five-way split is only 1.6/4 µA per branch, not a part specification.
Power-off 3V3/B5 must remain<=0.3 V under the parent decay checks. Disconnect
upstream of dividers; downstream buffering alone leaves 218/417 µA illustrative
12 V VSS/tach loading. Preserve B16/PGND and ON-state analog loading accuracy.
No bus or as-built design is introduced here.

DOR **1N4004-E3/54** remains the parent conditional selection. Its cold forward
voltage, temperature rise and USB reverse-recovery/load-step behavior are
unmeasured; the new COUT increases stored charge and must be included. USB
backfeed testing must cover **VIN_SW as well as B5**: QP's body diode permits
reverse flow from drain toward P12 if another source energizes the switched
stage. The switch is not bidirectional isolation.

At the post-endurance COUT screen of 1500 µF and RB5=1010 Ω, isolated
bleeder-only decay 5.25→0.3 V takes **4.336 s**, before input-stage support.
A separate CIN 150 µF/RBIN10.1k decay 16→8 V takes **1.050 s**. Adding them
as a pessimistic sequencing screen gives **5.386 s**, beyond the parent 5 s
criterion. Buck loading changes that sequence; this is not proof of an actual
failure. It demonstrates why the larger COUT cannot inherit five-second decay
acceptance without full-circuit analysis/measurement. Additional leakage can
also leave a nonzero final rail voltage.

Proposed fixture sequence for a future authorized, reviewed bench session:

1. No Pico, SD, vehicle harness, bus/debug or USB. Fit identified parts on a
   reviewed fixture; check polarized CCLK/CIN/COUT and QP/QS pinouts. Remove
   all five energized signal branches upstream of their dividers. Open JH.
   Use isolated regulated 12 V battery simulation with **50 mA current limit**
   for A5/disarmed checks; log supply limiting and wait at least five minutes
   before leakage readings. Limiting during startup is not a valid pass.
2. Separate regulated IGN simulation 12–16 V, **30 mA limit**, common fixture
   ground. After polarity/no-short/A5 review, allow battery source **250 mA**
   for unloaded startup. Use **500 mA maximum input limit** for reviewed
   output load steps up to 0.5 A. If limiting interferes, stop and investigate;
   do not silently increase it or substitute a real battery. These source limits
   do not protect against discharge of capacitors already on the board.
3. Record A5, VCLK, PGOOD, IGN_RC, ARM, QP VGS, VIN_SW and B5 on slow/fast,
   interrupted and partial ramps. Check A5 effective C, clock start/load and
   <=0.5 V/ms slew; retention<=900 ms for one-second IGN requires the separate
   firmware fixture/reviewer. New QP gate must stay -14..+1 V.
4. Measure branch currents at 12/16 V and 20/25/30/85 C, before/after cutoff,
   including stuck HOLD, reset, JH open and unpowered GPIO. Test QP at actual
   VGS=0 and worst permitted -0.2 V. Log temperature at parts, meter burden,
   uncertainty, settling and leakage floor. Remove instruments/probes that
   load current-sensitive nodes for the final current reading.
5. Only after electrical review, separately test Pico/SD and USB insertion,
   removal, DOR heating/recovery, VIN_SW/B5 decay and power-off injection.
   Repeat with actual reviewed LRA-03/04 interfaces before claiming whole-system
   100/500 µA. The disconnected fixture cannot earn vehicle acceptance.

No bench tests were performed here. A supply current limit does not prove QP
SOA, buck fault survival, fuse coordination or circuit safety under faults.

## 6. Closure map and proposed contract corrections

| Item | Disposition / next evidence / responsible review |
|---|---|
| Exact capacitor candidates; nominal/ripple screens | Supported selections within stated conditions; electrical reviewer accepts BOM delta |
| CCLK effective range | Conditional 24.057–43.923 µF engineering stack; obtain combined-stress/DC bounds and measure actual ramps/leakage |
| A5 ceramics | Unresolved approval-sheet bias/aging/IR/ESR; explicit retention thresholds above; then assembly stability tests |
| CIN/COUT | Catalog sizes/ripple supported; unresolved temperature impedance and FR-to-LM2678 loop compatibility; vendor/model then loop/load-step tests |
| A5 low-load and hot current | Unresolved manufacturer bounds/qualification, supplier limits for the audited nodes and physical measurements; no preload workaround |
| QP + DZ alternative | Conditional paired change; revised asymmetric gate limit, actual off-bias leakage, hot clamp and inrush/SOA evidence required |
| QI/QS/QMON/QRESET/opto | Unresolved actual-network hot leakage/drive; ICBO substitution is insufficient; select/qualify only offending devices |
| Protection / harness | Owner exposure inputs genuinely required for vehicle closure; bounded paper fixture work can proceed independently |
| Firmware R01 | Independent review still pending: GP6 4 mA/2.6 V, early HOLD, shutdown generations/clock/SD policy/qualified IGN. No implementation or acceptance inferred |

Proposed contract addendum: CCLK 33 µF selection and qualified bounds; UOE 2 V
minimum operating rail; paired QP/DZ option with -14..+1 V gate acceptance;
COUT 1000 µF and repeat decay/inrush; current-ledger corrections/omissions and
possible allocations. **No changes to GPIO, polarity, timer division or
1770/1800/1801 s policy are proposed.** Firmware reviewer should verify startup
budgets remain feasible with actual clock/A5 behavior, rather than treating this
component package as approval of the LRA-01 candidate.
