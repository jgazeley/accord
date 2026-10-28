# Prototype test plan — revision A, 2026-10-25

**All physical tests below are PENDING.** No connected hardware was controlled
in this engineering session. Each test requires physical owner participation
for assembly, connections and observations. Firmware tests additionally require
a separate firmware-owner candidate; deployed v0.6.0 and built v0.7.1 have no
HOLD feature. Never present a switch driven by a jumper as a firmware test.

## Equipment and connection order

Known inventory: Fluke 117 and Siglent SDS1202X-E, two channels. Scope location
has moved between VM and jaypi; `inventory/tools/SCOPE.md` is setup guidance,
not proof of present access. Needed but not confirmed: regulated isolated
current-limited supply, power resistors/electronic load, temperature probe,
low-current shunt with suitable resolution, short fused test leads. No car
battery or vehicle signal harness for initial tests.

1. Photograph and record actual part markings, values, transistor orientation,
   capacitor polarity/rating, fuse and connector pinout. Use DESIGN §3's
   connection schematic. Verify diode bands by net, especially TVS K=P12,
   A=PGND. Check shorts with supply/USB disconnected.
2. First build **only the latch**, omitting UREG and its passives. PSU to P12
   and PGND; 100 ohm/5 W resistor from VIN_SW to PGND. Supply initially 12 V,
   limit 0.25 A. IGN via DI/RI from an independent switch on the same supply;
   HOLD from a separate 3.3 V source with common PGND. Do not apply 12 V to
   HOLD or a Pico GPIO. Both controls initially low; JH fitted.
3. Add the protected-input network and compact soldered buck only after the
   latch passes. Connect PSU -> F1 -> BATT_IN, PGND return. Start at 12 V,
   0.25 A limit, no Pico, no external signals. If startup hits the current
   limit, capture it; increase in controlled steps to **1 A maximum** for
   this prototype. Measure before connecting a valuable load.
4. Load B5 with 100 ohm/1 W (~50 mA), 20 ohm/5 W (~250 mA), then
   10 ohm/10 W (~500 mA), or equivalent electronic load. For the 750 mA
   transient use a timed electronic load; do not approximate its duration
   with a handheld resistor. Confirm temperatures and B5 regulation first.
5. Only then connect DOR -> Pico VSYS, dedicated UIGN -> GP5 and proposed
   HOLD -> GP6. Remove Pi shared-GP5 wire and all other signal inputs; keep
   hondaPico disconnected from the experiment. SD is on Pico 3V3. A dummy
   load proves the buck, not the Pico regulator's SD/radio budget.

```text
isolated PSU -- F1 -- DREV -- latch -- onboard buck -- DOR -- VSYS
    PGND -------------------- PGND ------------------------ Pico GND
switched test IGN -- FIGN -- dedicated startup driver + opto -- GP5
Pico GP6 --------------------- JH / HOLD driver
```

Ordinary grounded scope probe clips go **only to PGND**. To measure VGS use
CH1=GATE, CH2=P12, both ground clips at PGND, then CH1-CH2 math. Do not clip
scope ground to the high-side source. For buck switching/ripple use short
ground springs, 10x probes; verify attenuation settings. Check supply/USB
earth relationships before connecting them.

## Test points and instrument settings

| Measurement | Suggested setup | Expected / pass criterion |
|---|---|---|
| Gate assertion/release | 10x, DC, 5 V/div, 1 ms/div; trigger GATE falling/rising; math VGS | On VGS -10 to -14 V at P12 12–16 V; off within 0.2 V of source; magnitude of VGS must remain below 18 V |
| Startup rails | CH1 VIN_SW 5 V/div, CH2 B5 1 V/div; 20 ms/div, single shot | B5 4.75–5.25 V, no repeated restarts; record time to valid 3V3 in separate repeat |
| B5 ripple | AC coupling, 10–20 mV/div, 20 MHz bandwidth limit, short spring, 2 us/div | <=100 mVpp at each steady load; no growing oscillation |
| Load step | DC, B5 plus load trigger, 1 ms/div then 100 us/div | 50->500 mA and 500->750 mA/100 ms remain 4.75–5.25 V; no sustained ringing |
| Logic levels | DC 1 V/div, capture IGN_N and HOLD in repeat runs | IGN_N <=0.4 V ON, >=3.0 V OFF; HOLD high >=3.0 V, low <=0.3 V |
| Power release | DC, B5 then VSYS/3V3 repeat; 1 s/div or roll | All three <0.3 V within 5 s with USB and signals removed; no reassertion |
| Heating | Temperature probe; 30 min at 500 mA, 25 C ambient | Part temperature rise <=30 C as bench screening; all stay below rated limits with margin; no extrapolated vehicle qualification |

The scope's recorded waveform download limitations at slow timebases mean
one long capture may not be retrievable. Use triggered short captures at
transitions plus time-stamped DMM/logger records for 30-minute intervals;
do not claim an unseen long waveform was captured.

## Execution and pass/fail matrix

| ID | Procedure | Acceptance / interpretation |
|---|---|---|
| P01 | Latch-only: IGN=0/HOLD=0; test each asserted separately, then both; remove each | VIN_SW powers only when IGN or HOLD active. No flicker when relinquishing IGN with HOLD high. Disconnect HOLD: off if IGN low |
| P02 | Repeat P01 at P12=12, 14.4, 16 V; characterize at 9 V | Gate limits above; record loss at 9 V rather than assuming full enhancement. No controller load yet |
| P03 | Buck unloaded and at 50/250/500 mA, BATT_IN=12/14.4/16 V; 9 V separately | B5 regulation/ripple/temperature criteria. Record input current and efficiency; low-load behavior cannot be inferred from continuous-mode math |
| P04 | Step loads, power up at 500 mA, capture VIN_SW/B5 | No overshoot, instability or current-limit cycling. Record input inrush, duration and QP VDS; check SOA before battery use |
| P05 | Fit candidate firmware; IGN initially OFF, then ON >=1 s; repeat 20 times | No self-start from HOLD while IGN absent; early HOLD assertion <=100 ms after valid 3V3 when IGN present, no wait for USB/Wi-Fi/card; every valid IGN start succeeds |
| P06 | Shortened 60 s timeout; IGN falls with Wi-Fi unavailable, server silent, VSS pulses and serial activity | Release at accepted fall +60 s (+1 s maximum), independent of activity. Short test uses 10 s finalization window; record actual build constants |
| P07 | Repeat with actual 1800 s window and 30 s finalization | No extension; release by edge +1801 s; rails fall as specified. Perform once with healthy storage/network and once with unavailable server |
| P08 | IGN returns at 20 s of short interval, at shutdown entry, and immediately before release; later falls again | Qualified return cancels cutoff; new deadline only on new accepted fall. No loss of power while IGN high. If file already closed, reopen normally |
| P09 | IGN pulses 10/50 ms and stable 200 ms during countdown | Short glitches do not refresh software timer. Stable 200 ms return does; record hardware wake from a short pulse separately, since QI is not debounced |
| P10 | Hardware RUN reset with IGN present; repeat with IGN absent during hold; then rapid reset shorter than capacitor discharge | IGN present remains powered and reboots; IGN absent releases without another hold window or re-latching from residual power |
| P11 | Firmware-owner fault injection stops core 0, core 1 and both separately | Proposed 4 s watchdog resets within 5 s of lost eligibility; IGN absent then powers off. Ordinary healthy SD/Wi-Fi operation does not reset. Record watchdog configuration and feeding core |
| P12 | Fault build keeps HOLD high while continuing valid watchdog feeds | Revision A remains on: record **known uncovered fault**, terminate manually after short test. Production cannot pass until independent inhibit cuts within its 32–40 min bound |
| P13 | Current-limited 3.3 V external HOLD high, MCU disconnected; emulate QH C-E short only on latch-only fixture | Demonstrates pulldown cannot defeat driven-high/shorted driver. Future series inhibit must interrupt it; never fault-inject by shorting a live GPIO to ground |
| P14 | At 12 V nominal, ramp to 9 V and back; then controlled 6 V/100 ms and complete source interruption on isolated bench | 9 V behavior documented; lower voltage may reset. IGN absent must not create a new hold window; IGN present may recover. No latch oscillation; prior files inspectable after recovery |
| P15 | USB only, BATT on/off in separate tests, IGN off, JH open | Pico can run from USB; latch stays off. Measure B5 and VIN_SW leakage/rise; no power delivered to battery connector. JH open must work even with software HOLD stuck high |
| P16 | No USB: unpowered input-isolation fixture, each cluster input energized separately and together | Perform first with dummy clamps/rail load, not real Pico. Verify isolation keeps output <=0.3 V and allocated leakage before attaching unpowered Pico; existing dividers alone are expected to fail |
| P17 | Final automatic isolation fitted: VSS 0/5 V, tach/brake/B11 0/16 V, C11 0/8 V; real harness later | Switched rails remain <=0.3 V when off; normal on-state readings/pulses preserved. Negative/transient tests require separately designed protection; do not apply them directly to these inputs |
| P18 | After off for 60 s, measure parked current at 12/14.4/16 V; repeat at 85 C only with suitable controlled equipment | <=100 uA at 20–30 C, <=500 uA at 85 C with every final normal connection; include both battery/IGN sources. Missing hot data remains pending |
| P19 | No USB, real SD writing and radio transmitting; record rails and file data through normal cutoff | Meets load envelope, no unexpected resets; complete final lines, successful sync/close when card healthy; next boot opens a new valid file |
| P20 | SD absent/unresponsive and uploads stalled at deadline; then deliberate abrupt bench supply loss | Shutdown remains bounded; report possible lost tail. On next boot previous readable prefix and filesystem recovery verified; do not claim guaranteed crash-proof FAT |
| P21 | Compare EN shutdown on a separately populated LM2678 reference: pin7 grounded, VIN retained, output discharged | Record input and output leakage at input/temperature points; compare with complete switched-input stage. This is evidence for a possible architecture change, not permission to modify hondaPico |

For P11, a raw processor reset is not a substitute for a hang/health test.
Record fault-injection time, stale-progress detection, last watchdog feed,
reset/HOLD release and rail collapse separately. The 2 s freshness allowance
and 4 s watchdog are separate intervals; do not report the watchdog period as
the complete fault-to-power-off time.
For P12, a watchdog-fed infinite loop is deliberately different from a dead
core. P16/P17/P18 cannot pass with the first disconnected-signal prototype;
they are later integration gates, explicitly retained here.

For P05/P06/P08/P09, instrument the maximum power-supervision service gap
while exercising ADC reporting, USB absent/attached/backpressured, command
bursts including repeated `l`, and concurrent SD/network work. Verify the
<=10 ms service requirement rather than inferring it from 1 Hz row cadence.
Include IGN return during an outstanding close request; a stale completion
must not close the resumed recording. Startup timing begins at valid 3V3,
not the first application timestamp. These checks require the firmware-owner
candidate and physical timing evidence.

## Current measurement and record format

Use the Fluke current range initially for active current, checking its jack,
range and burden voltage. For parked current, insert a **1k 1% shunt** in
the positive feed *after shutdown*, with a bypass link used during startup:
100 uA gives 100 mV. Measure actual DUT voltage and correct the supply within
the allowed range for shunt drop. Never start the logger through this shunt.
Remove unintended parallel supply paths. Measure shunt voltage with sufficient
resolution to resolve <=10 uA, record instrument accuracy and shunt tolerance;
if the result is close to a limit, uncertainty must fit inside the limit.
Reconnect the bypass before asserting IGN. A USB meter cannot measure the
battery-side parked budget or discover current arriving through a signal wire.

Record per test: date/operator, revision and photos, part substitutions, PSU
voltage/current limit, ambient/part temperatures, firmware identity and timing
constants, wiring including USB/signals, raw captures/readings, calculation,
PASS/FAIL/PENDING and reason. Keep records under `logger-power/evidence/` when
performed. No evidence folder with fabricated readings has been created.

Vehicle tests follow only after independent inhibit, signal isolation,
protection/fuse coordination and buck fault behavior are closed. Planned
vehicle work includes crank/restart, charging/aux switching, ground offsets,
thermal soak and representative driving/vibration. The first bench pass is
not the roadmap's vehicle-duty pass.

## Independent cutoff supplement

Use the staged checks in `MAX_ON_CUTOFF.md` for the new candidate, after
closing its explicitly listed oscillator, supply and reset-precharge design
margins. Revision A's original wiring lacks that circuit. Begin with regulated
A5 and a dummy load, then test the supervisor/IGN front end before the logger.
Include the 64 s accelerated test and a full 2048 s test; cold boot with
HOLD shorted high; partial brownout; HOLD release/reassertion; QH C-E short;
IGN return around expiry; and off-state QP gate bias and current at temperature.
Every physical result remains PENDING. Passing the Python Boolean checks is
not a pass of any electrical test in this plan.

The later `CUTOFF_MARGIN_REVIEW.md` replaces the bare crystal, diode-precharge
IGN filter and TPS7A16 supply. Use its revised BOM/connections. Add checks of
VCLK slew (<=0.5 V/ms), startup, actual buffer load, and IGN_RC reset discharge;
measure qualified GP5 against IGN_Q. The 104–376/119–590 ms calculated filter
intervals assume settled endpoints and the 5 V threshold table; pulse bursts
and supply/temperature corners are separate tests. Record timer-only and
whole-system parked currents: the old 40 µA timer allocation is not proven.
Never apply the earlier 41.4 V clamp envelope to the new <=30 V A5 regulator.
