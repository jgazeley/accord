# Logger onboard power design, revision A — 2026-10-25

**Reviewable bench circuit, not a vehicle-qualified design.** Names and values
below define the first experiment. Outstanding gates are part of this design,
not assumed capabilities. The owner selected an onboard supply similar to
`hondaPico-kicad` during this session.

## 1. Evidence and requirements

| Item | Evidence / requirement / remaining uncertainty |
|---|---|
| Target conversion | Onboard LM2678T-5.0 stage is the reference selected here following owner direction; reuse its topology, not its entire board or unverified substitutions |
| Present supply | `circuits.md`, October 16: trunk auxiliary battery, positive isolated from starter battery, common chassis; 4 A recorder fuse; rear 5.2 V/10 A external buck -> Pi USB -> logger. This is historical installed wiring, not confirmation of the future feed |
| Future feed | Owner confirmed October 25: auxiliary battery for testing; starter battery preferred eventually, with the integrated PCB probably near the gauge cluster. Fuse position, harness gauge/length, connector and ground termination remain open. Do not assume cluster B20/B21 may power this board |
| Assembly | Owner prefers through-hole; surface-mount parts are acceptable. Use adapters where useful for prototyping; package preference does not override electrical requirements |
| IGN | Real IGN ON/START, not ACC or amplifier remote by assumption. Existing logger GP5 is active-low through a Pi-shared opto; replace the shared output for independent power |
| Load | Pico W, SD, future RS-485. No measured logger current envelope. Initial allocation: 5 V, 0.5 A continuous, 0.75 A for 100 ms; measure SD write + radio transmit concurrently. No Pi or actuator loads |
| Normal bench input | 12–16 V at BATT_IN. Also characterize 9 V startup and disturbances, without claiming low-crank ride-through. First switch-only tests use a regulated source directly at P12 |
| Output | 5 V nominal, bench pass 4.75–5.25 V at B5; Pico supplied through DOR into VSYS. 3V3 target 3.20–3.40 V under representative load |
| Startup | IGN held at least 1 s must start. Firmware asserts HOLD within 100 ms of valid 3V3, before network/card initialization; maximum measured cold-start time must leave margin within that 1 s |
| IGN loss | Deadline is first sampled edge subsequently accepted as stable OFF for 100 ms, plus 1800 s. Poll at <=10 ms; do not use the existing once-per-second observation as the power controller |
| IGN return | Stable ON for 100 ms cancels countdown; next accepted OFF starts a new deadline. VSS, tach, Wi-Fi, serial, uploads and RS-485 cannot refresh it |
| Release | Begin shutdown by deadline minus 30 s; release HOLD by deadline +1 s even if storage/network fail. Scope rails: <0.3 V within 5 s, no USB/energized signal paths |
| Reset | IGN present: hardware maintains power and boot may assert HOLD. IGN absent: reset releases HOLD; reboot must not reassert it or start a fresh 30 minutes, even if capacitors keep the CPU alive |
| Parked budget | Proposed acceptance <=100 uA from constant feed at 20–30 C, <=500 uA at 85 C, IGN low, no USB, all normal harness connections. Includes protection, future safeguard and signal paths; not literal zero. 100 uA = 0.072 Ah/30 days |
| Maintenance | USB may deliberately power the logger, but must not power the buck backward or reopen the battery latch. Maintenance disconnect physically opens the HOLD path |
| Independence | hondaPico remains on its own supply. Do not switch common ground or B16 |

Known pin allocation, verified against current `picow-logger.ino` and
`logger_sd.cpp`: GP2 VSS, GP3 tach, GP4 brake, GP5 IGN, GP16–19 SD,
GP26 fuel, GP27 cluster supply; GP23/24/25/29 belong to the radio. GP6
(physical pin 9) is the proposed HOLD pin; GP7 (pin 10) is an alternative.
Reserve GP8/9 and a separately agreed DE pin for future RS-485. These are
proposals, not reservations accepted by the firmware/layout owners. B16 is
ground, not a newly available ADC. The full cluster map identifies B1=tach,
B2=VSS. The roadmap's earlier reversal was corrected in commit `e7415c9`.

Read evidence: root README, ARCHITECTURE power section, HARDWARE_ROADMAP,
PROJECT_HISTORY; logger README/SPEC/source; October 25 v0.7.1 review and
`NOTES-FOR-REVIEW.md` H1–H9; `fuel/NEXT_SESSION.md`, ADC_INTERFACE_SPEC and
CLUSTER_PINOUT. v0.7.1 is built, not flashed. Older SPEC pin/diode tables and
the cluster map's B11/B16 installation status are stale: newer records say
B11/B16 installed and clamps are 1N5819, not BAT54.

## 2. Reference supply and topology choice

`hondaPico-kicad/gen_sch.py:650` and the current schematic/BOM use an onboard
LM2678T-5.0, with a catch diode, inductor and output capacitor. September 24
and October 14 entries in `circuits.md` distinguish the drawn 22 uH/2 A
inductor from the fitted 100 uH axial. October 14 records a successful 5 V
output and bus test after correcting reversed TVS polarity. Neither proves
its stability or protection at this logger's larger, pulsed load.

| Choice | Benefits | Costs / disposition |
|---|---|---|
| P-MOSFET before buck | Removes buck input drain; matches explicit architecture; independent IGN/HOLD paths | New switch, clamp, drivers; leakage/inrush and reverse paths need tests. **Selected for prototype** |
| LM2678 ON/OFF only | Fewer power parts; avoids switching input capacitance | Buck remains on battery; default-on pin requires deliberate fail-off drive; shutdown output leakage matters. Documented ISTBY: 50 uA typical, 100 uA max at 25 C, 150 uA max over temperature, before other losses. Alternative if owner elects to relax switched-input requirement |
| High-side PNP harvest | May use donor devices | Base drive and voltage drop; donor identity/rating and availability unresolved. Not selected |
| Low-side switch | Simple gate drive | USB, B16 and signal returns bypass it; shifts measurement ground. Rejected |

LM2678 reference facts: operating VIN 8–40 V, absolute maximum 45 V; pin 7
low disables, open enables, external voltage must not exceed 6 V. Its
internal pullup is approximately 20 uA. Leave pin 7 open in this input-switched
prototype. Do not connect it directly to IGN, P12, or an unpowered GPIO.
Current-limit upper bound is 8.75 A, so the IC does not protect a 2 A
inductor against all faults. [TI LM2678, §§4–7](https://www.ti.com/lit/ds/symlink/lm2678.pdf).

No second external-buck identification is needed to design this onboard
proposal. The historical TOBSUN/EPBOWPT identity ambiguity concerns existing
equipment only. EN-only comparison requires measuring a populated reference
stage; no shutdown-current measurement is presently recorded.

## 3. Component-level connection schematic

This textual schematic is the authoritative bench connection list; it is not
a KiCad layout or an ERC-checked capture. All grounds below are PGND except
the existing analog reference arrangement discussed in §6. Do not construct
the 260 kHz buck on long solderless jumpers: use a compact soldered prototype
with a ground plane and local input/catch-diode loop.

```text
J1.1 BATT_IN -- F1 -- DREV A>|K -- P12 -- QP source(3)
                                     QP drain(2,tab) -- VIN_SW -- UREG VIN(2)
                                     QP gate(1) = GATE
P12 -- TVS cathode; TVS anode -- PGND       [candidate protection only]
P12 -- C0 100nF/63V -- PGND
P12 -- RGS 100k -- GATE
P12 -- DZ cathode; DZ anode -- GATE        [12 V gate-source zener]
GATE -- RG 1k/0.5W -- SINK
SINK -- QI collector(3); QI emitter(1) -- PGND
SINK -- QH collector(3); QH emitter(1) -- PGND

J2.1 IGN -- FIGN -- DI A>|K -- IGN_POS
IGN_POS -- RI 2.2k/0.25W -- QI base(2)
QI base -- RBI 100k -- PGND
IGN_POS -- RLED 1k/0.5W -- UIGN LED anode(1)
UIGN LED cathode(2) -- PGND
DR anode -- PGND; DR cathode -- UIGN LED anode
UIGN emitter(3) -- PGND
UIGN collector(4) -- IGN_N -- Pico GP5
3V3 -- RIGN 10k -- IGN_N                 [no Pi pullup on this node]

Pico GP6 -- HOLD_RAW -- JH removable link -- RH 1k -- QH base(2)
HOLD_RAW -- RPD 47k -- PGND
QH base -- RBH 100k -- PGND
Open JH for USB maintenance; keep QH base pulldown fitted.

VIN_SW -- CIN 100uF/50V || CIB 100nF/63V -- PGND
VIN_SW -- RBIN 10k -- PGND
UREG LM2678T-5.0: pin4 PGND; pin5 NC; pin7 OPEN
UREG pin1 SW -- L1 22uH -- B5
SW -- DCATCH cathode; DCATCH anode -- PGND
SW -- CBOOST 10nF/50V -- UREG pin3 BOOST
B5 -- UREG pin6 FB                      [Kelvin sense before DOR]
B5 -- COUT 820uF/16V || COB 100nF/50V -- PGND
B5 -- RB5 1k -- PGND
B5 -- DOR A>|K -- Pico VSYS (physical pin39)
Pico GND (pin38) -- PGND; Pico VBUS(pin40) has NO buck connection
Pico 3V3(pin36) -- existing SD supply, subject to measured regulator budget
Pico USB -- onboard VBUS-to-VSYS diode -- VSYS [board's existing path]
J1.2 / J2.2 / ground test loops -- PGND
```

Parts: QP IRF4905PbF; QI/QH onsemi 2N3904 **for the 12–16 V bench only**;
DZ BZX55C12; DI/DR 1N4148; UIGN Sharp PC817XNNSZ1B or a positively
identified/tested stock equivalent; DREV/DCATCH SB360-E3/54; DOR 1N5819;
UREG LM2678T-5.0/NOPB. Proposed input TVS is 1.5KE30A-E3/54, inherited
only as a candidate for protection coordination. F1 is a 1 A bench branch
fuse with a current-limited PSU, FIGN 100 mA at its source. Production fuse
family, DC interrupt rating, time-current curve and wire size remain open.
See BOM for passive tolerances and unresolved exact capacitor series.

Orientation: QP body diode is **drain to source**, so it blocks P12-to-VIN_SW
when off, but does not block reverse energy. DOR blocks USB-to-B5 apart from
leakage. Never infer transistor pinout from another TO-92 bag. For each diode
the band is the cathode; check its net rather than relying on vertical
footprint names. The hondaPico TVS reversal history makes that check essential.

The switch can be tested separately using an isolated 100 ohm/5 W load on
VIN_SW, before the buck exists. Do not use the running hondaPico as a donor or
modify its board to perform this test.

## 4. Calculations and component margins

All numbers here are calculations, not readings. Use 1% resistors unless
otherwise stated. Example supply points refer to P12 unless stated otherwise.

**Switch.** IRF4905 is rated -55 V VDS, ±20 V VGS, 20 milliohm maximum at
VGS=-10 V and the specified test current; thermal RthetaJA is 62 C/W under
datasheet conditions. Numbered pins 1/2/3 are G/D/S; tab is drain.
[Infineon datasheet, pp.1–2 and package](https://www.infineon.com/assets/row/public/documents/24/49/infineon-irf4905-datasheet-en.pdf).
At 0.5 A input, assuming 40 milliohm hot for sizing, P=10 mW. At 1 A,
P=40 mW, estimated rise 2.5 C. These estimates exclude switching/inrush and
are not a hot RDS guarantee. Below |VGS|=10 V, remeasure loss; threshold
voltage is not a full-enhancement rating.

**Gate network.** At P12=16 V and a nominal 12 V clamp, RG current is about
(16-12-0.2)/1000=3.8 mA; 0.12 mA goes through RGS. Zener power is about
44 mW, RG dissipation 14 mW. Initial gate-discharge current is bounded near
16 mA. Even a gate-clamp short leaves RG at <=0.259 W for 16 V and -1%
tolerance, hence 0.5 W. The zener's 11.4–12.7 V range is specified at 5 mA;
our lower operating current does **not** guarantee that range. Measure VGS:
normal target -10 to -14 V at 12–16 V; transient absolute test limit |VGS|<18 V
provides margin below the device limit. [Vishay BZX55](https://www.vishay.com/docs/85604/bzx55.pdf).

**Drivers.** At HOLD=3.3 V and VBE=0.85 V, RH supplies about 2.45 mA,
plus 70 uA in RPD. Design GPIO allocation <=3 mA. At IGN=9 V, conservatively
allowing 1 V in DI and 0.85 V in QI, base current is >=3.2 mA with RI +1%.
At IGN=16 V, RI dissipation is under 0.11 W. Both have ample base current
for the gate-discharge pulse; saturation at these exact conditions is a bench
check. onsemi 2N3904: VCEO 40 V, IC 200 mA, numbered E/B/C=1/2/3.
[onsemi datasheet](https://www.onsemi.com/pdf/datasheet/2n3904-d.pdf).
**These drivers cannot be carried into the proposed 41.4 V clamp envelope.**
Select higher-voltage drivers or a lower coordinated clamp for the vehicle.

**IGN sense.** With 1 V series-diode and 1.4 V LED allowances, 9 V gives
>=6.5 mA through RLED +1%; at 16 V current is <16.2 mA even neglecting diode
drops, and resistor power <0.259 W. A 0.5 W part is deliberate. GP5 pullup
requires only 0.33 mA. Sharp specifies CTR >=50% at IF=5 mA, VCE=5 V,
25 C; do not extrapolate that to a guaranteed saturated VOL over temperature.
Measure <=0.4 V ON, >=3.0 V OFF at the Pico. Sharp pinout A/K/E/C=1/2/3/4.
[Sharp PC817](https://global.sharp/products/device/lineup/data/pdf/datasheet/PC817XxNSZ1B_e.pdf).
DI blocks negative IGN in the controlled bench range; DR limits LED reverse
voltage. This is not a complete vehicle IGN transient filter.
[Vishay 1N4148](https://www.vishay.com/docs/81857/1n4148.pdf).

**Buck current and ripple.** At 5 V/0.5 A and an assumed 80% total efficiency,
input power is 3.125 W; current at 9 V is 0.347 A before extra losses. At
0.75 A output it is about 0.521 A. These are supply-sizing assumptions.
For L=22 uH, f=260 kHz, ideal delta-I=(VIN-5)*5/(VIN*L*f): 0.510 A at
12 V and 0.601 A at 16 V. With L -10%, f=225 kHz and VIN=16 V,
delta-I=0.772 A, giving 1.136 A peak at 0.75 A load. Bourns RLB0912-220KL
is 22 uH ±10%, 0.086 ohm maximum DCR, rated 2.1 A, saturation 2.5 A under
its stated criteria. It provides normal-load margin, **not** protection from
the regulator's much higher fault limit. [Bourns RLB, RLB0912 table](https://www.bourns.com/docs/product-datasheets/rlb.pdf).

At low load, discontinuous operation invalidates the continuous-current
waveform assumption. At 0.5 A, inductor copper loss is roughly 0.024 W using
the worst ripple above. With an illustrative 0.1 ohm COUT ESR, ripple is
about 77 mV plus <1 mV capacitive ripple; hence the 100 mV bench target is
meaningful, not guaranteed. Output-capacitor **series/ESR/ripple rating and
loop stability must be settled**, not just the 820 uF label. CIN ripple
allocation >=0.375 A for the 0.75 A test load. Unmarked kit cans are not a
production BOM. COUT 820 uF is inherited as an experiment starting point.

SB360 is 60 V/3 A, DO-201AD, VF <=0.68 V at 3 A under datasheet conditions.
At 0.75 A output and VIN=16 V, catch-diode average current is approximately
0.516 A; using 0.68 V yields 0.35 W as a sizing estimate. Check lead/case
temperature. [Vishay SB360](https://www.vishay.com/docs/88719/sb320.pdf).
DOR's 1 A rating suits the proposed 0.75 A peak, with measured temperature;
its specified reverse leakage is not zero. Stock Chanzon parts are not
automatically guaranteed to Vishay limits.
[Vishay 1N5819 reference](https://www.vishay.com/docs/88525/1n5817.pdf).

**Discharge and startup.** RB5/COUT alone gives tau=0.82 s nominal; with C
+20%, R +1%, falling from 5.25 to 0.3 V takes 2.84 s. RBIN/CIN gives
tau=1 s nominal, worst 1.212 s, about 4.82 s from 16 to 0.3 V. Additional
capacitance and alternate power sources must be included in measured decay.
The Pico regulator can stop discharging VSYS/3V3 when it reaches dropout;
these rails also need measurements, and a downstream bleeder if they fail.
RGS discharges the MOSFET gate toward its source, not toward ground.
Input-capacitor energy at 16 V is 12.8 mJ for 100 uF; this is not an inrush
current bound. Scope turn-on and check switch SOA and fuse I²t before removing
the bench current limit. No uncharacterized large gate capacitor is used to
slow turn-on into a linear-mode power problem.

## 5. Protection boundary and parked current

F1 belongs at the feed source to protect the wire, before the board. A local
fuse alone leaves the upstream harness unprotected. DREV, TVS and C0 are
always connected; CIN and the buck are downstream of QP, avoiding CIN's
electrolytic leakage in the parked budget. Do not copy the hondaPico battery
ADC divider onto P12 without counting its continuous current.

The hondaPico 1.5KE30A candidate has 25.6 V standoff and 41.4 V clamp at
36.2 A for its specified pulse; its 1500 W headline applies to a 10/1000 us
waveform. [Vishay 1.5KE](https://www.vishay.com/docs/88301/15ke.pdf).
That is not a universal bound on a harness transient or a load-dump rating.
It exceeds the bench drivers' 40 V rating and the buck's recommended operating
range, and leaves little margin to the buck's 45 V absolute limit. **Do not
declare the copied protection vehicle-ready.** Pulse energy, wiring inductance,
temperature, fuse clearing and reverse-battery behavior must be coordinated.

Before vehicle use define: normal battery/charger range; starter versus aux
feed; crank voltage/time and acceptable recording interruption; jump-start
exposure; reverse-battery duration; positive/negative conducted pulses with
source impedance; ground offsets; enclosure temperature and vibration.
Aux-positive isolation reduces direct alternator exposure only if still true;
IGN, chassis, charger and signal connections remain coupling paths. No ISO
compliance or load-dump immunity is claimed, and no arbitrary high-voltage
pulse should be applied to the car to test this prototype.

Proposed 100 uA room-temperature budget allocation: 30 uA switch leakage,
10 uA protection/drivers/PCB, 40 uA future maximum-on safeguard, 20 uA other
interfaces. These are design allocations to verify, not summed guaranteed
datasheet maxima. Measure both battery rails if IGN and BATT use separate
sources; powered cluster/USB current must not be hidden by measuring only J1.
At 0.5 A output for 30 minutes, estimated battery use is 0.130 Ah at 12 V
and 80% efficiency; this dwarfs one day's 0.0024 Ah at 100 uA.

## 6. Off-state/backfeed audit

| Path | Finding and action |
|---|---|
| USB/VBUS | USB deliberately keeps Pico awake. Use B5 -> DOR -> VSYS, never tie B5 to VBUS. Open JH during maintenance so USB-driven HOLD cannot keep the battery circuit on. Check DOR reverse leakage and B5/VIN_SW rise with USB alone |
| Shared Pi GP5 | Pi's 1.8k pullup can inject current into an off Pico. The proposed 4.7k series resistor only reduces it; it is not isolation. Fit the dedicated UIGN output above and remove the shared collector jumper for the new power domain |
| VSS/tach/brake | Existing 22k divider inputs clamp upward into 3V3 with 1N5819. If externally energized while logger is off, they can power the rail. Do not rely on an assumed key-off low or a resistor as isolation |
| Fuel C11/B11 | 7.5k/4.7k and 22k/4.7k dividers, 1k series at ADC, upper/lower clamps. Upper clamp can backfeed 3V3; reverse/negative input also needs its lower clamp. Preserve fuel loading/calibration when adding isolation |
| B16 | Installed common rail joins both divider bottoms and AGND. Supply/USB ground creates additional paths. Preserve current wiring until jointly reviewed; B16 must not become the logger's power return if J1 ground opens |
| RS-485 | Future transceiver must specify unpowered bus leakage and output behavior. DE must default low; RO, bias resistors and any always-powered transceiver supply must not feed off GPIOs. MAX3485 name alone does not settle the complete power-domain audit |
| SD/programmer | SD must share the switched domain. An independently powered SD module, UART adapter, SWD probe or external pullup is another possible source |

Illustrative injection with the off rail held at 0 V and a 0.3 V upper-clamp
drop: VSS=5 V gives about 0.205 mA; each tach/brake=16 V about 0.670 mA;
B11=16 V about 0.516 mA through its Thevenin source plus 1k; C11=8 V about
0.715 mA. All together approximately **2.78 mA**, already far above the parked
target. As the rail rises, currents change; these are not measured currents or
permission to operate RP2040 clamps continuously.

For the first isolated latch tests, physically disconnect those signals from
the Pico. For installed use provide automatic isolation ahead of every path
to the switched rail: digital buffers with documented Ioff, analog switches
with powered-off protection at the full divider voltage, or equivalent
independent opto/relay paths. Component selection and analog error budget are
open integration work. Moving a switch after an existing rail clamp fails to
remove the clamp path. Do not test an energized signal on an unpowered real
Pico until the proposed isolation is verified on a dummy fixture.

The Pico's normal USB diode path and external Schottky-to-VSYS arrangement are
documented in [Pico W powering guidance](https://datasheets.raspberrypi.com/picow/pico-w-datasheet.pdf).
RP2040 IO absolute maximum is IOVDD+0.5 V; there is no basis here for adopting
historical prose that a few mA of continuous clamp injection is guaranteed safe.
[RP2040 §5.5.3.1](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf).

## 7. Fault coverage and independent maximum-on cutoff

Source inspection found no application watchdog enable/update calls in the
logger's current .ino/.cpp/.h files. Core 0 performs SD/network work; core 1
counts and reports. The local Pico SDK `hardware/watchdog.h` describes a
maximum RP2040 timeout of 8388 ms; library or bootloader reboot use does not
establish an application health policy. Neither core currently implements the
required watchdog servicing contract.

| Fault | First prototype result / required behavior |
|---|---|
| HOLD low, unplugged or high-Z | QH off by pulldown; power off if IGN absent |
| MCU reset, IGN present | QI keeps power on, restart allowed; pulldown does not override IGN |
| Reset, IGN absent | QH releases; power decays; boot must refuse HOLD even if USB/capacitors allow restart |
| One/both cores stop | Only a deliberately enabled health-gated watchdog can reset them; proposed contract in handoff |
| Live firmware stuck holding, watchdog still fed | **Remains on indefinitely in revision A**; watchdog and pulldown do not cover it |
| HOLD shorted high or QH C-E short | Remains on with IGN absent; a software release cannot help |
| QP shorted D-S | Remains on even if gate drive is removed; fuse does not clear an ordinary-load shorted switch |
| IGN wire stuck high | Hardware remains on; distinguish electrical high from physical key state |
| Supply loss/brownout | Data may be lost; no 30-minute restart when IGN absent. Recovery while IGN present is allowed |

**Decision:** require an independent elapsed-time inhibit before unattended
vehicle operation if a live/stuck HOLD must have a bounded battery cost.
It must start from qualified IGN falling, expire within **32–40 minutes**
(nominal 35), and remain expired until a qualified IGN assertion. HOLD, MCU
reset, watchdog servicing and network activity must not retrigger it. Loss of
safeguard supply with IGN absent must default to inhibit; IGN present remains
a hardware startup override. Timer clock/logic must be independent of the
logger firmware. Its supply and worst-case leakage belong in the parked budget.

The safeguard needs a series interruption of the **HOLD sink path**, not
merely a pulldown against an actively driven GPIO. A second series power
switch is required if QP-short protection is in scope. This revision has a
physical JH maintenance break but **no independent timer**, so forced-high
tests intentionally demonstrate the gap. Detailed timer/latched-inhibit
component selection, power-on-reset behavior, drift and hot leakage are the
next circuit increment. A generic retriggerable watchdog is not an equivalent
substitute. Ignition wiring faults and a shorted power switch remain separately
declared faults unless extra independent detection/switching is added.

## 8. Open decisions and readiness

1. Owner/local agent: IGN tap, source fuses, connector/enclosure and power
   ground. Auxiliary testing and eventual starter-battery preference are now
   recorded; an actual starter-feed connection is not selected.
2. Engineer: exact capacitor series/ESR, missing parts and switch inrush/SOA;
   regulator startup/stability over load and temperature. Do not transplant the
   hondaPico 100 uH axial or assume its measured low load is ours.
3. Engineer + firmware: qualify boot/reset, both-core watchdog and cutoff;
   implement independent maximum-on inhibit for unattended use.
4. Engineer + signal/fuel owners: automatic off-state isolation and reference
   integrity; measure connected parked current.
5. Engineer: coordinated vehicle input protection, fault current and thermal
   validation. A 1 A bench PSU does not establish a battery-powered short test.
6. Board owner: freeze full signal set and mechanical interfaces before layout.

Physical prototype evidence must precede validation claims. Vehicle-duty and
the roadmap's other electrical/signal gates precede fabrication readiness.
No historical `circuits.md` entry was changed by this proposal.

## 9. Independent-cutoff continuation

See [MAX_ON_CUTOFF.md](MAX_ON_CUTOFF.md) for the October 25 candidate:
clocked 34 min 8 s backup limit, reset-dominant latch and separate HOLD-path
inhibit. It includes changes to RGS and IGN sensing which are **not yet merged
into revision A's connection list**. The incremental BOM, executable Boolean
checks and physical gates travel with that document. Its supply, oscillator
and ignition-qualification margins are still open; it does not establish
unattended or vehicle readiness.

The later [CUTOFF_MARGIN_REVIEW.md](CUTOFF_MARGIN_REVIEW.md) selects an
external temperature-rated oscillator and TPS70950-Q1 supply, replaces the
false-ON capacitor polarity with an active-high filter/reset discharge, and
proposes one qualified IGN decision for both hardware and firmware. It also
records gate-drive calculations and a parked-current allocation shortfall.
The new A5 supply requires protected P_AON <=30 V, with a 28 V design ceiling;
the old 41.4 V TVS candidate cannot protect it. These changes remain separate
from revision A's original connection list pending coherent schematic capture.
