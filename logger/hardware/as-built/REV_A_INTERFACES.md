# Logger Rev A — proposed interface freeze

October 29, 2026 by Claude Code `hardware-integrator`, session
`23d6d0fb-9656-4e03-acb3-922537019a5b`.
Resume: `claude --resume 23d6d0fb-9656-4e03-acb3-922537019a5b`.
Session ID read from this session's harness-assigned working paths; no
tool-provided session/thread pair exists here to cross-check it against.

**Disposition: proposal for review. Nothing here is frozen, accepted, ordered or
built.** A freeze needs the dispositions in §10: analog reviewer on loading and
protection, electrical lead on power boundaries, firmware reviewer on the pin
map and card metadata, LRA-04 on the bus allocation, and manager acceptance.

Baseline: [AS_BUILT.md](AS_BUILT.md), written at commit
`91a992c9de19c2c1c461fa1b78f5c921405a03ea` and rebased onto
`eb33d17a98a0f9bb07872fee7baadf368d3e3e55`. Every unknown referenced as U-nn and
every conflict as C-nn is defined there. This document adds no new as-built
claim; where the as-built is unknown, the proposal states the requirement and
leaves the value open rather than inventing one.

Derived figures in this document are recomputed by
[check_as_built_numbers.py](check_as_built_numbers.py) alongside the as-built
ones; it proves arithmetic consistency, not circuit behaviour.

Power architecture, timing, HOLD semantics and the parked-current budget belong
to [`../power/INTERFACE_CONTRACT.md`](../power/INTERFACE_CONTRACT.md) and
[`../power/COMPONENT_MARGIN_CLOSURE.md`](../power/COMPONENT_MARGIN_CLOSURE.md).
This document consumes them; it does not restate or revise them, and it
introduces no second power design.

---

**October 29 integration reconciliation.** Drafted by Codex `pcb-manager`,
session `01a18447-07c2-7bb3-8318-9b276cfdb3b8`
(`codex resume 01a18447-07c2-7bb3-8318-9b276cfdb3b8`), whose shift ended before
the merge was committed. Reviewed, repaired and committed by Claude
`pcb-manager`, session `630dea87-5e4d-4bad-a1ff-d41b3a5f509b`.
The reconciliation preserves Claude `hardware-integrator`'s revised return
`f23e51c` and removes residual stale claims, aligning the tables with the
reviewed conditional conclusions. No new owner measurement, part selection or
circuit change is introduced.

## 1. GPIO and peripheral allocation

Proposed freeze. "As built" columns come from the fitted hardware; "Rev A"
columns are the proposal.

| GPIO | Pin | As built | Rev A | Direction / domain | Status |
|---|---:|---|---|---|---|
| GP0, GP1 | 1, 2 | free | **keep free** — UART0 debug/service | — | Proposed |
| GP2 | 4 | VSS in | VSS in, isolated upstream | Input, 3V3 | Preserve fitted allocation; proposed |
| GP3 | 5 | Tach in | Tach in, isolated upstream | Input, 3V3 | Preserve fitted allocation; proposed |
| GP4 | 6 | Brake warning in | same, isolated upstream | Input, 3V3 | Preserve fitted allocation; proposed |
| GP5 | 7 | Opto collector, internal pull-up | **QUAL_N_REPORT**: QREPORT drain, 10k to switched 3V3 | Input, 3V3 | LRA-01 E02 |
| GP6 | 9 | — | **HOLD_RAW**, 4 mA drive, latch LOW before output enable, 47k external pulldown | Output, 3V3 | LRA-01 E03; firmware implements it in `logger_power.cpp` |
| GP7 | 10 | — | **released** — the LRA-01 contract dropped the GP7 HOLD alternate | — | Available |
| GP8, GP9 | 11, 12 | — | **offered to LRA-04** as UART1 TX/RX | — | Not reserved until LRA-04 agrees |
| GP10 | 14 | — | **offered to LRA-04** as a single DE//RE line with a 10k pulldown, following keyless practice | Output, 3V3 | Not reserved until LRA-04 agrees |
| GP11–GP15, GP20–GP22 | — | — | unassigned; bring at least two to pads | — | Proposed |
| GP16–GP19 | 21, 22, 24, 25 | SD MISO/CS/SCK/MOSI | unchanged, 12 MHz, switched 3V3 only | SPI0, 3V3 | Preserve fitted allocation; proposed |
| GP26 | 31 | Fuel ADC0 | unchanged ratio; protection fitted; isolated upstream | Input, analog | Preserve fitted allocation; proposed |
| GP27 | 32 | Supply ADC1 | unchanged ratio; protection fitted; isolated upstream | Input, analog | Preserve fitted allocation; proposed |
| GP28 | 34 | — | **keep free** — the only remaining ADC channel | — | Proposed |
| GP23/24/25/29 | — | CYW43 | CYW43 | — | Unavailable |
| ADC_VREF, AGND | 35, 33 | AGND carries B16 and both divider bottoms | unchanged topology, explicit single-point return | — | §5 |

Two allocation notes, so a later agent does not reopen them:

- **GP10 for DE and /RE together** is the keyless board's own arrangement
  (`DE` and `/RE` tied, 10k pulldown so the default is listen while the GPIO is
  still floating at boot). It is offered because it costs one pin instead of two
  and the default is already proved correct on a working board. LRA-04 may
  reject it; this is a coordination offer, not an allocation.
- **ARM, EXPIRED, PGOOD and HOLD_N stay off the GPIOs.** The power contract
  makes them A5-domain test points with no GPIO connection, and the firmware has
  no ARM feedback in this revision. Any later request for ARM feedback is new
  scope that re-opens the GPIO budget.

The total GPIO source budget must account for GP6's 4 mA allocation alongside
the SD interface. `INTERFACE_CONTRACT.md` §2 derives the 4 mA from a 3.581 mA
upper source calculation and replaces the old 3.0 V HOLD-HIGH criterion with a
2.6 V qualification target; neither is re-derived here.

---

## 2. Input interface requirements — provisional, with open rows

`INTERFACE_CONTRACT.md` §8 asks LRA-03 to *"establish each normal/fault input
range, source impedance and permissible cluster loading."* **This matrix does
not close that gate.** It states what is established and marks what is not: two
of the five source impedances are unknown (U-08), and the fault envelopes rest
on nominal waveforms rather than characterised transients. Treat the "proposed
permissible load" column as a requirement to be reviewed, not an agreed limit.
Present load is what the fitted divider draws.

**Open rows, which the gate needs before a freeze:** B2 source impedance and
permissible loading; B1 the same; the fault envelope on all five branches beyond
a nominal 16 V charging case; and a declared protected C11 design envelope. The
historical unloaded-voltage explanation in U-09 remains separate from selecting
an adequate input envelope.

| Channel | Normal range at the tap | Fault / worst-case exposure | Source impedance | Present load | Proposed permissible load | Basis |
|---|---|---|---|---|---|---|
| **B2** VSS | 0 V to "about 5 V or more", pulsing; ~91 Hz at 80 mph; nothing below ~2 km/h | Over-voltage to the charging rail if the PCM output is pulled up higher than assumed; 16 V harness fault | **Unknown** (U-08). PCM 32P terminal 9, open-collector idling low | 90.9 µA at 5 V (55 kΩ) | **≤100 µA at 5 V**, i.e. do not reduce the 55 kΩ | The record's own reason for high impedance: an opto cell would pull 4–10 mA out of a PCM output pin |
| **B1** Tach | 12.0 V engine off, **14.8 V charging**, pulled to 0 V; ~217 Hz at 6500 rpm; 3.8 ms low pulse at idle | 16 V charging fault; load dump | **Unknown** (U-08), open-collector driver | 514 µA at 14.8 V (28.8 kΩ) | **≤600 µA at 14.8 V** | No measured ceiling; hold the present value until U-08 resolves |
| **C14** Brake warning | ~11.3 V idle (12 V less the cluster's internal diode), ~14.1 V charging; ground-switched; dead with the key out | Cold-filament contact: **2.4 A** into a pin clamp if taken direct; 16 V charging fault | **Measured**: 375 mA into a short, ~32 Ω hot / ~3.6 Ω cold | 392 µA at 11.3 V | **≤1 mA**, keeping ≥2.5 decades below the measured 375 mA branch current | Measured source, 2026-10-23 |
| **C11** Fuel sender | 1.8–2.4 V measured; specified ceiling 8 V pending the FSM's unexplained 5–8 V unloaded band (U-09) | Reverse/negative excursions measured to −280 mV unenergised; impulsive ignition noise at 20–50x crest, 2.32 V p-p against a 2.13 V signal | **17.5 Ω** (R<sub>g</sub> ‖ R<sub>s</sub> = 52 ‖ 26) | 12.2 kΩ | **Total DC load ≥12 kΩ**, i.e. apparent-R<sub>s</sub> shift ≤0.057 Ω ≈ 0.1 point of float travel; gauge-needle unchanged before/after is the pass condition | `ADC_INTERFACE_SPEC.md` §3 |
| **B11** Supply | 11.93 V measured at ignition II engine off; up to ~15 V charging; **dead with the key out** | 16 V charging fault; chafed sense wire backed by the 7.5 A fuse 9 | Low — an ignition-switched fused feed | 26.7 kΩ, 0.45 mA at 12 V | No load limit; the requirement is a **100 mA fuse at the tap end** | `ADC_INTERFACE_SPEC.md` §4a |
| **B16** Ground sense | Reference only, no current intended | Loss of the B16 conductor leaves both ADC bottoms referenced only through the buck return | — | — | **Must never become a power return** | §5 |

Two consequences that matter more than any single number:

1. **Only C14's source is measured.** B2 and B1 are the two branches a Rev A
   loading change could disturb, and neither has a characterised source or a
   stated FSM load limit. The safe default — kept here — is not to change their
   divider ratios at all (see D11 for the one exception that must be analysed).
2. **Any series element added upstream sits inside the fuel channel's published
   calibration.** The card header publishes `log.adc.fuel div=7500/4700`, with
   no third term, so an isolation switch's R<sub>on</sub> is not representable
   today. See §9.

---

## 3. Protection and isolation requirements

### 3.1 What has to be true

From `INTERFACE_CONTRACT.md` §8 and `COMPONENT_MARGIN_CLOSURE.md` §5, two
**separate** acceptance criteria, which the record has so far discussed as one:

- **A — parked leakage.** All independently energized interface sources together
  ≤**10 µA at 20–30 °C / 25 µA at 85 °C**, of which LRA-02 tentatively reserves
  **8/20 µA for the five vehicle branches** and 2/5 µA for future bus and
  service paths. An equal five-way split would be 1.6/4 µA per branch; that is
  an illustration, not a part specification, and reviewers may redistribute
  within the total.
- **B — survival and bounded injection with the board off and the inputs
  energized.** This is not a parked state. It is reached by A5 supervisor BAD,
  EXPIRED with HOLD stuck, a reset during ignition-ON, and USB-only bench work
  with the key at II. In it, `power-off 3V3/B5 must remain ≤0.3 V`.

**The two criteria have different drivers, and this is the finding that should
shape the isolation choice.** Criterion B is what the existing analysis is
about: with the rail at 0 V and a 0.3 V upper-clamp drop, `DESIGN.md` §6 puts
VSS at 5 V injecting ~0.205 mA, tach and brake at 16 V ~0.670 mA each, B11 at
16 V ~0.516 mA and C11 at 8 V ~0.715 mA — about **2.78 mA** together, three
orders above the interface budget. (The digital branches are computed from the
divider top, the analog ones through their Thevenin plus the 1 kΩ; both are
conditional calculations, not measurements.)

Criterion A, however, probably has far more headroom than the budget assumes,
because **all five vehicle branches appear to be de-energized when the car is
parked**:

| Branch | Evidence for key-off dead |
|---|---|
| C14 brake | **Logged**: `brake=1` held through an ignition-off period as a dead circuit, breaking out at the exact second of `IGN state=off -> on`; the lamp is fed from fuse 9 → B11 |
| B11 supply | **Logged**: 0–4 counts (mean 1.212) with ignition off, 2577–2603 on; `ADC_INTERFACE_SPEC.md` §2 states it is ignition-switched "so the divider draws nothing while parked" |
| B2 VSS | **Inferred**: synthesised by the PCM, which is unpowered with the key out |
| B1 tach | **Inferred**: driven by the ignition system |
| C11 fuel | **Inferred**: the sender is excited from the cluster, which is ignition-fed |

Three of the five are inferred, which is exactly the class of claim this project
has been wrong about before, so **U-10 asks for one DMM pass at the three taps
with the key out before criterion A is sized on this basis.** If it holds, the
8/20 µA reservation covers only the isolation device's own off-state leakage
plus cluster-side leakage, and is comfortable. If it does not hold for some
branch, that branch alone decides the isolation class.

### 3.2 Isolation placement is not negotiable

Upstream of the divider **top**, on every branch. A buffer or switch placed
after the divider leaves both the DC loading and the existing clamp path intact:
at an illustrative 12 V the 22k/33k branch still draws 218 µA and a 22k/6.8k
branch 417 µA, and the VSS branch can still inject about 523 µA into a 3V3 rail
held at zero. Series limiting and firmware high-Z are not isolation.

### 3.3 Candidate classes, with their real costs

Not a selection — the analog reviewer and LRA-02 own that. Enumerated so the
trade is visible and so the one already-screened option is not re-screened.

| Class | Why it can satisfy A and B | What it costs / what must be proved |
|---|---|---|
| **Non-latching signal relay, gold-clad contacts, one or two multi-pole parts** | Open by construction with no power: parked leakage is contact leakage, not a specified I<sub>off</sub>; withstands full tap voltage; R<sub>on</sub> in the tens of mΩ, so no ratio effect; 217 Hz is trivial | Coil current **while energized** — budget it against the present ~51 mA branch baseline; **dry-circuit switching** at 90 µA / 3 V on the VSS branch needs contacts rated for low-level work; contact bounce at energize; mechanical life per ignition cycle; physical envelope (U-11) |
| **Latching (bistable) relay** | Coil current only during the transition | **Rejected as a default**: it holds the inputs connected through an unplanned power loss, which is precisely criterion B's entry condition. It would need a guaranteed reset that A5-BAD and EXPIRED cannot promise |
| **Analog switch with power-off protection** | Solid state, no coil, no contacts | The screened **ADG5412F-class** part is *not* selected: its 8 V minimum supply excludes powering it from B5, and its power-off source-leakage entry is **typical, not a maximum**. Any replacement must supply a guaranteed off-leakage maximum over temperature at the full tap voltage, and a rail that exists in this design |
| **Per-channel discrete (opto or series FET) for the three digital branches, relay for the two analog** | Lets the analog channels keep a metallic path with no R<sub>on</sub> error while the digital ones become genuinely isolated | Two mechanisms to qualify instead of one; the digital path's loading changes, which U-08 says is not yet permissible to decide |

**No confirmed suitable item was identified in the consulted list.** The
inventory the owner named on October 29
(`/srv/agent_share/inventory/inventory_list.md`) lists coil-driven power and
solid-state relay *modules* whose contacts are not specified for the 90 µA / 3 V
dry-circuit switching the VSS branch needs, and no power-off-protected analog
switch. The owner states that list is **incomplete and may include consumed
stock**, so absence from it cannot establish absence from stock. Exact
reconciliation is deferred to the parts discussion and must not block the design
choice; in either direction, stock is neither fitted hardware nor a suitability
argument.

### 3.4 Requirements any candidate must meet

1. **Normally open with no power applied**, by construction, not by a pull-down.
2. **Off-state leakage specified as a maximum** at the full tap voltage, at
   20–30 °C and 85 °C, and summing to ≤8/20 µA across the five branches.
3. **Withstand the full tap voltage with its own supply at 0 V**, including a
   16 V charging fault, and the C14 branch's measured source.
4. **Insert ≤25 Ω in the fuel top leg and ≤100 Ω in the supply top leg.** At
   25 Ω the fuel ratio shifts −0.205 %, which is −4.9 mV referred to a 2.4 V
   wire signal and ~0.07 Ω of R<sub>s</sub> — inside the existing 0.1-float-point
   loading allowance and removable by the in-situ ratio calibration in the
   historical `fuel/ADC_INTERFACE_SPEC.md` §9 step 2.
   The **temperature drift** of that resistance is the part calibration cannot
   remove and must be bounded.
5. **Introduce no edge artefact within 100 µs** on GP2/GP3, the firmware's
   `GLITCH_US` rejection window, and pass a 3.8 ms low pulse undistorted.
6. **Enable only from a rail that exists** in the Rev A domains, and open before
   HOLD releases, so the shutdown order is isolate-then-release rather than the
   reverse.
7. **Fail open on supervisor BAD**, with no software step required.

### 3.5 Clamp and filter, per channel

- Digital cells: keep one 1N5819 per cell to 3V3 and the fitted ratios (C-02).
  Whether a lower clamp is also needed is **open**, not settled: the record
  establishes only that these signals are nominally positive in normal
  operation, which does not bound negative harness transients. The analog
  reviewer decides it against an agreed fault envelope; this document neither
  requires nor rejects one.
- Analog cells: the specified 1 kΩ + 1 µF + two 1N5819 per channel are **already
  fitted** on both channels, per the owner's October 29 part counts (U-01
  closed). Rev A carries them forward; there is nothing to fit. The clamp
  leakage objection is **bounded, not eliminated**: the October 24 check showed
  the midpoint and GP26 within DMM resolution, i.e. under about 2 µA at room
  temperature at one operating point, and the historical specification itself
  limits that finding to its own resolution and conditions. Do not extrapolate a
  guaranteed hot limit from that single room-temperature observation; hot
  leakage remains open for the analog reviewer (U-07).
- Fuses: the C11 and B11 tap-end fuses are **already fitted**, owner-confirmed
  October 29. Rev A extends the same protection to B2, B1 and C14 (D10), which
  do not have it. C14 is the branch where it matters most — its source delivered
  375 mA into a short — and 100 mA is still 250x the 392 µA the divider draws.

---

## 4. Grounds and returns

| Net | Requirement | Reason |
|---|---|---|
| B16 cluster ground sense | One conductor from the cluster, bonded at the logger end only, carrying both ADC divider bottoms to a single node, then to ADC AGND | A common-mode offset largely self-cancels in the fuel computation; a differential offset between the two channels does not cancel at all |
| B16 current | **Never a power return.** If the main ground opens, B16 must not carry supply current | `DESIGN.md` §6; the as-built already depends on this |
| Opto output return | Pico PGND, separate from the AGND sense node | As built |
| Buck return | Its own conductor to PGND | As built |
| PGND / B16 | Never switched | `INTERFACE_CONTRACT.md` §8 |
| Isolation | **None.** AGND and GND are joined inside the Pico and B16 references the cluster, so the optocoupler does not make this installation isolated | AS_BUILT §3.3 |
| Missing-PGND behaviour | Must be analysed and safely simulated on the bench (B06) before it is called covered | `INTERFACE_CONTRACT.md` §9 |

Open: U-05, the signed Pico-GND-to-chassis and per-channel divider-ground
offsets. The one existing figure is 21 mV, unsigned, from a single October 24
reading.

---

## 5. Connectors, mechanics, access and test points

**Every dimension in this project is unknown.** No footprint, enclosure,
mounting or harness length is recorded anywhere in the sources read, and none is
invented here (U-11). What can be fixed now is the *interface shape*.

### 5.1 Connectors

| Connector | Proposed content | Notes |
|---|---|---|
| **J1 — power** | P12 protected +12 V from the auxiliary battery, and its return | 2 contacts. P12 is the power owner's protected input; its clamp/limiter selection is R02 and stays open |
| **J2 — cluster harness** | B2, B1, C14, C11, B11, B16, plus two spares | 8 contacts. Mates to the **existing** cluster breakout; nothing is added behind the cluster, and the Mini-Fit Jr taps stay as they are |
| **J3 — bus / expansion** | Defined by LRA-04, unpopulated if no bus is selected | A spare header with undefined interfaces is not a resolved design |
| **J4 — service** | UART0 on GP0/GP1 and a RUN-to-GND reset pair | Must be power-off-safe: no externally powered pull-up into an off GPIO |

Per-branch fuses belong at the **tap** end, not on the board, which is where the
specification puts them and where a chafed wire is actually backed by vehicle
current.

### 5.2 Mechanics and access

- **SD card**: the card must be removable without removing the board, because
  the card is the primary evidence path. The module is a separate breakout today
  (D6 may change that).
- **USB**: the Pico's USB connector must stay reachable. Flashing uses
  `pico-flash` from the car Pi, which needs physical USB, and `pico_enable_stdio_usb`
  is already set so the 1200-baud reset interface exists. The keyless precedent
  is explicit that panel-off access "in a few minutes" is not a blocker, so
  reachable-with-the-panel-off is the requirement, not permanently exposed.
- **Antenna keepout** for the CYW43 is an LRA-08 constraint; this document only
  records that Wi-Fi delivery is load-bearing for the data path.
- **Envelope, mounting and connector positions: unknown.** §7 question 7 in
  AS_BUILT asks the owner for them.

### 5.3 Test points

The keyless board already carries the right pattern — TP1–TP4 for +12 V, +5 V,
SW and +3V3, TP5–TP7 as three separate ground loops (buck, Pico, harness end),
J7 shorting RUN to GND for a reset without cutting power, plus power-good and
heartbeat LEDs. Follow it, extended for the power candidate's nodes:

| Test point | Node | Why |
|---|---|---|
| TP_P12 | Protected input | Entry voltage and transient capture |
| TP_VINSW | Switched buck input | QP state |
| TP_B5 | Buck 5 V output | Rail and decay (B07) |
| TP_VSYS, TP_3V3 | Pico input and switched rail | DOR drop and the ≤0.3 V decay criterion |
| TP_A5, TP_VCLK | Always-on rail and oscillator rail | Startup budget and ≤0.5 V/ms slew |
| TP_ARM, TP_EXPIRED, TP_PGOOD, TP_HOLDN | Cutoff logic | A5-domain only; **no GPIO connection** |
| TP_QUALN | GP5 report node | The ≤10 ms observation and startup budget |
| TP_HOLD | GP6 | Released ≤0.3 V and asserted ≥2.6 V, loaded |
| TP_GND ×3 | Buck, Pico, harness | Return-path separation, as keyless does |
| JH | Removable HOLD link | Maintenance; already in the power contract |

Current-sensitive nodes need a way to measure without the instrument supplying
the current being measured; `COMPONENT_MARGIN_CLOSURE.md` §5 step 4 requires
probes to be removed for the final leakage reading, which is a layout
requirement as much as a procedure.

---

## 6. Off-state path matrix

Every energized path against disabled rails. "Expected" is the Rev A intent;
"Evidence" names the class of work that could establish it. Nothing in this
table is established today.

| # | Path | Source when the board is off | As-built behaviour | Expected Rev A behaviour | Evidence required |
|---|---|---|---|---|---|
| 1 | B2 → 22k → GP2, clamp to 3V3 | Energized only at ignition II (U-10) | Injects ~0.205 mA at 5 V into a 0 V rail | Branch open upstream of the divider top; ≤8/20 µA aggregate with branches 1–5 | R05 analog review, then B06 with each branch alone and combined |
| 2 | B1 → 22k → GP3, clamp | Ignition / charging | ~0.670 mA at 16 V | As 1 | As 1 |
| 3 | C14 → 22k → GP4, clamp | Ignition (fuse 9 → B11) | ~0.670 mA at 16 V | As 1 | As 1; the measured 375 mA source makes this the worst fault case |
| 4 | C11 → 7.5k/4.7k → 1k → GP26, clamps both rails | Cluster excitation | ~0.715 mA at 8 V through Thevenin + 1 kΩ | As 1, with the ≥12 kΩ load and the ratio preserved when enabled | As 1, plus the analog reviewer accepting the added resistance and the changed off-state loading |
| 5 | B11 → 22k/4.7k → 1k → GP27, clamps | Ignition-switched | ~0.516 mA at 16 V | As 1 | As 1 |
| 6 | B16 ground sense | Cluster ground | Reference; shares the ADC bottoms' rail | Unchanged; never a power return; missing-PGND case analysed | B06, with missing PGND safely simulated |
| 7 | Opto LED input, B11 → 1N5819 → 2.2k | Ignition-switched | Draws vehicle current only with the key on: 4.72 mA at 11.93 V, 5.84 mA at 14.4 V | Existing topology is context; Rev A value remains an electrical proposal, with endpoints unqualified | R02/R03 review, then LRA-07; see D15 |
| 8 | Report node → GP5 | A5 domain in Rev A | Opto collector direct to GP5, internal pull-up from an off 3V3, 100 nF across the opto output. No Pi node: the Pi is out, owner-confirmed October 29 | Opto output moves to the A5 qualification network; **QREPORT** drives GP5 against a switched 10k pull-up; no DC A5 path into GP5. State whether a capacitor is placed on the report node, and budget its settling | Measure powered-A5/unpowered-Pico, and USB with A5 absent; scope the report-node edge |
| 9 | GP6 → QH / QMON | A5 domain | Does not exist | Released ≤0.3 V including hot collector leakage and an unpowered Pico; QH short tested separately | `INTERFACE_CONTRACT.md` §8; bench B05 |
| 10 | USB VBUS → Pico | Bench host | USB deliberately powers the Pico | B5 → DOR → VSYS, never B5 tied to VBUS; open JH for maintenance; no VSYS/3V3 decay required in this mode | B07, including DOR reverse recovery and both VIN_SW and B5 backfeed — QP's body diode permits reverse flow toward P12 |
| 11 | SD interface | — | Entirely on Pico 3V3; module powered from 3V3(OUT) | Unchanged: no externally powered SD module or pull-ups; SD capacitance included in the decay test | B07 |
| 12 | Future bus / SWD / service | External adapter | Does not exist | No externally powered pull-up into an off GPIO; DE defaults LOW; unselected options unpopulated; 2/5 µA reserved | LRA-04, then B06 |
| 13 | Isolation device enable | Its own rail | Does not exist | Fails open with no power; opens before HOLD releases | §3.4; bench |

Until the parts in §3 are reviewed, the existing restriction stands:
**omit or disconnect these inputs on the power fixture.** A manual disconnect is
a bench restriction, not autonomous vehicle acceptance.

---

## 7. Delta list: as-built → Rev A

Each delta has a reason. IDs are referenced from AS_BUILT §2.

| ID | Change | Reason | Owner | Status |
|---|---|---|---|---|
| **D1** | Replace GP5's internal pull-up and any shared node with QREPORT level translation and a 10k pull-up to **switched** 3V3 | Two independent reasons. (a) Removes the DC path into GP5 from an always-on domain and the historical Pi back-feed; LRA-01 E02. (b) **Report-node delay, which must now be budgeted.** In the as-built, the fitted 100 nF plus the internal pull-up needs 12–19 ms (nominal) to reach the contract's 3.0 V criterion, against a 10 ms observation budget. Rev A changes the node: QREPORT, not the optocoupler, sinks this pull-up. So the open question is whether any capacitance is placed on the QREPORT/GP5 report node — if a 100 nF is, the same arithmetic gives 2.40 ms at 10 kΩ; if none is, the delay is QREPORT's own. Either way it belongs inside the 10 ms budget, not assumed to be zero. AS_BUILT §3.2a | Electrical lead | Existing contract candidate; the delay-budget requirement is the new part |
| **D2** | Add GP6 HOLD_RAW with 4 mA drive, LOW latch before output enable, 47k pulldown, and the JH maintenance link | Autonomous power requires a HOLD output; LRA-01 E03; the LRA-05 candidate already writes GP6 | Electrical lead + firmware | Candidate, reviewed; implementation is opt-in |
| ~~D3~~ | Carry the fitted ADC protection forward unchanged | **Not a delta.** The 1 kΩ, 1 µF and two 1N5819 per channel are already fitted on both channels, with their tap-end fuses, per the owner's October 29 part counts. Rev A reproduces the as-built here rather than changing it | Analog reviewer confirms the carry-forward | Closed — nothing to fit |
| **D4** | Add normally-open, power-off-safe isolation upstream of **every** divider top, on all five branches | ~2.78 mA of off-state injection against a 10/25 µA interface budget; §3 | Analog reviewer + LRA-02 | Open — the largest Rev A design item |
| **D5** | Make the single-point ADC return explicit: one B16 conductor, one common node, then AGND | Already how it is built; Rev A must not lose it to a ground plane that creates a second path | Analog reviewer + LRA-08 | Proposed |
| **D6** | Add 10–100 µF bulk at the SD supply | **Confirmed absent** October 29, so 100–200 mA write spikes land directly on the Pico's shared ~300 mA regulator. This is now a real addition, not a possible duplicate | LRA-06 | Proposed |
| **D7** | Replace the external buck with the onboard switched supply: QP before LM2678, independent latch/counters/clock, direct QI startup | The whole point of Rev A; `DESIGN.md` E01 | Electrical lead | Candidate, reviewed |
| **D8** | Add the test points and the RUN-to-GND reset header of §5.3 | Nothing on the logger is instrumentable today; the keyless board already shows the pattern | LRA-06 / LRA-08 | Proposed |
| **D9** | Drop the 4.7 kΩ GP5 series resistor | **Superseded, not forgotten.** It was decided on October 24 against the Pi-shared node, never fitted, and D1 removes the node it protected. Record it so nobody re-adds it as if it were outstanding | — | Closed; the node it protected no longer exists |
| **D10** | Extend the 100 mA tap-end fuse to **B2, B1 and C14** | C11 and B11 already have theirs, owner-confirmed October 29; the three digital branches do not. C14's source delivered 375 mA into a short | Owner | Proposed, narrowed to three branches |
| **D11** | Analyse the tach cell's top-of-range clamp margin | The cell idles 0.45 V below its estimated clamp onset, with an unspecified low-current V<sub>F</sub> (U-07). Either accept bounded clamp conduction or change the ratio — but a ratio change needs U-08 first | Analog reviewer | Open |
| ~~D12~~ | Confirm the ignition cell's values | **Closed October 29.** 1N5819 series diode, 2.2k measured, 100 nF output capacitor, no input capacitor, inline fuse present. The LRA-01 endpoint budget can now be computed from measured values; qualifying the endpoints themselves stays with LRA-07 | — | Closed |
| **D15** | Evaluate the measured **2.2k** as an alternative RLED value | Nominal `28²/2200 = 0.356 W`, versus `28²/990 = 0.792 W` for the candidate 1k at -1%. This is not a fitted-rating or hot/pulse guarantee. Rev A opto endpoints must be checked against IGN_A/IGN_RC; the GP5 10k is QREPORT's load and supplies no opto CTR margin. See AS_BUILT §3.4a | Electrical lead, R02/R03 input | Conditional proposal; ratings/endpoints open |
| **D13** | Replace DOR with the 1N4004-E3/54 candidate, B5 anode → VSYS cathode | Specified reverse-current maxima; `INTERFACE_CONTRACT.md` §8 | Electrical lead | Candidate, reviewed |
| **D14** | Fix the stale cell descriptions in `accord-logger.ino`'s header comment | C-01 and C-02: the comment still says 6k8 for VSS and Schottky/BAT54 for all three clamps | Firmware owner — **not claimed here** | Open |

Deliberately **not** changed: the five divider ratios, GP2/3/4/5/16–19/26/27,
the 1N5819 digital clamps, the SD rail choice, the single-point B16 return, and
the brake column's inverted logging convention. Each is either verified on the
car or load-bearing for published data, and none has a demonstrated defect.

---

## 8. Firmware and metadata agreement items

For the firmware reviewer; no firmware change is proposed or made here.

1. **Pin map.** GP6 as the sole HOLD writer is already in `logger_power.cpp`
   (`gpio_put(6, …)`, 4 mA, LOW preload). Confirm that the Rev A freeze matches
   and that GP0/GP1, GP7, GP8–GP10 and GP28 stay unclaimed by firmware.
2. **The card header cannot express an isolation switch.** `card_header.h`
   prints `log.adc.fuel div=%lu/%lu` from `FUEL_R_TOP`/`FUEL_R_BOT` and computes
   the ratio and full scale from those two numbers alone, so the published
   calibration has no third term for series resistance. If D4 puts R<sub>on</sub>
   in the top leg, either (a) keep it negligible and absorb it in the in-situ
   ratio calibration, or (b) publish the effective top resistance in
   `FUEL_R_TOP`/`SUPPLY_R_TOP` and version the change where the converter can
   see it. Option (b) changes a documented field's meaning and needs the
   bridge/converter owner's agreement. Option (a) is why §3.4 bounds
   R<sub>on</sub> and its drift.
3. **Circuit revision identity.** `INTERFACE_CONTRACT.md` §5 already requires the
   circuit/firmware revision in agreed metadata. A Rev A board changes what GP5
   means (hardware-qualified rather than raw opto) and what the ADC top legs
   are; `log.power interface=` carries the first, nothing carries the second.
4. **Column semantics are unchanged by this proposal.** `brake=1` stays
   "line grounded", `ign=1` stays "on", units and column order stay as they are.
   `brake` remains meaningful only with the ignition on.
5. **No raw-IGN column exists after D1**, as the contract already states.
6. **The ≤10 ms observation budget must be stated to include the report node's
   own settling time**, not only firmware sampling. Rev A's GP5 node is driven
   by QREPORT against a 10 kΩ pull-up, so the first thing to settle is whether
   any capacitance is fitted there at all. If a 100 nF is retained, nominal
   arithmetic gives 2.40 ms to the contract's 3.0 V criterion, leaving 7.6 ms
   for sampling and scheduling; the as-built internal-pull-up case needs 12–19 ms
   and would not fit. A **≤52 nF** limit applies only in the hypothetical where
   the internal pull-up is kept, at the worst-case 80 kΩ. None of these is a
   timing qualification: rail, capacitor, leakage and temperature corners have to
   be carried through first. AS_BUILT §3.2a has the table and its assumptions.
   This also bears on LRA-05's masked-interrupt analysis, which assumes the pin
   transition itself is prompt.

---

## 9. Dependencies and what blocks a freeze

| Blocker | Held by | Why the freeze waits |
|---|---|---|
| R05 — five input isolation channels, DOR delta, bus/service paths, B16/PGND | LRA-02 / 03 / 04 analog and schematic review | D4 is unselected; §6 rows 1–6 and 12 have no accepted answer |
| U-10, U-11, U-12 | Owner | Presence/nominal-value questions U-01 through U-04 and U-13 closed; exact opto identity and fuse/resistor ratings remain to be resolved during parts discussions. U-10/11/12 cover key-out state, physical envelope and divider tolerances |
| U-06, U-07, U-08 | Bench / datasheet work | D11 and the VSS off-state case depend on them |
| LRA-04 bus allocation | Communications reviewer | GP8/GP9/GP10 and J3 are offers, not reservations |
| R02 — P12 and IGN protection envelope | LRA-02 + owner vehicle exposure | Decides what J1 must survive. The as-built RLED value is a candidate answer to its open IGN dissipation defect; see D15 |
| R03, R04 — component and current closure | LRA-02 | The interface budget's 10/25 µA sits inside an unclosed total |
| LRA-05 masked-interrupt limitation | Firmware follow-up | Does not block the interface freeze; blocks automatic-power acceptance |

**What does not block it:** a fuel calibration model, the FSM's 5–8 V question
(U-09), a complete CAN implementation, and dashboard or database work.

---

## 10. Acceptance

| Role | Must disposition |
|---|---|
| Analog reviewer | §2 loading limits, §3 isolation class and requirements, D4, D5, D10, D11, and the D3 carry-forward |
| Electrical lead | That §1, §4 and §6 are consistent with `INTERFACE_CONTRACT.md`, and that this document introduces no second power design |
| Firmware reviewer | §1 pin map and §8 metadata items |
| LRA-04 | GP8/GP9/GP10 and J3, or a counter-proposal |
| Owner | The §7 questions in AS_BUILT, and the physical envelope |
| Manager | Records acceptance in `coordination/PROJECT_MILESTONES.md`; this document records none |

Authorized for this return: public-safe documentation and analysis only.
Hardware operation, vehicle wiring, flashing, purchasing, fabrication and
private runtime or database changes each require separate owner authorization.
