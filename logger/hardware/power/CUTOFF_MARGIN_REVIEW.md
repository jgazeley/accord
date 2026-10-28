# Cutoff margin review — continuation of 8937ccb

October 25, 2026. Remote calculations and manufacturer-document review only.
This document controls the changes listed here over the earlier candidate.
It is not an as-built record. `MAX_ON_CUTOFF.md` retains the latch and counter
connections; the replacement blocks below remove the bare-crystal oscillator,
diode-precharge ignition filter and TPS7A16 supply proposal.

## Disposition

| Question | Design decision | Remaining limitation |
|---|---|---|
| Temperature-rated clock | OV-7604-C7, 32.768 kHz, ±20 ppm, TA, QC; external-clock mode on HC4060 | Verify startup over temperature and populated clock capacitance |
| Clock supply ramps | Separate RC-filtered oscillator rail and overvoltage-tolerant logic interfaces | RC capacitance is an effective-capacitance requirement; verify actual part and ramps |
| False IGN at startup | Filter voltage now rises for ON; reset actively discharges it | Saturation/leakage endpoints and transient propagation require qualification |
| Two different IGN decisions | One hardware-qualified signal drives the cutoff and proposed GP5 input | Firmware-owner acceptance/implementation remains required |
| LDO output-to-input collapse | Replace TPS7A16 with TPS70950QDBVRQ1 | Requires a protected input; the old 41.4 V TVS proposal is incompatible |
| Gate drive with 10k RGS | Recomputed divider, initial current, clamp-current range and dissipation | Zener behavior at low current and hot transistor behavior need measurements |
| Parked current | Explicit conditional budget; no claim that 40 µA timer allocation is closed | Datasheet maxima do not yet prove the entire 100/500 µA target |

The remaining limitations are deliberately specific. Temperature-qualified
parts and paper calculations can be selected remotely. Clock startup,
assembled leakage, interference and power ramps cannot be certified remotely.
Some production choices below still require engineering or manufacturer
limits, not just a request for a bench reading.

## 1. Clock replacement and interfaces

Select **Micro Crystal OV-7604-C7-32.768KHZ-20PPM-TA-QC** on an adapter.
TA covers −40 to +85 C. The module integrates the crystal and oscillator;
remove XTAL, RF, RS, CX1 and CX2 from the earlier candidate. Leave HC4060
pins 9 and 10 open and drive pin 11 with CLK32. Division remains unchanged.
Pin numbers below refer to top views, not adapter pad order.

```text
A5 -- RCLK 1k/1% -- VCLK
VCLK -- CCLK -- GND         [effective capacitance 22–60 uF over conditions]
VCLK -- 10nF -- GND        [local oscillator bypass]
UXO OV-7604: 4=VCLK, 2=GND, 3=CLKOE, 1=XO_OUT

UOE SN74LVC1G17DBVR: 5=VCLK, 3=GND, 2=ARM, 4=CLKOE, 1=NC
UGCLK SN74LVC1G97DBVR: 5=A5, 2=GND,
    1(In1)=GND, 6(In2)=ARM, 3(In0)=XO_OUT, 4(Y)=CLK32
CLK32 -- HC4060 pin 11
Each logic buffer gets 100nF directly across its own supply.
```

UGCLK is configured as AND, so disarmed means CLK32=0. UOE translates ARM
to the filtered rail without injecting A5 into the oscillator's enable pin.
When A5 collapses, UGCLK accepts the temporarily higher XO_OUT voltage at its
input; its output shares A5 with the counter. The Schmitt input accepts the
oscillator's edge rate. UOE's input likewise accepts ARM when VCLK is still
ramping. Do not substitute a conventional CMOS gate with input-to-VCC clamps.
Sources: [TI SN74LVC1G17](https://www.ti.com/lit/ds/symlink/sn74lvc1g17.pdf),
[TI SN74LVC1G97, pinout, thresholds and function table](https://www.ti.com/lit/ds/symlink/sn74lvc1g97.pdf).

The oscillator specifies a maximum supply slew magnitude of 0.5 V/ms.
For a 5.11 V rail step and minimum RCLK/CCLK, the RC contribution is
0.235 V/ms. Allowing a **100 µA maximum VCLK load** adds 0.0046 V/ms on
falling ramps, still below 0.5 V/ms. The same 100 µA allocation gives at most
0.101 V static drop. This is a circuit envelope, not an asserted maximum
module startup current: verify that allocation, including UOE, experimentally
or obtain a manufacturer bound before claiming the ramp requirement closed.
An external short directly on VCLK is outside this RC ramp calculation.

At A5=4.89 V and the allocated drop, VCLK>=4.789 V; oscillator VOH>=4.389 V
at its specified load. UGCLK's listed positive threshold is at most 3.33 V
at 5.5 V. Keep total XO_OUT load <=10 pF for its specified edge-rate test;
15 pF is the module's output-load maximum. Adapter, buffer and probe
capacitance all count. CLKOE low makes XO_OUT low while the internal
oscillator continues running. Disabled current is specified at 0.55 µA
maximum at 5 V/25 C, 1.1 µA at 5 V over TA; enabled output adds C*V*f.
Startup is specified as 500 ms maximum at the table's 3 V/25 C default,
**not an all-temperature 5 V startup guarantee**.
[Micro Crystal application manual, sections 2–3](https://www.microcrystal.com/fileadmin/Media/Products/kHzOSC/App.Manual/OV-7604-C7_App-Manual.pdf).

Conservatively sum 20 ppm initial error, 188.65 ppm temperature curvature
(−40 C versus +30 C turnover), 3.75 ppm voltage allowance and 3 ppm
first-year aging: round to **±220 ppm for first-year timing calculations**.
This is an engineering envelope assembled from the separate specifications,
not a new manufacturer combined guarantee or a lifetime aging bound. With
one 2 Hz edge allowance and 1 s startup allowance, expiry computes to
2047.05–2049.95 s from qualified IGN loss, inside 32–40 minutes. The 1 s
startup allowance remains a qualification condition. Clock failure is still
an uncovered fault of this single-clock safeguard.

## 2. IGN polarity, reset and shared decision

Use **one** PC817 in the A5 domain. Revision A's IGN LED resistor, LED and
reverse clamp remain; do not add the second series LED from the first cutoff
draft. Disconnect the old opto collector-to-GP5 connection. Rewire its output:

```text
UIGN collector(4) = A5; emitter(3) = IGN_A
IGN_A -- 47k/1% -- GND
IGN_A -- 220k/1% -- IGN_RC
IGN_RC -- 1uF film/5% -- GND
USCH A: pin1=IGN_RC, pin2=A5, pin3=QUAL_N
ULATCH C: pin8=QUAL_N, pin9=QUAL_N, pin10=IGN_Q
ULATCH D remains unused: pins12,13=GND; pin11 open.

BAD -- 22k/1% -- QRESET base; base -- 100k -- GND
QRESET emitter = GND; collector -- 4.7k/1% -- IGN_RC
QRESET = onsemi 2N3904 (E=1, B=2, C=3)
Remove the earlier DBOOT diode and its series 1k resistor.

IGN_Q -- 1k -- QREPORT gate; gate -- 100k -- GND
QREPORT = Nexperia BSS138P: gate1, source2=GND, drain3=GP5
GP5 -- existing 10k -- switched Pico 3V3
```

Retain USUP **TPS3839K50DBZR**: pin1=GND, pin2=PGOOD (its active-low
RESET output), pin3=A5, local 100nF across supply. PGOOD feeds USCH B as
shown in the main connection table. Its falling threshold is 4.271–4.446 V
over the specified temperature range; reset releases after 120–350 ms.
The falling propagation delay is specified as 20 µs typical, without a
maximum in that table. Thus arbitrary fast collapse is not proven by a
worst-case propagation bound. Test slow/fast and partial ramps; logic below
its operating range is not covered by the Boolean model.

Empty IGN_RC now means OFF. QRESET forces a previously charged capacitor
toward OFF while BAD is high. With 5.11 V on the opto side, 0.2 V assumed
QRESET saturation, and +1% discharge/−1% charging resistors, the reset
endpoint is approximately 0.305 V before input leakage. Including a 1 µA adverse input leakage
allowance adds less than 5 mV. The worst RC time to fall from 5.11 to 0.9 V
is about 10.3 ms, versus the supervisor's **120 ms minimum** release delay.
These results are conditional on the transistor saturation bound at the
actual drive/temperature; they do not promote its 25 C test limit into a hot
guarantee. QRESET base drive is about 0.16 mA using a 4.5 V BAD output and
0.85 V VBE; initial collector demand is about 1.1 mA. No weak diode-charge
path is being relied on to preset the Schmitt input high.
[TI TPS3839 timing](https://www.ti.com/lit/ds/symlink/tps3839.pdf),
[onsemi 2N3904 electrical conditions](https://www.onsemi.com/pdf/datasheet/2n3904-d.pdf).

For short brownouts the reset timer must actually trigger; a disturbance
filtered out by the supervisor cannot be treated as a guaranteed reset.
The requirement is no false rearm on recovery when IGN is absent. Test this
with IGN_RC initially charged, not just a fully discharged cold start.

At a 5.0 V test rail, the CD4093 single-input thresholds span VP=2.2–3.6 V
and VN=0.9–2.8 V. Require the complete filter's steady endpoints, including
all opto/gate/PCB leakage, to be ON>=4.5 V and OFF<=0.3 V. Under those
conditions, the calculation gives approximately 104–376 ms ON qualification
and 119–590 ms OFF qualification **starting from settled endpoints**.
An edge immediately after a previous transition need not meet those times.
This range uses component tolerances and
the 5 V threshold table; **it is not a guaranteed bound across the full
A5 range**, because that datasheet does not tabulate every intermediate
supply. Test 50 ms rejection and 1 s recognition at supply/temperature
corners; repeated bursts also require a test, since RC networks accumulate
charge. The deadline always uses the resulting qualified edge.
[TI CD4093B, single-input conditions](https://www.ti.com/lit/ds/symlink/cd4093b.pdf).

The PC817's CTR and saturation limits are specified at particular current,
voltage and temperature points. The proposed emitter load is about 0.11 mA
plus the RC charging current; the LED circuit supplies at least about 6.5 mA
at the 9 V input calculation point. This is useful drive margin, not proof
of the 4.5 V endpoint for unidentified kit optos over temperature. Reject a
stock part that cannot meet the endpoint/leakage conditions or select a
fully specified replacement before production.
[Sharp PC817 electrical characteristics](https://global.sharp/products/device/lineup/data/pdf/datasheet/PC817XxNSZ1B_e.pdf).

**Proposed firmware contract:** GP5 LOW is this same IGN_Q decision, translated
to switched 3V3 by QREPORT. Firmware polls at <=10 ms and uses the first
observed qualified OFF edge for its 1800 s deadline. Do not independently
accept a shorter raw IGN pulse or apply a separate 100 ms rearm rule. Keep
the first edge time through any software noise handling. This changes the
meaning of GP5 to hardware-qualified ignition and requires explicit firmware
owner acceptance, including the recorded `ign` column's semantics. There is
no extra GPIO reservation and no firmware edit in this package. QI's direct
electrical IGN startup path remains independent of the qualification delay.

At cold boot, qualified IGN may arrive later than the former 100 ms HOLD
deadline. Assert HOLD promptly once qualified ON is observed, before blocking
initialization; budget the complete cold-start path against the >=1 s IGN
startup requirement. The old 100 ms-from-3V3 contract cannot be retained
unchanged with this filter. At USB-only power with A5 absent, QREPORT is off,
GP5 is high, and firmware must leave HOLD released.

## 3. Always-on supply boundary

Select **TPS70950QDBVRQ1**, SOT-23-5: pin1 IN, pin2 GND, pin3 EN open,
pin4 NC open, pin5 OUT=A5. Do not substitute TPS709A/B pinouts. EN may float
to enable; do not tie it to battery. Use local input capacitance >=1 µF
effective and output capacitance >=2.2 µF effective, low-ESR ceramic; proposed
starting values are 4.7 µF/50 V input and 10 µF/16 V output, with DC-bias
and tolerance data required for exact procurement. Add local logic bypasses.

Input node **P_AON** must be 6–28 V for this design envelope, nonnegative
and <=30 V during transients at the IC. Controlled 9–16 V testing may feed
P_AON from P12. Vehicle use requires a coordinated upstream limiter/clamp:
the old 1.5KE30A's 41.4 V specified clamp is **not compatible**. This is an
explicit input contract, not a claim that vehicle surge protection is now
implemented. The separate power-protection task must meet it or replace
this regulator deliberately.

The device blocks OUT-to-IN current when OUT exceeds IN, with the documented
caveat below 1.8 V output. This removes the earlier TPS7A16's OUT<=IN+0.3 V
constraint from the selected supply. Typical 10 nA reverse leakage is not
a maximum. A5 droop still triggers the supervisor and invalidates arming;
reverse-current blocking does not preserve permission through a brownout.
The accuracy/line/load tables support using 4.89–5.11 V as a calculation
envelope **where their load conditions apply**. Below 100 µA the full load
regulation limit is not specified; parked A5 still needs checking.
[TI TPS709-Q1, pinout and sections 5–6](https://www.ti.com/lit/ds/symlink/tps709-q1.pdf).

## 4. Gate drive and leakage accounting

Retain QS=BSS138P, QH=2N3904 and RGS=10k/1%. For the un-clamped model,
`|VGS(QP)| = (P12 - VCE(QH))*RGS/(RGS+RG+RQS)`. Using VCE=0.2 V,
RQS=10 Ω and nominal resistors gives 7.99/10.72/14.35 V at P12=9/12/16 V.
The last value enters the zener region; it is not the expected regulated
gate bias. At 12 V, −1% RGS/+1% RG retains approximately 10.70 V in this
conditional model. Thus 9 V remains a characterization point; do not claim
the IRF4905's −10 V on-resistance specification there.

At 16 V and an assumed 11.4–12.7 V zener voltage, RG current is roughly
3.1–4.4 mA, of which about 1.1–1.3 mA flows in RGS. The resulting zener
current is only about 1.8–3.3 mA, below its 5 mA voltage test point. Its
11.4–12.7 V table range therefore remains **an illustrative assumption**.
Scope VGS rather than claiming the zener tolerance is guaranteed here.
The initial RG current is bounded by 16/990=16.2 mA. A clamp short gives
<=16²/990=0.259 W in RG, retaining the 0.5 W part. Maximum RGS dissipation
at 16 V is 16²/9900=25.9 mW, so a rated 0.25 W axial part is ample for
this bench envelope. The QH base-drive allocation remains adequate for
these currents under the original 25 C saturation assumptions.

The 0.2 V off-gate limit with RGS+1% permits 19.80 µA **total** sink leakage.
For a faulted QH, allocate 10 µA to QS (its 150 C/60 V IDSS limit), 5 µA
to QI and 4 µA to PCB/other paths: 19 µA would give 0.1919 V. The latter
two figures are **acceptance allocations, not guaranteed datasheet maxima**.
The original QI datasheet does not supply the needed worst-case hot limit
under this actual base network. A guaranteed hot design needs a suitably
specified replacement or documented qualification; the whole budget is not
closed by citing QS alone. QS's RDS limit is at VGS=5 V; ARM drive below
that also needs qualification. These are remaining production design gaps.

## 5. Parked-current ledger and completion boundary

| Path | Room-temperature screening, µA | 85 C screening, µA | Meaning |
|---|---:|---:|---|
| Two HC counters | 16 | 160 | Static maxima at datasheet test rail |
| Three CD4000 gate packages | 1.5 | 45 | Static maxima at 5 V; intermediate filter voltages may increase current |
| UOE and UGCLK | 20 | 20 | Rail-input static maxima; excludes transition and intermediate-input current |
| Oscillator disabled | 0.55 | 1.1 | Specified at 5 V; count its filtered supply/load conditions |
| Supervisor | 0.5 | 0.5 | Output unloaded specification |
| LDO ground current reserve | 10 | 10 | Specified maximum at 100 µA load/30 V; not a bound for every load |
| Subtotal | 48.55 | 236.6 | Not the whole logger and not a guaranteed assembled maximum |

The former **40 µA timer allocation is not demonstrated and the static
screening sum already exceeds it**. Do not silently raise the whole logger's
100/500 µA targets. Additional input leakage, off switches, opto dark current,
capacitors and external interfaces remain; UOE's high-input current can also
increase if ARM is too far below its local supply. Parked ARM and clock are
low, but IGN/HOLD sense endpoints must be checked for excess CMOS current.
This design can be prototyped against the target; a guaranteed worst-case
budget requires lower-leakage logic choices or revised allocations elsewhere.

Remote completion: selected clock and supply interfaces, removed false-ON
capacitor polarity, specified the shared-IGN contract, and recomputed gate
and RC margins. Still open as **engineering**: exact capacitor effective-C
proof; production hot QI/QS limits; all-load LDO/current budget; complete
vehicle input protection; owner acceptance of the revised firmware contract.
Still open as **physical validation**: actual clock startup, reset ramps,
opto endpoints, timing, leakage, gate/clamp waveforms and connected-system
behavior. Do not report either list as completed by the Boolean tests.

## Reproducible checks

Run `python3 logger-power/check_cutoff_margins.py` for the input assumptions,
computed values and eight arithmetic/interface checks. Run
`python3 logger-power/check_max_on_logic.py` for the eleven settled-logic
checks. All 19 pass in this remote continuation. They establish consistency
under the listed assumptions, not component qualification or measured results.
