# LRA-11 — B2 off-state isolation: recommendation

> **Integration status, October 29:** this original LRA-11 return is retained
> as a conditional design reference, not an accepted implementation. The
> [manager follow-up](../../../coordination/reviews/LAYOUT_READINESS_2026-10-29.md)
> closes the datasheet temperature question and controls the limitations below,
> including BAD/enable behavior, finite leakage, timing and footprint verification.
> This supersedes “nothing integrated” below; the schematic still contains X1.
> Integration by Codex `pcb-manager`, session
> `01a18447-07c2-7bb3-8318-9b276cfdb3b8`
> (`codex resume 01a18447-07c2-7bb3-8318-9b276cfdb3b8`).

Prepared October 29, 2026 by Claude `analog-isolation`.

**Session ID: unavailable.** This session runs as a subagent
(`CLAUDE_CODE_CHILD_SESSION=1`) and the only identifier the harness exposes is
`CLAUDE_CODE_SESSION_ID=630dea87-5e4d-4bad-a1ff-d41b3a5f509b`, which belongs to
the dispatching manager, not to me. Per
`logger/coordination/AGENT_ATTRIBUTION.md` I state this rather than borrow or
invent one, and **no resume bookmark can be given for this work**.

Task packet: [`coordination/handoffs/LRA-11_B2_OFFSTATE_ISOLATION.md`](../../../coordination/handoffs/LRA-11_B2_OFFSTATE_ISOLATION.md).
Arithmetic: [`check_b2_isolation.py`](check_b2_isolation.py) — 24 checks, all
passing, stdlib only.

**Nothing here is integrated, frozen, or authorization to purchase or to touch
hardware.** X1 stays a placeholder until the manager reviews this.

---

## Recommendation in one line

Put a **Broadcom ASSR-601JV** optically-isolated photo-MOSFET relay in series
with the B2 divider top leg, LED driven from the **switched B5 rail** through a
GPIO-gated low-side FET.

| | |
|---|---|
| Parked injection | **≤1 µA**, a specified maximum **over −40 to +105 °C**, quoted at 1000 V against the 4.669 V actually applied |
| Against budget | 8× inside the 8 µA cold allowance, 20× inside the 20 µA hot allowance |
| Back-feed | **Eliminated.** No conductive path of any kind from B2 to the 3V3 rail exists when the LED is dark |
| Withstand | 1500 V min BV<sub>DSS</sub>, 94× the 16 V charging fault, with no supply on the output side at all |
| Signal | 300 Ω max R<sub>ON</sub> → −0.54 % ratio shift, −16.3 mV on a 5 V pulse; no artefact within 100 µs |
| Enable cost | 10.3 mA nominal LED current, only while the board is awake |

---

## How this was narrowed

I screened optically-isolated solid-state relays (photoMOS) first, on the
manager's reasoning of October 29, which I checked and agree with: the LED-off
state is open **by construction**; the output has **no supply rail at all**, so
requirement 3 is vacuous rather than marginal — this is precisely what
disqualified the ADG5412F; and there are no contacts, so requirement 5's
dry-circuit problem does not arise rather than being met.

**Requirement 2 was the only hard one, and it is where most of the class
fails.** Nearly every photoMOS quotes its off-state leakage maximum from a
table headed "Ambient temperature: 25 °C" and publishes nothing at 85 °C. That
is the same defect as the ADG5412F's typical-only entry. Two parts were
screened out on exactly this and are recorded below. The ASSR-601JV passes
because Broadcom states its maxima **over recommended operating conditions**,
and its recommended operating temperature runs to +105 °C.

**Deviation from the manager's steer, stated plainly:** the steer said to skip
the packet's two non-switch directions and record them as deliberately unexplored.
It arrived after I had already worked them through, so recording them as
unexplored would be false. They are written up below. One of them — the clamp
topology — produced a result that changes how the off-state matrix should be
read, so discarding it would have lost something.

---

## The part

**Broadcom ASSR-601JV**, automotive R²Coupler photo-MOSFET relay, 1 Form A.
Datasheet: Broadcom *ASSR-601JV, ASSR-601JT* data sheet (300 mil SO-16),
read in full for this review. AEC-Q101 qualified; ESD HBM H2 (2–4 kV), CDM C4
(750–1000 V) per AEC-Q101-001/-005.

### Requirement 2 — the one that matters

The DC electrical specification table carries this header, verbatim:

> Unless otherwise stated, all minimum/maximum specifications are over
> recommended operating conditions. All typical values are at T<sub>A</sub> = 25 °C,
> I<sub>F</sub> = 10 mA.

and the row:

| Parameter | Symbol | Device | Min. | Typ. | Max. | Unit | Test Conditions |
|---|---|---|---|---|---|---|---|
| Output Leakage Current | I<sub>O(OFF)</sub> | ASSR-601JV | — | 0.3 | **1000** | nA | V<sub>O</sub> = 1000 V |

Recommended Operating Conditions give **T<sub>A</sub> = −40 to +105 °C** for the
JV variant.

Two things make this a real guarantee rather than a reading of mine:

1. The I<sub>O(OFF)</sub> row carries **no temperature override** in its test
   conditions. The row immediately above it — Output Withstand Voltage —
   *does*, stating "I<sub>O</sub> = 250 µA, **T<sub>A</sub> = 25 °C**". Broadcom
   marks the rows that are 25 °C-only, and this is not one of them, so the
   blanket "over recommended operating conditions" applies.
2. The qualification is consistent with it: note (b) records that "per
   AEC-Q101, device performance is demonstrated with high temperature reverse
   bias stress at 1200 V (80 % of rated voltage)".

So **1 µA maximum at 85 °C is specified, not argued.** Budget is 8 µA cold and
20 µA hot: 8× and 20× margin respectively, from the maximum, before taking any
credit for the fact that the maximum is quoted at **1000 V** while B2 parked
applies **4.669 V** — a 214× lower stress that is not claimed here.

### Requirement 3 — withstand 16 V with its own supply at 0 V

Vacuous in the strict sense, which is the point. The output is two
photovoltaically-driven MOSFETs; **there is no supply pin on the output side**,
so "supply at 0 V" is the device's only state whenever the LED is dark. The
relevant limit is BV<sub>DSS</sub> ≥ 1500 V min at I<sub>DSS</sub> = 250 µA,
with avalanche-rated MOSFETs and a continuous load-voltage rating of 1000 VDC.
Against a 16 V charging fault that is **94× margin**. U-06's unmeasured upper
pulse amplitude is comfortably covered and does not gate this.

### Requirement 4 — pass the VSS signal undistorted

- **R<sub>ON</sub> max 300 Ω** (at I<sub>O</sub> = 2 mA; 250 Ω at 10 mA). In the
  22 kΩ top leg the divider ratio goes 0.600000 → 0.596745, a **−0.54 % shift,
  −16.3 mV referred to a 5 V pulse at the junction**. The high level lands at
  2.98 V against an RP2040 V<sub>IH</sub> of about 2.0 V. §3.4's ≤25 Ω / ≤100 Ω
  top-leg limits are C11/B11 limits and do not apply here.
  Our signal current is **90.9 µA**, well inside the ±10 mA recommended load
  window but an order below the 2 mA at which R<sub>ON</sub> is specified; the
  300 Ω max is used as an upper bound, which is conservative for a channel in
  the linear region.
- **Closed-state timing.** Once closed the device is a resistor. Against a
  generous 100 pF of node and track capacitance the added time constant is
  **30 ns**, 0.03 % of the 100 µs `GLITCH_US` window. The 4 ms turn-on and
  0.5 ms turn-off are transitions of the *switch*, which happen at power-up and
  at shutdown when no VSS edge is being counted — they are not artefacts on the
  passed waveform.
- **Open-state coupling**, the one place this part is weaker than the fallback.
  C<sub>OUT</sub> is 190 pF typ. In the parked case this is irrelevant: B2 is
  held at a steady 4.669 V by an always-on pull-up and there is no AC at all.
  It only matters in criterion B's "board off, key at II" case, where VSS is
  pulsing with the switch open: 190 pF × 5 V × 2 edges × 91 Hz = **0.173 µA
  average**, which on the measured dead rail is **1.4 mV** against criterion B's
  0.3 V limit.

### Requirement 5 — low-level switching

Not applicable, and that is a result rather than a dodge. There are no
contacts, so there is no wetting current, no contact film and no minimum
permissible load. The measured 140.8 µA at 1.042 V is conducted by a MOSFET
channel. The acceptance row reads "dry-circuit rating cited **if contacts are
used**"; none are.

### Package and footprint for X1

| | |
|---|---|
| Package | 300 mil SO-16, **12 leads populated** |
| Body | 10.363 × 7.493 mm (+0.254 / −0.127) |
| Height | 2.160 mm max, 0.203 mm standoff |
| Lead pitch | 1.270 mm; lead width 0.457 mm BSC |
| Recommended land pattern | 11.634 mm span × 10.363 mm |
| Creepage | ≥8 mm input-to-output, >5 mm between drain pins |

Pinout: **4 = AN** (anode), **5 = CA** (cathode), **15, 16 = D1**,
**9, 10 = D2** (each pair internally connected). Pins 1, 2, 6, 7, 8 are NC.
**Pin 3 is "do not connect — internally connected to pin 5."**
**Pins 11–14 do not exist**; the gap carries the drain-to-drain creepage.

**For LRA-08:** this is *not* a stock `SOIC-16W_7.5x10.3mm_P1.27mm`. That
footprint places pads at 11–14 where there are no leads, which both wastes the
creepage gap and leaves four unconnected pads under a part whose datasheet asks
for clearance there. Derive a 12-pad variant from the recommended land pattern
above. Orientation is free — the part is symmetric about its long axis and D1/D2
are interchangeable (the output is a bidirectional back-to-back pair).

---

## Enable path, rail, and shutdown ordering

```
B5 ──[ R_ISO 330R ]── AN (pin 4)
                      CA (pin 5) ── D  Q_ISO (logic-level N-ch)
                                    S ── PGND
         GP<ISO_EN> ──[ 1k ]──────── G
                                    G ──[ 100k ]── PGND
```

### The rail is B5, not A5 — correcting the steer

The manager's note suggested "a few mA from A5 or switched 3V3". **A5 would
break the design.** A5 is the always-on supervisor rail; an LED fed from A5 is
lit whenever A5 is up, which is always, so the switch would be closed while the
car is parked and B2 would still be connected. That is the condition this task
exists to remove. The LED must come from a rail that **dies when the board is
off**.

Switched 3V3 works electrically but is the Pico's own 3V3(OUT); 10 mA is a
meaningful bite out of it, and the headroom over V<sub>F(max)</sub> = 1.85 V is
thin. **B5 is the right rail**: 5 V gives comfortable headroom, and B5 collapsing
is exactly the event that should open the switch.

### R_ISO = 330 Ω

Holds I<sub>F</sub> inside the 7–30 mA recommended window across the V<sub>F</sub>
spread (1.25–1.85 V at 10 mA) and ±5 % on B5:

| Case | I<sub>F</sub> |
|---|---|
| B5 −5 %, V<sub>F</sub> max | **8.64 mA** (floor is 7 mA) |
| Nominal | **10.30 mA** — matches the I<sub>F</sub> the switching specs are characterised at |
| B5 +5 %, V<sub>F</sub> min | **11.97 mA** (ceiling is 30 mA) |

Resistor dissipation <48 mW. Cost on the ~51 mA awake branch baseline: **+20 %**,
drawn only while recording.

### Behaviour in each state

| State | Behaviour | Requirement |
|---|---|---|
| **No power applied** | B5 = 0 V, so there is no LED current whatever the gate does. Output open **by construction**. The 100 k is a pulldown on the *driver*, not the isolation mechanism — the open state does not depend on it | 1 |
| **Supervisor BAD** | BAD drops B5, LED goes dark, output opens within T<sub>OFF</sub> ≤ 0.5 ms. **No software step** | 7 |
| **Normal shutdown** | Firmware drives ISO_EN low, waits **t_iso = 5 ms** (10× the 0.5 ms T<sub>OFF</sub> max), *then* releases HOLD. Isolate-then-release | 6 |
| **Startup** | After B5 and the Pico are up, firmware asserts ISO_EN and waits **20 ms** (5× the 4.0 ms T<sub>ON</sub> max) before trusting VSS edges, so no partially-conducting edge is counted | 4 |
| **Unplanned power loss** | B5 collapses, LED goes dark, output opens. The board **cannot** be left connected — the failure mode that rejected the latching relay | packet §Dead ends |

**Dependency to confirm (not mine to close):** this rests on *B5 being the rail
the supervisor kills on BAD*. §3.1 lists "A5 supervisor BAD" as an entry
condition to the board-off state, which implies it, but I did not verify it
against the power design — that is the electrical lead's or the manager's call.
**If BAD does not drop B5**, add a second series N-FET in the LED path gated by
the A5-domain PGOOD/not-BAD signal. One extra part, same topology, and the
requirement is still met in hardware.

---

## Fallback: Panasonic AQY221N2S

Panasonic PhotoMOS, 1 Form A, SOP 4-pin, datasheet ASCTB156E.

Better on almost every axis **except the one that decides the task**:

| | AQY221N2S | ASSR-601JV |
|---|---|---|
| Off-state leakage max | **10 nA** (typ 0.01 nA) | 1000 nA |
| Specified at | **T<sub>A</sub> = 25 °C only** | **over −40 to +105 °C** |
| R<sub>ON</sub> max | 12.5 Ω (−0.02 % ratio) | 300 Ω (−0.54 %) |
| C<sub>OUT</sub> max | 1.5 pF | 190 pF typ |
| T<sub>OFF</sub> max | 0.2 ms | 0.5 ms |
| Load voltage | 40 V (2.5× the fault) | 1500 V (94×) |
| LED current | ~5 mA | ~10 mA |
| Package | 4.3 × 4.4 × 2.1 mm SOP-4 | 10.4 × 7.5 mm SO-16 |
| Automotive | **"not designed for automotive use"** (datasheet, verbatim) | AEC-Q101 |

**Why it is the fallback and not the recommendation.** Its 10 nA maximum comes
from a table headed "Ambient temperature: 25 °C 77 °F", and the datasheet
publishes *no* leakage-versus-temperature curve — graph 10 is leakage versus
load voltage, also at 25 °C. The hot case can only be argued: junction leakage
doubling every 8–10 °C over a 60 °C rise gives 0.64–1.81 µA, which is 11–31×
inside the 20 µA hot budget, and it would take a **2000×** rise to breach it. That
is a strong argument, but requirement 2 asks for a specification, and this is
not one.

Its datasheet also states, verbatim: *"These products are not designed for
automotive use. If you are considering to use these products for automotive
applications, please contact your local Panasonic Corporation technical
representative."*

**Use it if** the ASSR-601JV's availability does not hold up (see open items),
or if the owner would rather take a bench measurement than pay for the
automotive part. If chosen, the hot leakage must be measured, not assumed.

---

## Rejected

### Signal relay, non-latching, gold-clad contacts — Omron G6K-2F-Y DC5

The packet asked for a fresh look now that the coil cost falls on one branch
instead of five. It was looked at, and it **functionally passes**: minimum
permissible load 10 µA at 10 mV DC against our measured 140.8 µA at 1.042 V is
14× on current and 100× on voltage, a genuine dry-circuit margin; insulation
resistance ≥1000 MΩ at 500 V DC converts to ≤4.7 nA at 4.669 V.

It is nevertheless **strictly dominated**:

1. **Temperature.** Distributor data gives the G6K-2F-Y a maximum ambient of
   **70 °C**. Criterion A's hot spec point is **85 °C**. The part is outside its
   rating at the temperature the requirement is written at. *(Distributor
   sourced, not Omron's own PDF — flagged as such.)*
2. **Its leakage guarantee is no better qualified than the fallback's.** The
   insulation-resistance minimum is an *initial*, room-temperature, 500 V
   figure, and Omron's own note on the minimum permissible load says it "may
   vary depending on the switching frequency and operating environment". That
   is the same unqualified-number defect that killed the ADG5412F.
3. **Enable cost is 2.05× the primary's** — 21.1 mA coil at 5 V versus 10.3 mA
   LED, i.e. +41 % on the awake branch baseline rather than +20 %.
4. Contact bounce at energize, a mechanical wear-out mechanism, and thin gold
   cladding on an unenclosed board in a vibrating, unsealed automotive
   environment where sulfur and silicone contamination of low-level contacts is
   a known failure mode.
5. It needs a coil driver and a flyback diode anyway, so it is not simpler.

Not wrong — just beaten on every axis by a part that costs a few dollars more.

### Raising the divider impedance

Rejected, and **not** useful as an adjunct either.

It fails on structure before it fails on numbers: there is nothing to open, so
specification items 1, 6 and 7 are unmet outright, and the acceptance criterion
asks for the back-feed to be **eliminated, not merely reduced** — scaling can
only ever reduce it.

The numbers are also worse than the packet's estimate. Solving the divider with
the clamp still conducting, the dead rail modelled from the measurement
(8.09 kΩ equivalent) and the Schottky drop extrapolated from U-07's single
point — a model that **reproduces the measured state exactly at 1×**
(140.81 µA, 1.042 V, 109.23 µA):

| Divider | Injection | Still back-feeding |
|---|---|---|
| 1× (as fitted) | 140.81 µA | 109.23 µA |
| 10× | **19.69 µA** | 18.89 µA |
| 20× | 10.13 µA | 9.87 µA |
| 100× | 2.09 µA | 2.07 µA |

**The packet's "~10× gets to roughly 14 µA" is optimistic; it is 19.7 µA**,
which fails the 8 µA cold budget and sits on the 20 µA hot limit. Even 20× still
fails cold. Only 100× — 2.2 M / 3.3 M — buys the budget, and it puts a
**1.32 MΩ** Thevenin source on the GP2 node: with 30 pF of node capacitance the
time constant is **39.6 µs**, 40 % of the whole `GLITCH_US` window, on a
pulse input sharing a harness with the impulsive ignition noise §2 already
records on a neighbouring branch. U-08 also leaves B2's *driven* source
impedance unmeasured, so there is no evidence the PCM output could hold a
megohm node cleanly.

Once a series switch is fitted the parked current is ≤1 µA regardless of the
divider, so raising it buys nothing and costs noise immunity. Leave the
22 k / 33 k alone.

### Changing the clamp topology — and why it changes the off-state matrix

**Rejected, and this is the result worth keeping.**

The intuition in the packet is that "a clamp that does not reference the
switched 3V3 rail removes the mechanism rather than starving it." It does not,
because **the clamp that matters is inside the RP2040 and cannot be removed.**

Remove the external 1N5819 and change nothing else, and the parked divider is
3757 + 22 k + 33 k across 4.669 V = 79.5 µA, putting the GP2 node at
**2.622 V**. The RP2040's absolute-maximum GPIO limit of IOVDD + 0.3 V is the
standard statement of a pin-to-rail protection diode, and 2.622 V against a 3V3
rail at 0 V forward-biases it hard. Solving again with a silicon drop in place
of the Schottky, the back-feed **persists at a comparable current and a higher
rail voltage** — worse than the 109.2 µA at 0.883 V measured today, not better.

There is no escape by choosing a different clamp value. To hold the node below
the internal diode's onset while the rail is dead you would have to clamp it
under roughly 0.3 V absolute, which is below the RP2040's V<sub>IL</sub> and
destroys the logic high. The clamp reference and the logic reference are the
same rail; one clamp cannot satisfy both. Re-referencing the clamp to an
always-on rail merely energizes a different rail.

**The generalisation, which belongs in §6's off-state matrix:** the mechanism
is not the clamp. It is *any DC path from an energized source to a pin whose
protection diode references a dead rail*. Only breaking the DC path upstream
fixes it. This independently re-derives §3.2's "upstream of the divider top"
rule from the measurement rather than from assertion, and it means rows 1–5 of
the matrix cannot be closed by clamp changes on any branch.

*Honest limit:* the RP2040 internal diode is taken from the datasheet's
absolute-maximum pin limit, not from a measurement. It is cheap to confirm on
the bench by lifting the external clamp and re-reading the two nodes. The
conclusion does not depend on the diode's exact characteristics — 2.622 V is
far above any silicon onset.

### Screened out on requirement 2, recorded so they are not re-screened

- **Littelfuse/IXYS CPC1017N** (60 V, SOP-4, 1 mA LED — attractive on enable
  cost). Off-state leakage **1 µA max at V<sub>L</sub> = 60 V** but from a table
  headed "Electrical Characteristics @ 25 °C", with no hot figure. Starting from
  a 1 µA max at 25 °C, routine temperature scaling lands outside the 20 µA hot
  budget, so unlike the AQY221N2S it cannot even be argued home. Rejected.
- **Discrete series MOSFET.** N-channel needs a gate above the signal's highest
  level plus V<sub>GS(th)</sub>, which a 5 V rail cannot provide for a 4.67 V
  signal — **the same charge-pump requirement that disqualified the ADG5412F's
  8 V minimum supply**, not an incidental limitation. P-channel with its source
  at B2 does block the parked direction and needs no extra rail, but when the
  PCM pulls B2 low the source falls, V<sub>GS</sub> collapses and the **body
  diode becomes the signal path**, offsetting the low level by ~0.6 V and making
  it depend on the FET's V<sub>th</sub> and on U-06's unmeasured amplitude.
  Small-signal I<sub>DSS</sub> maxima are also typically 25 °C-only. Rejected.

---

## Open items

1. **Availability of the ASSR-601JV is not confirmed.** Distributor data is
   contradictory: one aggregator reports the lifecycle as Active, one
   distributor lists it as obsolete, and indicative pricing is around
   USD 6.25 at unit quantity. **This needs an authorized-distributor check
   before anything is committed.** It is the single reason the fallback is
   specified in as much detail as it is.
2. **Does supervisor BAD drop B5?** The fail-open-in-hardware claim rests on it.
   See the enable section for the one-part contingency if it does not.
3. **R<sub>ON</sub> at 91 µA** is below the 2 mA the 300 Ω maximum is specified
   at. Used as an upper bound, which is conservative, but not a specified point.
4. **The G6K's 70 °C ceiling is distributor-sourced**, not from Omron's own
   datasheet. It is a rejection argument, not a load-bearing design number.
5. **The RP2040 internal pin diode** is inferred from the absolute-maximum
   rating, not measured. See the clamp section.

None of these block LRA-08 from placing X1: the package and land pattern are
fixed by the primary, and the fallback is a strictly smaller part that fits
inside the same keep-out.

---

> **Required agent attribution:** Follow `logger/coordination/AGENT_ATTRIBUTION.md`
> relative to this repository root. Use your own tool, role and verified current
> session ID for Git author and committer (`<Tool> <role> [<short-id>]`), using
> per-command settings. End commits with `Agent-Session: <role>` and your full
> tool-specific session-ID trailer. Identify yourself and your resume command in
> coordination documents and dated updates. If an ID is unavailable, state that
> explicitly; never invent or borrow one.
