# Logger as-built — consolidated physical record

October 29, 2026 by Claude Code `hardware-integrator`, session
`23d6d0fb-9656-4e03-acb3-922537019a5b`.
Resume: `claude --resume 23d6d0fb-9656-4e03-acb3-922537019a5b`.
Session ID read from this session's harness-assigned working paths; this tool
exposes no `CLAUDE_SESSION_ID`/thread-ID pair to cross-check it against, so the
identity is single-sourced rather than independently verified.

**Disposition: documentation consolidation of the existing physical build. No
assembly, wiring, flashing, measurement, purchase or service change accompanied
it, and nothing here is accepted hardware.** This is the first LRA-03 return.
Starting commit: `91a992c9de19c2c1c461fa1b78f5c921405a03ea` (public `main`,
including reviewed LRA-01/02 candidates and the LRA-05 candidate `0745d5b`).
Rebased onto `eb33d17a98a0f9bb07872fee7baadf368d3e3e55`, which added the
manager's October 29 LRA-04 dispatch and inventory clarification; neither
touches this directory.
Claimed scope is `logger/hardware/as-built/` only; power, firmware, KiCad and
root/coordination artifacts were read and left unchanged.

**October 29 integration reconciliation.** Drafted by Codex `pcb-manager`,
session `01a18447-07c2-7bb3-8318-9b276cfdb3b8`
(`codex resume 01a18447-07c2-7bb3-8318-9b276cfdb3b8`), whose shift ended before
the merge was committed. Reviewed, repaired and committed by Claude
`pcb-manager`, session `630dea87-5e4d-4bad-a1ff-d41b3a5f509b`.
The reconciliation preserves Claude `hardware-integrator`'s revised return
`f23e51c` and removes residual stale claims, aligning the tables with the
reviewed conditional conclusions. No new owner measurement, part selection or
circuit change is introduced.

## Owner correction — October 29, 2026

Stated directly by the owner, and therefore top of the precedence order in §1:

- **The Pi is out.** It has been removed for some time. Nothing of the Pi's
  wiring, including its 1.8 kΩ pull-up, is on the GP5 node.
- **The clock-harness tap is removed**, not merely superseded.
- **Ignition sense is consolidated on B11.** There is one ignition source.

This closes U-03, C-05 and C-06 and retires the historical 1.44 mA unpowered
back-feed hazard with it. Where the body of this document hedges on whether old
Pi or clock wiring is still physically attached, this statement governs.

Owner part count, same date: **no capacitor on the SD module**, and **three
capacitors, eight diodes and thirteen resistors** on the build. Capacitor
values: **100 nF across the opto output, 1 µF on each ADC channel.** Owner also
states that **all eight diodes are 1N5819**, and *assumes* the opto series
resistor is **2.2k**, which the owner then **measured** rather than inferred
(§3.4a). Owner also confirms the **fuses are in place**: the
tap-end fuses on the C11 and B11 sense wires and the inline fuse on the ignition
feed. The C11/B11 specification calls for 100 mA; the reported confirmation was
of presence, not a reading of the fitted ratings. That count resolves the
largest open item in this record; §3.2 works it through. It closes U-04 and most
of U-01, and it contradicts this document's original assumption that the ADC
protection was unfitted — the assumption was wrong, and the count governs.

**The nominal circuit is substantially reconstructed as of October 29.**
Five of the thirteen register entries closed: U-01, U-02, U-03, U-04 and U-13.
Those closures record reported presence, nominal values and count-based
inferences, not complete component qualification. The exact optocoupler
manufacturer and suffix, the fitted fuse ratings, resistor power ratings and
other part limits remain unconfirmed. The eight remaining register entries cover characterisation,
tolerances and mechanics. Resolve part identification/ratings during the later
parts discussion; do not repeat the owner's completed presence/count questions.

Two kinds of October 29 evidence appear below and are not interchangeable:
**owner-reported values and connections**, and **conclusions inferred from total
part counts**. The counts are strong because each total matches its prediction
exactly with nothing left over, but an inference from a total is not a
part-by-part reading, and §3.2 says which is which.

Companion document: [REV_A_INTERFACES.md](REV_A_INTERFACES.md) holds the
proposed interface freeze. **This file records what exists; that file records
what is proposed.** Nothing is moved between them silently.

Every derived number in both documents is recomputed by
[check_as_built_numbers.py](check_as_built_numbers.py), so a reviewer can check
the arithmetic without re-deriving it:

```sh
python3 -B logger/hardware/as-built/check_as_built_numbers.py
```

It establishes self-consistency and nothing else. It is not a measurement, a
component guarantee or a circuit simulation, and its assumed 0.3 V Schottky drop
is itself an open item (U-07).

---

## 1. How to read this record

Three things are deliberately not merged: what is physically fitted, what a
specification asks for, and what nobody has established. Every row carries a
confidence class.

| Class | Meaning |
|---|---|
| **F** | Fitted: owner reported or confirmed the physical connection, with a date |
| **M** | Measured: a dated instrument reading or logged capture exists |
| **S** | Specified only: a document calls for it; no fitting report exists |
| **U** | Unknown: not established by any source read here |
| **P** | Proposed: a Rev A candidate, recorded in the companion document |

**Precedence, highest first.** This ordering is itself a finding of the source
record, not a convention invented here: the October 24 corrections caught three
documents each wrong in a different field about one circuit.

1. A dated owner statement about the physical hardware.
2. A dated instrument measurement or logged capture of that hardware.
3. The as-built diagrams and installation notes, newest first.
4. Specifications (`fuel/ADC_INTERFACE_SPEC.md`, `SPEC.md`).
5. Firmware comments and README pin tables.

Source 5 is last on purpose. `accord-logger.ino:31` still describes the VSS cell
as `22k series, 6k8 to GND` and all three clamps as `Schottky`/BAT54; both were
corrected in the record (§6, C-01 and C-02). A comment is evidence of what a
programmer believed, not of what is soldered.

Nothing below is a fuel-quantity model, and none of it is a calibration.

---

## 2. Circuit matrix

Resistor positions are written *top/bottom*: top = in series from the tap,
bottom = shunt to the divider ground rail. Rails: **3V3** = Pico 3V3(OUT);
**PGND** = Pico ground; **AGND-rail** = the breadboard ground rail that carries
B16 and both ADC divider bottoms (§3.3).

| # | Signal | Vehicle tap | Polarity at the pin | Fitted part / value | Class | GPIO | Rail | Proposed Rev A change |
|---|---|---|---|---|---|---|---|---|
| 1 | Vehicle speed | Cluster **B2**, BLU/WHT (PCM 32P t.9 on the A/T) | Pulses up from 0; counted on RISING | 22k / 33k, one 1N5819 anode→pin, cathode→3V3 | **F** (Oct 24) | GP2 | 3V3 | Upstream isolation; keep ratio (D4) |
| 2 | Tachometer | Cluster **B1**, BLU | Idles high, open-collector pulled to 0 | 22k / 6.8k, one 1N5819 to 3V3 | **F** (Oct 24) | GP3 | 3V3 | Upstream isolation; review top-of-range clamp margin (D4, D11) |
| 3 | Brake warning | Cluster **C14**, GRN/RED | Active **low** at the pin; logged inverted as `brake=1` = line grounded | 22k / 6.8k, one 1N5819 to 3V3 | **F** (Oct 23 fitted, Oct 24 diode corrected) | GP4 | 3V3 | Upstream isolation (D4) |
| 4 | Fuel sender | Cluster **C11**, YEL/BLU | Analog, 0–8.57 V full scale | 7.5k / 4.7k divider | **F** (Oct 24 07:14) | GP26 / ADC0 | 3V3 ref | Isolation only (D4); protection carried forward |
| 4a | Fuel protection | — | — | 1k series at the pin, **1 µF** to GND, 1N5819 to 3V3 **and** to GND, plus the tap-end fuse — fully as specified | **F** (Oct 29) | GP26 | 3V3 | Isolation only (D4) |
| 5 | Cluster supply | Cluster **B11**, YEL (driver's fuse 9, 7.5 A) | Analog, 0–18.75 V full scale; `< 155` counts = key out | 22k / 4.7k divider | **F** (Oct 24, confirmed connected) | GP27 / ADC1 | 3V3 ref | Isolation only (D4); protection carried forward |
| 5a | Supply protection | — | — | 1k series, **1 µF**, two 1N5819 and the tap-end fuse — fully as specified | **F** (Oct 29) | GP27 | 3V3 | Isolation only (D4) |
| 6 | Ignition, input side | **B11** → 1N5819 → 2.2k → opto LED anode (pin 1); LED cathode (pin 2) → **B16**; inline fuse on the feed | +12 V-active | PC817-class opto; **1N5819** series diode; **2.2k** series resistor; no input capacitor | **F** + **M** (Oct 29) | — | vehicle | Keep topology; see D15 |
| 7 | Ignition, output side | — | Collector LOW = ignition ON | Collector → GP5, emitter → PGND, **100 nF** across collector/emitter; pull-up is the RP2040 internal (`INPUT_PULLUP`) | **F** (Oct 26 / Oct 29) | GP5 | 3V3 | QREPORT + 10k to switched 3V3; capacitor retention and report-node timing remain conditional, §3.2a (D1) |
| 8 | Ground sense | Cluster **B16**, BLK (G501) | — | Lands on a breadboard ground rail jumpered to Pico **AGND**; both ADC divider bottoms use that same rail | **F** (Oct 24, owner correction) | AGND | — | Explicit single-point return (D5) |
| 9 | SD card | — | — | SPI0 breakout: DO/MISO→GP16, CS→GP17, SCK→GP18, DI/MOSI→GP19, module 3V3 from Pico **3V3(OUT)** pin 36, GND pin 23; 12 MHz | **F** + **M** (Oct 18) | GP16–19 | 3V3 | Stay on switched 3V3; add bulk cap (D6) |
| 10 | Supply | Auxiliary battery → external buck module | — | Buck 5 V output into the Pico's USB positive feed; own return; **manual** power only | **F** + **M** (Oct 26) | — | 5 V | Onboard switched LM2678 + QP (D7) |
| 11 | HOLD | — | — | **Nothing fitted.** No autonomous power circuit exists | **U**/none | (GP6 proposed) | — | D2 |

Pins not in the matrix: GP23/24/25/29 are CYW43 resources and are not available.
GP6–GP15, GP20–GP22 and GP28 carry nothing today.

---

## 3. What the matrix is worth per channel

### 3.1 The three digital cluster cells

One 1N5819 per cell, anode to the pin, cathode to 3V3, no lower clamp. Owner
confirmed all three on October 24, replacing the BAT54 drawn in the historical
as-built diagram. VSS is the odd cell: 22k/**33k**, not the 22k/6.8k shared by
tach and brake.

The owner's inventory, named on October 29 as
`/srv/agent_share/inventory/inventory_list.md`, independently corroborates the
part correction: it lists 100 Chanzon 1N5819 (1 A, 40 V, DO-41 axial) and a
PC817 in an IC assortment, and contains **no BAT54 of any type**. Read that
only as corroboration of C-02. The owner states the inventory is mostly
accurate, incomplete and possibly includes consumed stock, and stock is neither
evidence that a part is fitted nor evidence that it is electrically suitable.

Verification status per channel, which is not uniform:

- **Tach** — scoped at the cluster, October 15: rests at 14.8 V charging /
  12.0 V engine off, pulled to 0 V, 3.8 ms low pulse, 87.8 % duty high, 32.0 Hz
  at ~1000 rpm, 2 pulses per crank revolution. **M.**
- **VSS** — confirmed by driving (11.1 miles against the trip meter), never
  scoped. The FSM says "0 to about 5 V or more"; **the pulse amplitude has no
  measured upper bound** (U-06). **M** for function, **U** for amplitude.
- **Brake** — toggle-tested October 23 over five full lever cycles with no
  chatter, and independently corroborated: the column broke out of a stuck `1`
  at the same second as the `IGN state=off -> on` note, because the warning lamp
  is fed from fuse 9 → B11. **M.**

Derived level checks against the fitted ratios, at a nominal 0.3 V Schottky drop
at microamp currents:

| Cell | Tap voltage | Pin voltage | Divider draw | Clamp onset at the tap |
|---|---:|---:|---:|---:|
| VSS 22k/33k | 5.0 V | 3.00 V | 90.9 µA | **6.0 V** |
| Tach 22k/6.8k | 14.8 V | 3.49 V | 514 µA | **15.25 V** |
| Brake 22k/6.8k | 11.3 V | 2.67 V | 392 µA | 15.25 V |
| Brake, charging | 14.1 V | 3.33 V | 490 µA | 15.25 V |

Two margins in that table are thinner than the record discusses anywhere, and
both are recorded here as findings rather than defects:

- The **tach** cell idles 0.45 V below its own clamp onset. A charging rail at
  15.3 V — within normal alternator spread — puts the fitted 1N5819 into
  continuous conduction at the high level. The diode's forward voltage at tens
  of microamps is not a specified quantity (the 1N5819 datasheet specifies
  V<sub>F</sub> at 1 A), so the onset itself is uncertain to a hundred millivolts
  or so. See U-07.
- The **VSS** cell clamps above 6.0 V at the tap. The FSM's "about 5 V or more"
  does not exclude a 12 V open-collector swing, which would hold the clamp in
  conduction for 88 % of each cycle. See U-06.

The dividers limit current, but these estimates alone do not establish clamp
voltage, permissible injection or logging behavior across faults. Retain these
questions in the Rev A ratio and off-state review before reusing the cells.

The measured brake-branch Thevenin is the one genuinely characterised vehicle
source on the board: **375 mA** through C14 to ground with the lever down
(max 395, min 366, avg 375), which is ~32 Ω hot and ~3.6 Ω cold filament, and
0 V with continuity to ground with the lever up. That measurement is what
settles direct-to-GPIO quantitatively: 2.4 A into a pin clamp on cold contact.
The divider's 392 µA is 0.105 % of the lamp's own current, three orders below
its rated current, so it cannot light the lamp.

**Signal bandwidth the as-built chain actually carries**, needed by anyone
inserting isolation in series (§REV_A_INTERFACES.md 4):

| Signal | Highest expected rate | Narrowest feature |
|---|---:|---|
| Tach | ~217 Hz at 6500 rpm (2 pulses/rev) | 3.8 ms low pulse at idle |
| VSS | ~91 Hz at 80 mph, from the published 4104.3 pulses/mile | not measured |
| Brake, fuel, supply | level / minutes | — |

The firmware's `GLITCH_US = 100` rejects edge pairs closer than 100 µs. Against
the fastest real signal that is a factor of about **46**: a 217 Hz tach has a
4.62 ms period, not the four decades an earlier revision of this document
claimed. 46x is comfortable for a nominal waveform, but minimum pulse width and
edge integrity need their own evidence — neither is established here, and U-06
is the open amplitude question on the other channel. The sketch comment's "VSS
at 80 mph a few hundred [Hz]" is conservative by about 3x against the project's
own pulse constant.

### 3.2 The two analog channels

Both dividers sit at the Pico end, within a few centimetres of GP26/GP27; the
C11 and B11 sense wires arrive from the cluster at full signal voltage and are
divided only at the point of measurement. Nothing was added behind the cluster;
the existing Mini-Fit Jr taps are untouched. The specification's reasons are
sound and should survive Rev A: the C11 node is driven by R<sub>g</sub> ‖ R<sub>s</sub> =
52 ‖ 26 = **17.5 Ω**, and moving the divider to the cluster would hand the long
harness run a 2889 Ω Thevenin instead — 165x higher, in the environment that
produced 1.86 V peak-to-peak on that very wire.

| Channel | Top/bottom | Ratio | Full scale | Divider load | Thevenin |
|---|---|---:|---:|---:|---:|
| Fuel, C11 → GP26 | 7.5k / 4.7k | 0.3852 | 8.57 V | 12.2 kΩ | 2889 Ω |
| Supply, B11 → GP27 | 22k / 4.7k | 0.1760 | 18.75 V | 26.7 kΩ | 3873 Ω |

**The specified protection is fitted.** The specification calls for, per
channel, a 1 kΩ series resistor at the pin, a 1 µF capacitor to ground, two
1N5819s (one to 3V3, one to GND) and a 100 mA fuse at the *tap* end of the wire.
No installation note ever confirmed any of it — the October 24 entry records only
that "the fuel divider" was fitted, the B11/B16 entry says "as-built
divider/protection details and post-install DMM readings" were not supplied, and
the same day's capacitor note still listed the 1 µF on GP26/GP27 as "specified,
not yet fitted". On that basis this document originally assumed the whole of
rows 4a and 5a was absent. **The owner's October 29 part count settles it the
other way**, and a count is physical evidence where a missing note is not:

| Part type | Predicted by the records | Owner count |
|---|---:|---:|
| Diodes: 3 digital clamps + 4 ADC clamps + 1 opto series | 8 | **8** |
| Capacitors: 2 x ADC 1 µF + 1 opto output 100 nF | 3 | **3** |
| Capacitor at the SD module | 1 if fitted | **0** |

Both totals match exactly with nothing left over, so each ADC channel has its
pair of 1N5819s and a filter capacitor, and the optocoupler has its output
capacitor. The owner gave the values with the count: 1 µF on each ADC channel
and 100 nF on the opto output (§3.2a). Two further things fall out of the same
arithmetic:

- **There is no input-side capacitor on the optocoupler.** The clock-tap cell's
  2.2 nF is either removed or is now the capacitor across the output; a fourth
  capacitor would be needed for both to exist. This answers what the October 26
  report left open.
- **Both 1 kΩ series resistors are fitted.** The owner counted **13** resistors,
  which is the full predicted set: 2+2+2 for the three digital cells, 3+3 for
  the ADC channels including their 1 kΩ, and 1 for the opto. Eleven would have
  meant neither 1 kΩ was present. This agrees with independent evidence in the
  October 24 leakage check — "midpoint and GP26 read identical … the drop across
  the 1 kΩ is below DMM resolution" — since measuring a drop across that
  resistor presupposes it exists. Each ADC channel therefore presents the
  specified 1 kΩ at the pin, and the published Thevenin-plus-1 kΩ figures used
  throughout the power documents describe the real circuit.

The C11/B11 tap-end fuses cannot be established by the board count, but the
owner separately confirmed their presence on October 29. Their specified rating
is 100 mA; fitted ratings remain unconfirmed. No further presence check is open.

### 3.2a Capacitor values, and the one real consequence

Owner, October 29: **100 nF across the optocoupler output, 1 µF on each of the
two ADC channels.** So both analog channels have the specified filter. U-13 is
closed.

**The filter poles, computed for the documented topology.** The specification's
§4 diagram puts the capacitor on the *GPIO side* of the 1 kΩ, so the resistance
charging it is the divider Thevenin **plus** that 1 kΩ:

| Channel | Resistance seen by the 1 µF | Nominal pole |
|---|---|---:|
| Fuel | (7.5k ‖ 4.7k) + 1k = 3889.34 Ω | **40.92 Hz** |
| Supply | (22k ‖ 4.7k) + 1k = 4872.66 Ω | **32.66 Hz** |

Assumptions: ideal source, nominal values, negligible ADC and leakage loading,
`fc = 1/(2πRC)`. **This corrects an error in an earlier revision of this
document**, which used the Thevenin resistance alone and reported 55 Hz and
41 Hz. Those figures came from the historical specification's own prose, which
inherited the same omission; reproducing a source's arithmetic is not
independent validation of it. The corrected poles are *lower*, i.e. more
rejection than claimed, so the impulsive-noise case is unaffected — but the
numbers now match the circuit as drawn. If the fitted capacitor is actually on
the divider side of the 1 kΩ, that connection must be recorded explicitly rather
than computed with an incompatible model.

The 100 nF is on the position that matters, and it produces the one genuine
electrical finding in this consolidation.

**The GP5 node is heavily filtered, and that is almost certainly deliberate.**
100 nF against the RP2040's internal pull-up puts the node corner at **26.5 Hz**.
For an ignition level sampled once a second that is a sensible trade: it
attenuates coupled noise, though immunity to arbitrary ignition transients is
not established here. The ON edge depends on the optocoupler's sink current and
saturation; its discharge time is not established by this RC charging
calculation. The recorded manual-power operation remains useful evidence:
firmware reads GP5 at 1 Hz for the log and at about 20 ms in the network path,
so a slow rise is invisible.

**But the OFF edge cannot meet the LRA-01 observation budget with the internal
pull-up.** `INTERFACE_CONTRACT.md` §2 defines `HIGH >= 3.0 V` as IGN_Q = 0, and
§3 requires firmware to observe that transition within **10 ms**. The RC rise
alone, before firmware samples anything:

| Pull-up on the GP5 node | τ | Time to 3.0 V | Against the 10 ms budget |
|---|---:|---:|---|
| Internal, 50 kΩ (fast end of the RP2040 spread) | 5.00 ms | **11.99 ms** | over |
| Internal, ~60 kΩ (this project's working figure) | 6.00 ms | **14.39 ms** | over |
| Internal, 80 kΩ (slow end of the spread) | 8.00 ms | **19.18 ms** | over |
| A 10 kΩ pull-up, if the capacitor is retained on this node | 1.00 ms | **2.40 ms** | 7.6 ms left |

The result does not depend on the assumed pull-up value: it exceeds the budget
across the whole specified spread. Two qualifications, both material:

- **This is nominal arithmetic**, for an ideal 100 nF charging from zero to a
  nominal 3.3 V rail. It is not a worst-case timing qualification and it does
  not by itself prove a firmware defect. Rail tolerance, capacitor tolerance and
  bias behaviour, opto leakage and pull-up spread all have to be carried through
  before anything is called closed.
- **The pin reads logic HIGH sooner.** The RP2040 specifies V<sub>IH</sub> =
  **2.0 V** at IOVDD = 3.3 V (datasheet §5.5.3.4, table 625); the
  `0.65 × IOVDD` formula an earlier revision of this document used belongs to
  the 1.8 V row, and that error is corrected here. Times to 2.0 V are **4.658 /
  5.589 / 7.452 ms** at 50 / 60 / 80 kΩ. V<sub>IH</sub> is a guaranteed
  input-level boundary, not a measured switching threshold. So it is the
  contract's deliberately stricter 3.0 V criterion that the RC misses, not the
  silicon's guaranteed level.

Three consequences, and none of them is a defect in what is built:

1. **Rev A is a different circuit on this node, so the capacitor's fate is a
   decision, not a carry-over.** Rev A disconnects the opto collector from GP5
   altogether: the optocoupler output moves to the A5 qualification network, and
   **QREPORT** — not the optocoupler — sinks the 10 kΩ pull-up on GP5
   (`CUTOFF_MARGIN_REVIEW.md` §2). Whoever freezes that node must state
   explicitly whether a 100 nF is placed on the QREPORT/GP5 report node. If it
   is, the same arithmetic applies and gives 2.40 ms against the 3.0 V criterion
   with a 159 Hz node corner; if it is not, the node is fast and the report
   delay is QREPORT's own. Either way the external 10 kΩ remains the power
   contract's existing candidate — this finding does not request a pin or
   topology change, and it is not a timing closure.
2. **If anyone ever proposes keeping the internal pull-up in qualified mode**,
   the capacitor must come down to **≤52 nF** to hold 10 ms at the worst-case
   80 kΩ (≤70 nF at 60 kΩ, ≤83 nF at 50 kΩ). Recording the limit so the trade is
   explicit rather than rediscovered on a bench.
3. **The observation budget must be stated to include this RC.** The contract's
   10 ms is written as a firmware sampling requirement; the GP5 node's own
   settling time has to be counted inside it, not assumed to be zero. See
   REV_A_INTERFACES.md §8.

### 3.3 Grounds and returns, as built

- **B16** lands on a breadboard ground rail that is jumpered to Pico **AGND**
  (physical pin 33). Both ADC divider bottoms use that same rail. This is the
  specification's single-point requirement as actually built, and it is correct:
  a common-mode offset largely self-cancels in the fuel computation
  (dR<sub>s</sub>/dd = 14 Ω/V, i.e. 0.14 Ω per 10 mV), while a *differential*
  offset between the two channels does not cancel at all.
- The **opto output return** is ordinary Pico **PGND**, not the AGND rail.
- The **buck** has its own return into the Pico's USB positive/negative feed.
- AGND and GND are connected inside the Pico. Combined with the B16 reference,
  **this installation is not galvanically isolated across the optocoupler**, and
  must not be described as isolated anywhere downstream.
- Measured October 24 14:56: **Pico GND to chassis = 21 mV** (polarity not
  reported). No measurement exists between B16's local termination and the
  divider ground, and the owner withdrew the request on the ground that they are
  the same intended node in the confirmed layout.

### 3.4 Ignition

Current source and return, owner-reported October 26, superseding the earlier
clock-harness feed:

```text
Cluster B11 ── series diode ── series resistor ── opto LED anode
Cluster B16 ───────────────────────────────────── opto LED cathode

Opto collector ────────┬──────── Pico GP5   (internal pull-up; LOW = ON)
                       │
                  capacitor
                       │
Opto emitter ──────────┴──────── Pico PGND
```

The capacitor is across the **output** collector/emitter, i.e. GP5 to PGND, and
the owner gave its value on October 29 as **100 nF**. It is *not* the input-side
2.2 nF of the older clock-tap sketch and of keyless U13's cell, and the two must
not be conflated; the part counts show there is no input-side capacitor at all.
Its effect on the GP5 edge is the one electrical finding of this consolidation —
see §3.2a. The series diode is a 1N5819 per the owner; the series resistor is
**2.2k, measured by the owner on October 29** (§3.4a).

**Historical continuity.** The previous manager's wiring discussion retained
an existing optocoupler cell and moved its input feed from the clock harness to
B11/B16. Before the October 29 owner statements, history only suggested the
series diode and resistor values; it did not confirm them. The reported 1N5819,
measured 2.2k and reported output capacitor now supersede that uncertainty.

The topology is deliberately not new: the historical record states outright that
the logger's ignition cell is a copy of keyless **U13**'s +12 V-active PC817
cell — `wire → 1N5819 → 2.2k → LED → GND` — and the keyless schematic confirms
`R12 = 2.2k`, `D4 = 1N5819`, `C12 = 2.2 nF` on the input side, with no external
collector pull-up because the firmware uses `INPUT_PULLUP` (GP14, active low).
The logger reads the same way on GP5. **Do not rediscover this topology, and do
not transfer keyless component values into the logger as-built BOM**: the
documented differences at the time of the copy were a different pull-up source,
an added inline fuse, a different tap and a different output pin, and the
October 26 rewiring changed the tap and the output again.

One historical hazard is resolved by the rewiring and must not be carried
forward as if it were still live: GP5 formerly shared the opto collector node
with the **Pi's 1.8 kΩ pull-up to the Pi's 3.3 V rail**, which back-fed IOVDD at
1.44 mA through the pin clamp with the Pico unpowered. The quantified decision
was a 4.7 kΩ series resistor (0.40 mA, GP5 still reading 0.43 V against a 0.99 V
V<sub>IL</sub> limit), and its status on October 24 was **not yet fitted**. The
October 26 as-built describes a dedicated opto output into GP5 with a Pico-GND
return and no Pi node. **The owner confirmed on October 29 that the Pi is out,
the clock-harness tap is removed and ignition sense is consolidated on B11**, so
the 1.8 kΩ is not on the node and the 1.44 mA hazard is closed. The 4.7 kΩ
series resistor decided against it was never fitted and is not outstanding.

### 3.4a Reported diode types and measured opto resistor

**Diodes.** Owner, October 29: all eight are **1N5819**. That is a belief about
the build rather than a part-by-part reading, but it is corroborated by the
inventory, which holds 100 Chanzon 1N5819 and whose only other rectifiers are
five 1N4002. It also makes U-07 — the unspecified forward voltage of a 1N5819 at
tens of microamps — apply uniformly to all eight positions rather than to three.

**The series resistor is 2.2k, measured.** The owner measured the resistor
between the 1N5819 and the optocoupler's pin 1 on October 29, rather than
inferring it from the cell's history. That matters: the same value would have
been *assumable* from provenance, and a value carried forward by assumption is
exactly what produced conflicts C-01, C-02 and C-03. It is class **M**, and it
agrees with the original deliberate choice of 2.2k over the 1k of a 5 V circuit,
because 1k at 12 V would pass 10.8 mA — three times what the factory puts on
this signal.

The project's netlist also fixes the pinout this sits on: `U13 pin 1` fed
through R12, `pin 2` to ground, `pin 4` the collector, `pin 3` the emitter. In
the logger, pin 2 returns to B16 with nothing in series.

**What the confirmed value buys.** The resistor sets the LED current, and the
output only has to hold GP5 low:

| At the fitted 2.2k | Value |
|---|---:|
| LED current at B11 = 11.93 V (1N5819 + 1.2 V LED) | 4.72 mA |
| LED current at 14.4 V charging | 5.84 mA |
| Collector current needed, as-built internal pull-up | 55 µA |
| QREPORT sink-current screen for the separate Rev A 10 kΩ pull-up | 330 µA; not the optocoupler load |
| Conditional screen at 50 % CTR | 2.36 mA |
| Ratio to the as-built requirement | **43x** |

**These are conditional screens, not guarantees.** Sharp's 50 % CTR minimum is
specified at I<sub>F</sub> = 5 mA, V<sub>CE</sub> = 5 V and T<sub>a</sub> =
25 °C. The fitted LED runs at **4.72 mA**, below that condition; the part is
PC817-*class* from an assortment kit rather than an identified Sharp device; and
hot CTR is unproved — `COMPONENT_MARGIN_CLOSURE.md` already records that "hot
PC817 leakage/CTR at actual LED current is unproved" and that generic stock does
not inherit Sharp's specifications. The 43x ratio says the as-built has large
nominal headroom, which is consistent with the recorded road operation; it does
not establish saturation at any corner.

The Rev A figure is **not** a comparable number and an earlier revision of this
document wrongly presented one. In Rev A the optocoupler drives IGN_A/IGN_RC in
the A5 qualification network, not a 10 kΩ GP5 pull-up, so its endpoint and CTR
requirements come from that network and must be analysed against it.

The measured resistance is useful evidence for the as-built. It still matters to:

- the LRA-01 opto endpoint and 400 ms qualification budget, which depends on
  actual LED current and the IGN_RC filter — now computable from a measured
  resistor rather than an assumed one;
- hot CTR and opto leakage in the parked ledger, where
  `COMPONENT_MARGIN_CLOSURE.md` already notes that "hot PC817 leakage/CTR at
  actual LED current is unproved" and that generic stock does not inherit Sharp's
  specifications;
- the R02 protection decision — see the next point, which is the useful one.

**The fitted 2.2k is a candidate answer to a defect the power contract flagged.**
`INTERFACE_CONTRACT.md` §6 rejects its own IGN sizing because "RLED upper sizing
is 28²/990 = 0.792 W, above its 0.5 W rating" at the 28 V protected-input
ceiling. Compare nominal resistance-only screens against a hypothetical
0.5 W rating, without assigning that rating to the fitted part:

| RLED | Dissipation at 28 V | Against a 0.5 W part |
|---|---:|---|
| As-built 2.2k (measured) | **0.356 W** | below a hypothetical 0.5 W rating; fitted rating and hot derating unknown |
| Power candidate 990 Ω | 0.792 W | **over rating**, as the contract states |

Both figures are **nominal arithmetic on resistance alone**. 0.356 W is not
proof of the fitted resistor's wattage rating, tolerance, hot derating or pulse
capability, none of which is known — the fitted part's power rating is not
recorded anywhere, and R02 and R03 remain open. This is offered to the
electrical lead as an input, not as a resolution: the Rev A chain feeds an
analog qualification stage rather than a bare GPIO, so its CTR and endpoint
requirements may not be satisfied by 4.7 mA. The point is only that a measured,
already-fitted value is worth evaluating before a new part is specified.

### 3.5 SD

Wired and electrically cleared October 18, and the measurements are the reason
MISO on GP16 is safe rather than lucky: with the module wired, no card inserted
and the Pico powered, the module's 3V3 pin read **3.3 V** and DO/MISO and
DI/MOSI both read **0 V**. The topology makes over-voltage impossible — the
shifter's output cannot exceed its own supply, and that supply is the Pico's
3.3 V whatever a card does. 12 MHz is chosen for the level shifter and jumper
wires, not for bandwidth; 1 Hz of 40-byte lines is 40 B/s against a 512-byte
sector. Card on hand: 16.0 GB SDHC, FAT32, 8 KiB clusters, single MBR partition.

The gate attached to that clearance still stands for **any** rail change: before
connecting MISO to GP16 on a module powered from 5 V, insert a card, leave MISO
unconnected and measure MISO to GND; above ~3.6 V, stop. The known cost of the
3V3 choice is the current budget — the card's write current comes from the Pico's
own regulator, which has roughly 300 mA to share with the RP2040 and the CYW43,
against SD write spikes of 100–200 mA. A 10–100 µF bulk capacitor at the module
is the documented cheap preventative, and the owner confirmed on October 29 that
**none is fitted** (U-04 closed), so those spikes land directly on the shared
regulator. The symptom to watch is the board rebooting during a write, which the
report-stall check cannot see because a reset produces a negative time delta.

### 3.6 Supply, and what the current figures do and do not bound

An auxiliary-battery buck module feeds 5 V into the Pico's USB positive feed
under **manual** power. No autonomous power circuit, latch, HOLD path or cutoff
is fitted; the entire `logger/hardware/power/` package is a candidate.

Measured October 26 with a Fluke in DC A mode between the buck's 5 V positive
and the USB positive feed — therefore **excluding** buck input losses and the
buck's own quiescent current:

| Condition | Current |
|---|---|
| Settled, repeated startup and IGN-off-window trials | ~**51 mA** |
| Trial maxima | 88, 96, 101, 89 mA |
| Later trials' minima | 46 mA |
| Sustained after the latest drive, then returning to 51 mA | 72–80 mA |
| Whole-trip meter readings | 96 max / 46 min / 53 avg mA |

The higher interval is provisionally attributed to upload. Trial 1's zero
minimum includes an intentionally unplugged start and is not measured powered
sleep. At a nominal 5 V, 51 mA is 0.255 W. **This is a powered-branch
measurement at the 5 V node. It is not a battery-side figure, not an off-state
leakage figure, and it bounds neither inrush nor fast transients.** Meter model,
capture timing and exact durations are unknown. No measured off-state current
exists anywhere in this project.

---

## 4. Cross-check: logged counts against the owner's DMM

Worth doing once, because it is the only end-to-end check of the fitted analog
chain that the existing record contains the ingredients for but never performed.
Conditions: October 24, ignition II, engine off, charger not independently
confirmed; logger confirms `ign=1` and RPM 0 throughout. DMM seconds unknown, so
whole-minute logger windows are used. 12-bit reads, nominal V<sub>REF</sub> = 3.3 V.

| Channel | Logger, 14:57 window | → volts at pin | → volts at tap | DMM at 14:57 | Difference |
|---|---|---:|---:|---:|---:|
| Supply B11 | mean 2596.42 counts (2593–2599, SD 1.49) | 2.0924 V | 11.886 V | 11.93 V | **−43.7 mV, −0.37 %** |
| Fuel C11 | mean 893.08 counts (891–894, SD 1.05) | 0.7197 V | 1.868 V | 1.847 V | **+21.2 mV, +1.15 %** |

Both agree to within about 1 %, which is the first independent evidence that the
two fitted dividers have their specified ratios and that neither channel is
mis-wired. It is **not** a calibration and must not be used as one: the ADC's
own gain/offset error is unmeasured, V<sub>REF</sub> is assumed rather than
measured, the resistors are 1 % parts, the readings are not simultaneous, and
the DMM's own accuracy is unstated.

The fuel channel's +21.2 mV residual is the same size as the measured 21 mV
Pico-GND-to-chassis offset. That is noted and **not** explained: the signs were not
reported, the two measurements are a minute apart, and a 1 % divider tolerance
spans the same range. Resolving it is the ground-offset check in the historical `fuel/ADC_INTERFACE_SPEC.md` §9 step 3, not an
inference from these two numbers (U-05).

---

## 5. Conflict register

Each conflict names the losing source so nobody re-imports it.

| ID | Conflict | Resolution | Authority / date | Owner of the fix |
|---|---|---|---|---|
| C-01 | VSS cell bottom resistor: 6.8k (`SPEC.md`, `README.md`, `accord-logger.ino:31`) vs 33k (as-built diagram) | **33k.** Resistor values in the as-built diagram were right; the two documents were corrected | Oct 23 correction | Firmware owner should fix the sketch comment (no code change) |
| C-02 | Clamp part: BAT54 / "Schottky" (as-built diagram, sketch comments, `SPEC.md` 5.1) vs 1N5819 | **1N5819**, one per digital cell. The project has never owned a BAT54 | Owner confirmation, Oct 24 | Firmware owner (comment); nobody may order BAT54 |
| C-03 | Fuel/supply clamp: BAT54S (`ADC_INTERFACE_SPEC.md` §4) vs two 1N5819 | **Two 1N5819 per channel**, one to each rail; through-hole, owner-reported fitted, proven on three channels | Oct 24 correction | Analog reviewer, at D3 |
| C-04 | B11/B16 state: "specified, not pulled" (`CLUSTER_PINOUT.md`, Oct 24) vs connected | **Connected.** The pinout extract was written earlier the same day | Owner report + logged supply response, Oct 24 | Closed here |
| C-05 | Ignition source: clock harness / Pi-era feed vs cluster B11/B16 | **B11 input, B16 return, output to GP5 on PGND.** The clock tap is physically removed and ignition is consolidated on B11 | Owner reports, Oct 26 and Oct 29 | Closed |
| C-06 | GP5 pull-up: Pi 1.8 kΩ shared node vs Pico internal | **Pico internal.** The Pi is out; its pull-up is not on the node | Owner reports, Oct 26 and Oct 29 | Closed |
| C-07 | Startup/qualification rules: raw GP5 + 100 ms software debounce (`DESIGN.md` §1) vs one hardware-qualified IGN_Q | **Hardware-qualified**, per `INTERFACE_CONTRACT.md` E02 / D-RA-03. Never mix the two rule sets | LRA-01 candidate, Oct 28 | Electrical lead; recorded, not re-decided here |
| C-08 | Brake column meaning: "parking brake" vs brake-system **warning** line | **Warning line grounded.** Low brake fluid grounds it too; the lamp can also light without C14 grounded | FSM topology + Oct 23 | Closed; already correct in firmware and `CARD_FORMAT.md` |

---

## 6. Unknown register

Every row has a proposed resolution and a responsible role. Precise owner and
bench questions are collected in §7 so they can be asked in one pass.

| ID | Unknown | Why it matters | Proposed resolution | Role |
|---|---|---|---|---|
| ~~U-01~~ | **CLOSED October 29.** The counts (8 diodes, 3 capacitors, 13 resistors) confirm every on-board element of rows 4a and 5a — both 1 kΩ series resistors, both 1 µF filters, all four clamp diodes — and the owner confirms the tap-end fuses are in place. The ADC channels are fitted exactly as specified | Presence confirmed; ratings and fault qualification are separate | No repeated presence question | Closed |
| ~~U-02~~ | **CLOSED October 29.** Output capacitor 100 nF, series diode 1N5819, series resistor **2.2k measured**, no input capacitor, inline fuse present. Nominal values/presence reconstructed; exact opto identity and fuse/resistor ratings remain unconfirmed | — | No repeated nominal-value question; qualify actual Rev A endpoints and ratings | Closed |
| ~~U-03~~ | **CLOSED October 29** by owner statement: the Pi is out, the clock tap is removed, ignition sense is consolidated on B11 | — | None; see the owner correction above | Closed |
| ~~U-13~~ | **CLOSED October 29:** 100 nF on the opto output, 1 µF on each ADC channel. This created a finding rather than leaving a gap — the GP5 OFF edge cannot meet the contract's 10 ms budget with the internal pull-up (§3.2a) | — | None for the as-built. The design consequences are REV_A_INTERFACES.md D1 and §8, for the electrical and firmware reviewers | Closed |
| ~~U-04~~ | **CLOSED October 29:** there is **no** capacitor at the SD module, so 100–200 mA write spikes sit directly on the Pico's shared ~300 mA regulator | — | None. Fitting one becomes a Rev A proposal (D6); the bench should still watch for resets during writes with the reset-aware check | Closed |
| ~~U-14~~ | Back-feed into the unpowered 3V3 rail | **CLOSED October 29, measured exactly.** Everything seated and the Pico unpowered, B2 draws **140.8 µA** from the tap: **31.6 µA** through the 33k to ground and **109.2 µA through a forward-biased clamp into the Pico's own 3V3 rail**, which sits at 0.883 V with no power applied. One branch is **141 % of the entire 100 µA whole-system parked budget** and **17.6×** the 8 µA allocated to all five. The board is partially energized while parked. This is the one row of REV_A_INTERFACES §6's off-state matrix established by measurement | None | Closed |
| U-05 | Sign and stability of the 21 mV Pico-GND-to-chassis offset, and the differential offset between the two ADC channels | A differential offset does not cancel in the fuel computation; 10 mV is 0.14 Ω of R<sub>s</sub> | `ADC_INTERFACE_SPEC.md` §9 step 3, with signed readings and both channels | Owner + analog reviewer |
| U-06 | VSS pulse amplitude at B2, upper bound | Sets whether the 22k/33k cell clamps in normal operation and what it injects when the board is off | Scope one capture at the tap while driving above 2 km/h; the FSM minimum is "about 5 V or more" | LRA-07 |
| U-07 | 1N5819 forward voltage at 10–100 µA, hot and cold | Sets the tach cell's clamp onset, now estimated 0.45 V above its measured idle | **First measured point, October 29: 159 mV at 109 µA, room temperature**, derived from the B2 clamp (1.042 V pin against 0.883 V rail). That is a Schottky drop, consistent with the 1N5819 the record claims, so the part identity is corroborated rather than merely reported. **Does not close this row** — hot and cold are still open, and V<sub>F</sub> falls further below 109 µA, so clamp onset is *lower* than a 0.3 V assumption gives and **D11's margin is correspondingly smaller than estimated**. Analog reviewer to carry it through | Analog reviewer |
| U-08 | Source impedance of B2 (PCM output) and B1 (tach driver), and each one's permissible load | Required before any loading change | **B2's parked source measured exactly October 29: 3,757 Ω.** All readings share one configuration — dividers, clamps, Pico module and SD module seated, Pico unpowered with the USB lead off. Four readings close it with no assumption left: 4.669 V open-circuit, 4.140 V at the tap loaded, **1.042 V at the 22k/33k junction**, 0.883 V on the clamp cathodes. Earlier 7.03 kΩ and the clamp-V<sub>F</sub> range are superseded. Still the *parked* source — an always-on pull-up to about 4.67 V, not the PCM driving — so the permissible-load question stays open, though the pull-up already sinks **1.24 mA** whenever B2 is pulled low and the divider adds **11.3 %** to that. B1's source remains unmeasured |
| U-09 | C11 open-circuit voltage and the FSM's unexplained 5–8 V unloaded band | The 0.3852 ratio was chosen for an 8 V ceiling that the measured supply law cannot reach | Analysis against the FSM; no hardware change until it resolves | Fuel analyst (FUEL-01), not a Rev A gate |
| ~~U-10~~ | **CLOSED October 29** by owner measurement, key out and parked: **B2 = 4.140 V** (loaded; 4.669 V open-circuit), **B1 = 0 V**, **C11 = 0 V** to chassis | B1 and C11 are confirmed dead. **B2 is energized when parked, which the design assumed it was not.** Draw on that branch is **140.8 µA** — see U-14; the divider is not the only load, because the clamp conducts — against an 8/20 µA allocation for all five branches and a 100 µA whole-system parked budget, which one branch alone exceeds | Narrows D4 to B2 alone. The loaded/open-circuit question is **answered**: 4.140 V is the loaded value and 4.669 V the open-circuit one, so 75.3 µA is flowing, not an upper bound. See U-08 | Closed |
| U-11 | Physical envelope: board footprint, enclosure, mounting, harness lengths, connector locations | LRA-08 cannot place connectors without it | **Partially closed October 29 by the owner.** No enclosure and no mounting decided: the circuit currently sits on breadboards loose in the cabin. Mounting behind the gauge cluster was considered and set aside. The plan is a **generic rectangular board** carrying the Pico module, the SD module and the remaining circuitry. Size reference given is the present breadboard area: a **82 × 55 mm half-size board plus a 46 × 36 mm mini**. SD needs `PinHeader_1x06_P2.54mm_Vertical` plus a square area of about 16 mm (read as 16 mm on a side, ≈256 mm²; **confirm**, since a literal 16 mm² is 4 × 4 mm and smaller than a microSD socket). **Still open: the chosen board outline, mounting method, harness lengths and connector positions.** See `D-ENVELOPE-01` for why the breadboard area is not a sufficient target | Owner, then LRA-08 |
| U-12 | Fitted resistor tolerances and series on all five dividers | The specification asks for 1 % metal film, 50–100 ppm/°C, all four ADC parts from one series, so the tempcos partly cancel in the ratio | Owner reads the bands / part labels | Owner |

---

## 7. Questions for the owner and for the bench

Collected so one inspection pass answers the record's open items. These are
documentation questions; none of them is an authorization to change wiring.

**Owner inspection, no tools beyond a DMM** (U-01 through U-04 are now closed
or nearly so; U-10 and U-12 remain):

1. **Answered October 29:** on each ADC channel the 1 kΩ, the 1 µF and both
   clamp diodes are present, and the tap-end fuses are in place. Nothing open.
2. **Answered October 29:** 1N5819 series diode, 2.2k series resistor
   (measured), 100 nF across the opto output, no capacitor on the LED side,
   inline fuse present. Nothing open.
3. **Answered October 29:** the Pi is out and the clock-harness tap is removed.
   Nothing open.
4. **Answered October 29: no SD capacitor; three capacitors, eight diodes and
   thirteen resistors on the build, 100 nF on the opto output and 1 µF on each
   ADC channel.** Nothing further needed here; §3.2a records what the 100 nF
   means for the Rev A timing budget.
5. What are the resistor tolerances and the series/type of the five dividers'
   parts?
6. **Answered October 29**, key out and parked: B2 = **4.140 V**, B1 = **0 V**,
   C11 = **0 V** to chassis. B2 is live with the key out; the other two are not.
   One follow-up: was that 4.140 V read with the logger's divider connected or
   disconnected? Loaded, it is 75.3 µA flowing today; open-circuit, the real
   figure depends on B2's source impedance, which is still U-08.
7. What physical space does the logger have to live in — rough envelope,
   mounting, and where the cluster harness and the aux-battery feed enter it?

**Bench, under separate authorization** (LRA-07):

8. One scope capture of B2 while driving above 2 km/h, for the VSS amplitude.
9. Signed Pico-GND-to-chassis and per-channel divider-ground offsets, both ADC
   channels, ignition II, engine off, charger disconnected.
10. Opto LED current at 12 V and 14.4 V against the computed 4.72 / 5.84 mA, and
    the GP5 rise/fall with the fitted 100 nF — the measurement that would confirm
    §3.2a's timing table on real hardware.

---

## 8. Evidence index

Each fitted or measured assertion above, with its dated source. Source paths are
in the historical repository at the revision recorded in
[SOURCE_MANIFEST.json](SOURCE_MANIFEST.json).

| Assertion | Date | Source |
|---|---|---|
| Three digital cells are 1N5819, not BAT54 | 2026-10-24 | `circuits.md`, "CORRECTION 2026-10-24"; corroborated by the owner's inventory (no BAT54; 100x 1N5819) |
| VSS 22k/33k; tach and brake 22k/6.8k | 2026-10-23 / 24 | `circuits.md` same section; `CLUSTER_PINOUT.md` |
| Tach waveform: 14.8 V rest, 0 V active, 3.8 ms, 87.8 %, 32.0 Hz at ~1000 rpm, 2/rev | 2026-10-15 | `circuits.md`, "Tach — SOLVED" |
| VSS is PCM-synthesised on the A/T, 32P terminal 9, nothing below ~2 km/h | 2026-10-15 | `circuits.md`; FSM p. 22-71 |
| Brake branch 375 mA (395/366), ~32 Ω hot, ~3.6 Ω cold; divider 392 µA | 2026-10-23 | `circuits.md`, "MEASURED 2026-10-23" |
| GP4 brake tap toggling, five clean cycles, ignition dependency corroborated | 2026-10-23 | `circuits.md`, "VERIFIED 2026-10-23" |
| Fuel divider fitted at the Pico end on the C11 tap; B11/B16 not yet wired | 2026-10-24 07:14 | `fuel/READINGS.md` |
| B11 and B16 connected; supply channel follows ignition (0–4 counts off, 2577–2603 on) | 2026-10-24 | `fuel/READINGS.md`, "B11 and B16 connected" |
| DMM: Pico GND–chassis 21 mV; B11 11.93 V; C11 1.847 V; battery 12.28 V | 2026-10-24 14:56–14:58 | `fuel/READINGS.md` |
| Logger windows: fuel mean 893.08 (SD 1.05), supply mean 2596.42 (SD 1.49) | 2026-10-24 14:57 | `fuel/READINGS.md` |
| B16 lands on a breadboard ground rail jumpered to Pico AGND; both dividers share it | 2026-10-24 | `fuel/READINGS.md`, "owner confirms B16 ground topology" |
| No resolved ADC leakage drop at one measured condition: midpoint and GP26 both 0.701–0.706 V, inferred under ~2 µA | 2026-10-24 | `fuel/ADC_INTERFACE_SPEC.md` §4 |
| 1 µF on GP26/GP27 specified, **not yet fitted** | 2026-10-24 | `circuits.md`, "TWO 100 nF decisions" |
| Ignition now B11 → diode → resistor → opto LED, B16 return, collector → GP5, cap across output, emitter → PGND | 2026-10-26 | `circuits.md`, "AS BUILT 2026-10-26" |
| Ignition cell is a copy of keyless U13; R12 2.2k, D4 1N5819, C12 2.2 nF on the input side | 2026-10-16 / schematic | `circuits.md`, "The circuit is a copy of U13"; `keyless/hardware/hondaPico.kicad_sch` |
| GP5 shared-node back-feed quantified at 1.44 mA; 4.7 kΩ decided, **not fitted** | 2026-10-24 | `circuits.md`, "GP5 power-off protection" |
| SD wired and cleared: module 3V3 3.3 V, MISO 0 V, MOSI 0 V, no card, Pico powered | 2026-10-18 | `benchlink/picow-logger/SPEC.md` §5.2 |
| SD pin map and 12 MHz clock as built | 2026-10-18 | `SPEC.md` §5.2; `logger/firmware/accord-logger/logger_sd.cpp` |
| Buck 5 V branch: ~51 mA settled, maxima 88/96/101/89 mA, 72–80 mA after a drive | 2026-10-26 | `circuits.md`, "MEASURED 2026-10-26" |
| Divider ratios published in the card header from the same constants the code uses | current | `logger/firmware/accord-logger/accord-logger.ino`, `card_header.h` |
| Pi removed, clock-harness tap removed, ignition consolidated on B11 | 2026-10-29 | Owner statement, **reported** |
| No capacitor at the SD module | 2026-10-29 | Owner statement, **reported** |
| Three capacitors, eight diodes, thirteen resistors on the build | 2026-10-29 | Owner count, **reported** |
| Both ADC channels carry 1 kΩ, 1 µF and two 1N5819; no input-side opto capacitor | 2026-10-29 | **Inferred** from the counts above matching prediction exactly, corroborated for the 1 kΩ by the Oct 24 midpoint-vs-GP26 reading |
| Capacitor values: 100 nF opto output, 1 µF per ADC channel | 2026-10-29 | Owner statement, **reported** |
| All eight diodes are 1N5819 | 2026-10-29 | Owner statement, **reported**; corroborated by the inventory holding 100x 1N5819 and no BAT54 |
| Tap-end fuses and the ignition feed's inline fuse are in place | 2026-10-29 | Owner statement, **reported**; ratings not stated |
| Opto series resistor 2.2k | 2026-10-29 | Owner **measurement** |

Public artifacts in this repository that already carry part of this record:
[`logger/hardware/REV_A_CONTEXT.md`](../REV_A_CONTEXT.md),
[`logger/hardware/README.md`](../README.md),
[`logger/hardware/power/DESIGN.md`](../power/DESIGN.md) §6 and
[`logger/protocols/CARD_FORMAT.md`](../../protocols/CARD_FORMAT.md).

---

## 9. What this record does not establish

- No bench access, measurement, flash, wiring change or purchase occurred.
- No off-state current, inrush or transient figure exists for this build.
- No fuel-quantity model, calibration or acceptance is claimed, and the 1 %
  agreement in §4 is a sanity check, not a calibration.
- The installation is **not** galvanically isolated, whatever the presence of an
  optocoupler suggests.
- Nothing here authorizes fabrication, ordering, deployment or a database write.
