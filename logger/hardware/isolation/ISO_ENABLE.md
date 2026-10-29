# B2 isolation — the implemented circuit and its enable analysis

Prepared October 29, 2026 by Claude Code `logger-electrical`, session
`b690946d-3a88-4626-8e7b-b321126a3d16` (LRA-12).
Resume: `claude --resume b690946d-3a88-4626-8e7b-b321126a3d16`.
Session ID read from this session's harness-assigned working paths; this tool
exposes no second identifier to cross-check it against.

This is the implementation of [B2_ISOLATION.md](B2_ISOLATION.md), which stays
as the original LRA-11 return and keeps its own authorship. That return
selected the part and was integrated as a conditional design reference. The
[manager follow-up](../../../coordination/reviews/LAYOUT_READINESS_2026-10-29.md)
set four qualifications on using it, and this document is the answer to those
four, plus the footprint. The circuit itself is in
`../kicad/accord-logger.kicad_sch`; the decisions sit in
[../power/LAYOUT_CLOSURE.md](../power/LAYOUT_CLOSURE.md) §4.

**Nothing here is ordered, built or measured.** Three of the four
qualifications close on paper; the fourth is bounded and handed to bring-up
with the measurement named.

---

## 1. The four qualifications, and what each turned into

| Manager qualification | Outcome |
|---|---|
| **BAD does not necessarily remove B5.** The original design gates only QH; QI can hold power with ignition present. Complete the PGOOD-controlled series driver or an equivalent, rather than silently weakening requirement 7 | **Closed in hardware.** A second series channel, gated from A5-domain PGOOD, so supervisor BAD opens the branch with no software step whatever QI is doing. §2 |
| **The switch has finite leakage.** "No conductive path of any kind" and "eliminated" are overstatements. Bound the residual current and the dead-rail voltage | **Corrected.** Those words are not used. The bound is 1 µA maximum over −40 to +105 °C, carried in the ledger as 1.0/1.0 µA against 8/20 µA for all five branches. §4 |
| **The timing arithmetic is conditional.** The 4 ms turn-on maximum uses 10 mA LED drive and a specified test load; the proposed 330 Ω can supply less. Do not promote 5/20 ms into guarantees | **Half closed, half bounded.** R_ISO changed to 270 Ω so the worst-case LED current is *at* the specified 10 mA point, which makes the 4 ms maximum apply. The load condition still differs and stays a bring-up measurement. §3 |
| **Check the package drawing directly.** The return has no footprint; verify pad geometry, numbering, omitted leads and height. Pin 3 must stay externally unconnected | **Closed.** A 12-pad footprint derived from the manufacturer land pattern, with the pin-3 rule asserted in `check_capture.py`. §5 |

---

## 2. The enable circuit

```text
B5 -- R_ISO 270R/1%/0.25W -- AN (pin 4)
                             CA (pin 5) -- QISO_PG drain (3)
                                           QISO_PG source (2) -- ISO_MID
PGOOD -- R_ISOPG 1k -- QISO_PG gate (1)
                       gate -- R_ISOPG_PD 100k -- PGND

                                           ISO_MID -- QISO_EN drain (3)
                                                      QISO_EN source (2) -- PGND
GP7 (ISO_EN) -- R_ISOEN 1k -- QISO_EN gate (1)
                              gate -- R_ISOEN_PD 100k -- PGND

QISO_PG, QISO_EN = Nexperia BSS138P, SOT-23: gate 1, source 2, drain 3
```

Two channels in series. **Both must conduct for LED current to flow**, so
either one off leaves the relay open. `check_capture.py` asserts the series
topology by net identity — `ISO_MID` reaches exactly the two transistors and
`ISO_LED_K` exactly the relay cathode and the permission channel — because a
parallel miswiring would look identical in a parts list.

### Why two channels and not one

The LRA-11 return's fail-open argument rested on *"B5 being the rail the
supervisor kills on BAD"*, and flagged it as a dependency it could not close.
The dependency does not hold, and the manager said so first: **the original
design gates only QH.** Tracing it, BAD → BASE_RESET and ARM_RESET → the latch
disarms → ARM falls → QS opens → QH can no longer sink the QP gate → QP opens
→ VIN_SW falls → B5 decays. That chain works **only with raw ignition
absent**. With ignition present QI sinks the gate directly, QP stays on, B5
stays up, and an LED fed from B5 alone would keep the branch connected through
a BAD event.

So the rail cannot carry requirement 7 and PGOOD can, which is exactly the
one-extra-part contingency the return itself named. The part sits in the LED
path, in series, not in the signal path, so it adds nothing to the
measurement.

### Why PGOOD can drive a gate directly

TPS3839's RESET output is **push-pull**, not open drain, and sources at least
V<sub>DD</sub> − 0.4 V at 2 mA for V<sub>DD</sub> ≥ 3.3 V. Against the
~50 µA the 1 k / 100 k gate divider draws that is four decades of margin, and
the gate sees `VOH × 100/101` — about 4.41 V at the 4.89 V A5 minimum.
[TI TPS3839, SBVS193D](https://www.ti.com/lit/ds/symlink/tps3839.pdf).

Falling propagation delay is **20 µs typical with no maximum** in that table,
so an arbitrarily fast A5 collapse is not covered by a worst-case bound. That
is a limit of the supervisor, not of this circuit, and it is the same limit
the cutoff logic already lives with.

### Why B5 and not A5 for the LED

Restating the original return's correction because it is the whole point of
the task: **A5 would break the design.** A5 is always on, so an LED fed from
it would be lit while the car is parked and B2 would still be connected. The
LED has to come from a rail that dies when the board is off.

### State table

| State | What happens | By |
|---|---|---|
| No power applied | B5 = 0, so no LED current whatever any gate does. Open **by construction** — the 100 k pulldowns are on the driver, not the isolation mechanism | hardware |
| Supervisor BAD | PGOOD falls, permission channel opens, output opens within T<sub>OFF</sub> ≤ 0.5 ms | hardware, **no software step** |
| Pico 3V3 absent or in reset, B5 present | GP7 floats; R_ISOEN_PD holds the enable channel off | hardware |
| USB only, A5 and B5 absent | no LED current; PGOOD is absent too | hardware |
| Startup | after B5 and the Pico are up: assert ISO_EN, wait **20 ms**, then trust VSS edges | firmware |
| Normal shutdown | ISO_EN low, wait **t_iso = 5 ms**, **then** release HOLD | firmware |
| Unplanned rail collapse | B5 falls, LED goes dark, output opens | hardware |
| EXPIRED with HOLD stuck | QS opens, power is removed, B5 falls, output opens | hardware |

**The hardware is safe before that firmware exists.** Every default is open:
with no firmware at all, GP7 never asserts, the enable channel never conducts
and the relay never closes — the branch is simply isolated and the VSS channel
reads nothing. There is no state in which absent or incorrect firmware leaves
B2 connected while the board is off.

---

## 3. LED drive and timing

Broadcom ASSR-601Jx-DS105, June 17 2024: I<sub>F(ON)</sub> recommended
7–30 mA; V<sub>F</sub> 1.25 / 1.55 / **1.85 V** at I<sub>F</sub> = 10 mA;
T<sub>ON</sub> ≤ **4.0 ms at I<sub>F</sub> = 10 mA** and ≤ 1.0 ms at 30 mA,
both into V<sub>DD</sub> = 40 V and R<sub>LOAD</sub> = 20 kΩ; T<sub>OFF</sub>
≤ **0.5 ms** at the same load; absolute maximum I<sub>F(avg)</sub> 30 mA and
reverse input voltage 6 V.

### R_ISO = 270 Ω, and why the 330 Ω of the return is wrong

The turn-on maximum is specified **at** 10 mA. 330 Ω puts the worst-case LED
current at 8.64 mA, *below* that point, which leaves T<sub>ON</sub>
unspecified precisely where the requirement needs a number — the manager's
third qualification. 270 Ω fixes it, allowing 5 Ω per switch channel at the
reduced gate drive rather than the 2 Ω specified at V<sub>GS</sub> = 5 V:

| Corner | I<sub>F</sub> |
|---|---:|
| B5 −5 %, V<sub>F</sub> max, R +1 % | **10.26 mA** — at or above the specified point |
| Nominal | 12.32 mA |
| B5 +5 %, V<sub>F</sub> min, R −1 % | 14.42 mA — inside the 30 mA ceiling |

Dissipation 57 mW against a 0.25 W part. Awake cost rises from about 10.3 mA
to 12.3 mA, roughly +24 % on the ~51 mA awake branch baseline, drawn only
while recording. The LED is never reverse-biased: its cathode is switched to
ground, never to a source, so the 6 V reverse limit is not approached.

### Delays, against the budget that has to absorb them

| | Value | Basis |
|---|---:|---|
| t_iso, isolate before releasing HOLD | 5 ms | 10 × the 0.5 ms turn-off maximum |
| t_settle, enable before trusting VSS edges | 20 ms | 5 × the 4.0 ms turn-on maximum, which now applies at the worst-case LED current |

Both fit the existing shutdown budget with room to spare:

- The release boundary allows 1800 → 1801 s. 5 ms of isolation consumes
  **0.5 %** of it, leaving 995 ms. The ordering costs nothing in the deadline.
- The 20 ms enable wait happens **after** HOLD is already asserted, so it does
  not enter the ≤900 ms retention path at all.

**Still conditional, and named as a bring-up measurement rather than closed:**
the turn-on maximum is specified into a 20 kΩ test load and this branch
presents 22 k + 33 k = 55 kΩ, so the figure is used outside its stated load
condition. Scope the output against a VSS pulse train at both temperature
extremes and confirm the first edge is clean after the 20 ms wait. Neither
5 ms nor 20 ms is a guarantee.

---

## 4. Leakage and signal error, bounded rather than eliminated

| | Value | Condition |
|---|---|---|
| Off-state output leakage | **1000 nA maximum** | V<sub>O</sub> = 1000 V, over recommended operating conditions (−40 to +105 °C for the JV), device off with V<sub>F</sub> ≤ 0.4 V |
| Applied in this circuit | 4.669 V | the owner's open-circuit measurement |
| Against the branch allocation | 1.0 / 1.0 µA | of 8 / 20 µA reserved for all five branches |
| Open-state coupling | 0.173 µA average | 190 pF **typical** × 5 V × 2 edges × 91 Hz; no maximum is published |
| Output withstand | ≥1500 V at 25 °C | against a 16 V charging fault |
| Continuous load voltage | 1000 V DC | the rating to use for an operating-range argument |

The leakage row carries no temperature override, unlike the withstand row
immediately above it in the same table, which states T<sub>A</sub> = 25 °C.
That is what makes 1 µA a specification over the range rather than an
extrapolation. The 1000 V at which it is quoted is 214× the applied voltage;
that is noted and **not** claimed as margin.

Signal error: R<sub>ON</sub> ≤ 300 Ω (at I<sub>O</sub> = 2 mA) in the 22 kΩ
top leg moves the divider ratio 0.600000 → 0.596745, a **−0.54 % shift,
−16.3 mV** referred to a 5 V pulse, leaving the high level at 2.98 V against
an RP2040 V<sub>IH</sub> of about 2.0 V. The signal current is 90.4 µA, two
decades below the current R<sub>ON</sub> is specified at, so 300 Ω is used as
a conservative upper bound rather than as a specified point. Temperature drift
of that resistance is the part calibration cannot remove; it is a bring-up
measurement, and at 0.54 % of a *digital* threshold rather than an analog
reading it has three decades of headroom before it matters.

B2 is a digital pulse input, so the ≤25 Ω and ≤100 Ω top-leg limits of
`../as-built/REV_A_INTERFACES.md` §3.4 belong to C11 and B11 and do not apply
here — and because those two branches take no series element at all, the
card-header calibration question of its §8.2 does not arise.

---

## 5. The footprint, verified from the drawing

`../kicad/accord-logger.pretty/ASSR-601Jx_SO-16-12Lead_11.634x10.363mm_P1.27mm.kicad_mod`

Read from the datasheet's own "Package Outline Drawings (SO-16)" and "Pin
Description", not from a summary:

| | |
|---|---|
| Pads | **12**, numbered 1–10, 15, 16. **Pins 11–14 do not exist** |
| Pitch | 1.270 mm |
| Pad size | 2.871 × 0.65 mm (land-pattern span 11.634 mm minus centre spacing 8.763 mm; 0.635 mm is the stated minimum width) |
| Pad centres | ±4.3815 mm, from the 8.763 mm centre spacing |
| Body | 10.363 × 7.493 mm, height 2.160 mm max, standoff 0.203 mm |
| Lead width | 0.457 mm BSC |
| Pin functions | 4 AN, 5 CA, 9 and 10 D2 (internally paired), 15 and 16 D1 (internally paired), 1/2/6/7/8 NC, **3 "do not connect — internally connected to pin 5"** |

Three things a layout reader needs:

1. **Pin 3 is left unconnected**, and `check_capture.py` asserts it. It is
   internally tied to the LED cathode, so connecting it would short the
   cathode to whatever it reached.
2. **The pin 11–14 gap is marked on `User.9` as keep-clear.** Neither creepage
   figure is load-bearing at these voltages — this installation is not
   galvanically isolated and the drains see under 5 V — but the gap costs
   nothing to respect and the datasheet asks for it.
3. **Orientation is free.** The output is a back-to-back avalanche MOSFET
   pair, so D1 and D2 are interchangeable and the part is symmetric about its
   long axis. The LED is not: pin 4 anode, pin 5 cathode.

Courtyard 12.13 × 10.04 mm, 121.8 mm², measured by `../kicad/fp_area.py`. The
documented fallback AQY221N2S is a 4.3 × 4.4 mm SOP-4, strictly smaller, so it
fits inside the same keepout if availability forces the change.

---

## 6. What is still open

| Item | Class | What closes it |
|---|---|---|
| ASSR-601JV availability | **order gate** | An authorized-distributor check. Distributor lifecycle data is contradictory; indicative price about USD 6.25 at unit quantity. The fallback AQY221N2S is specified in the original return and fits the same keepout; if chosen, its hot leakage must be measured because its 10 nA maximum is 25 °C only |
| T<sub>ON</sub> into 55 kΩ rather than the specified 20 kΩ | bring-up | Scope the output against a VSS pulse train, hot and cold, and confirm the first edge after the 20 ms wait |
| R<sub>ON</sub> at 90 µA and its temperature drift | bring-up | Measure; 300 Ω at 2 mA is used as an upper bound |
| Output capacitance maximum | bring-up | 190 pF is typical and no maximum exists; the 0.173 µA coupling figure inherits that |
| The 100 pF of node and track capacitance assumed in the closed-state settling | bring-up | Measure on the assembled board |
| ISO_EN sequencing | **firmware** | `logger_power.cpp` asserts ISO_EN after B5 and the Pico are up, waits 20 ms before trusting VSS edges, drives it low and waits 5 ms before releasing HOLD. The hardware is safe without it: every default is open |
| RP2040 internal pin diode | bring-up | Inferred from the absolute-maximum pin rating, not measured. Cheap to confirm by lifting the external clamp and re-reading the two nodes. The conclusion does not depend on its exact characteristics |

Run `python3 check_b2_isolation.py` for the original return's 24 arithmetic
checks, which still pass unchanged, and
`python3 ../power/check_layout_closure.py` for the LRA-12 enable corners,
timing and the netlist path audit.

> **Required agent attribution:** Follow `logger/coordination/AGENT_ATTRIBUTION.md`
> relative to this project root. Use your own tool, role and verified current
> session ID for Git author and committer identity (`<Tool> <role> [<short-id>]`),
> with per-command settings. End each new commit message with `Agent-Session: <role>`
> and your full tool-specific session-ID trailer. Identify yourself and your
> resume command in new coordination documents and dated updates. If your ID is
> unavailable, say so rather than inventing one.
