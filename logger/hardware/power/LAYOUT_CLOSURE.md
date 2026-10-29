# LRA-12 — electrical closure for layout

Prepared October 29, 2026 by Claude Code `logger-electrical`, session
`b690946d-3a88-4626-8e7b-b321126a3d16`.
Resume: `claude --resume b690946d-3a88-4626-8e7b-b321126a3d16`.
Session ID read from this session's harness-assigned working paths and
confirmed against its transcript file; this tool exposes no second identifier
to cross-check it against, so that is stated rather than implied.

Branch `task/LRA-12-b690946d`, from public `main` at
`5ffcb26958d2b7154b4d1417431fad22246cedd9`.
Packet: [LRA-12](../../../coordination/handoffs/LRA-12_LAYOUT_ELECTRICAL_CLOSURE.md).
Readiness review: [LAYOUT_READINESS_2026-10-29](../../../coordination/reviews/LAYOUT_READINESS_2026-10-29.md).

**Disposition: the electrical design is complete and routable. Nothing here is
frozen, ordered, fabricated, flashed or vehicle-approved.** Every one of the
eight LRA-06 placeholders now has a real circuit or a recorded, justified
bypass; every populated part carries a checked footprint; ERC is clean at
`--severity-all`; the board fits 80 × 120 mm with a 1.52× courtyard
allowance. What is still open is listed in
[LRA12_HANDOFF.md](../LRA12_HANDOFF.md), classified, and none of it is a
layout blocker.

---

## 1. What changed

| Was | Now | Where |
|---|---|---|
| X1 B2 isolation, no part | ASSR-601JV in the divider top leg, with a GPIO enable in series with a hardware PGOOD permission | §4 |
| X2–X5 four branches, under review | **Justified bypass**, on the ignition interlock plus the fitted series resistance, with a reachable-state table | §4 |
| X6 qualified IGN / QREPORT, no circuit | Captured component for component from `CUTOFF_MARGIN_REVIEW.md` §2 | §5 |
| X7 vehicle protection, no selection | 1.5KE20A entry clamp **plus** a second-stage clamp on the A5 regulator input; one declared excluded exposure | §3 |
| X8 independent cutoff, no circuit | Captured from `MAX_ON_CUTOFF.md`, including the QS permission switch and QMON sense | §5 |
| J1/J2 connector family not selected | Molex Mini-Fit Jr., the family already in service in this car | §6 |
| Q2 / R06-REV-2 opto LED return | Moved from the B16 cluster conductor to PGND | §6 |
| Q4 onboard ignition fuse | Dropped; the fuse belongs at the tap end | §6 |
| Q5 J4 "service UART" with NC pins | J4 is the RUN/GND reset pair only; USB CDC is the service console | §6 |
| Q6 where the cutoff interrupts HOLD | QS between SINK and the QH collector | §5 |
| QP IRF4905, hot leakage over its allocation | IPD50P04P4L-11 with the paired BZX55C10 gate clamp | §3 |
| CIN/COUT/CCLK/A5 caps unspecified | The LRA-02 selections, with their conditions carried | §5, §7 |
| C_SD "10–100 µF" | 47 µF, selected from the duty | §6 |
| RGS 100 k | 10 k, per the MAX_ON revision | §5 |

Deliberately **not** changed: the five divider ratios, the GPIO allocation
except for taking up the released GP7, the 1N5819 digital clamps, the SD rail,
the single B16 return, the LM2678 buck topology, the 1770/1800/1801 s policy,
the nominal 2048 s cutoff, and the 100/500 µA whole-system targets.

---

## 2. Design basis

`D-REUSE-02` and `D-POWER-03`: this board is the working keyless circuitry
plus the logger's documented input cells and SD wiring plus the existing
IGN-sense, power-hold and automatic-shutoff design. It is integration, not a
new power survey. The regulator, the TVS role, both bulk capacitors, the boost
capacitor, the inductor value, both Schottky positions, the connector family
and the test-point and reset-header pattern all come forward from a board
that runs in this car on a permanent 12 V feed through cranking.

Every change to an inherited block below names a concrete incompatibility, a
changed operating condition or a documented defect. There is no blanket
requalification: the LM2678 loop, the keyless clamp precedent and the fitted
divider ratios are carried as they are.

Two conditions genuinely changed, and they are where the engineering went:

1. **The always-on A5 supply is new.** Its regulator has a 30 V recommended
   input maximum, where everything keyless puts behind the same clamp is
   rated 40 V. §3.
2. **The shutdown addition creates a state keyless never has:** a board that
   has removed its own power while vehicle inputs may still be energized.
   §4.

---

## 3. X7 — the input voltage envelope

### 3.1 It is one chain, not five independent choices

This is the part of the task that looks like a menu and is not. Starting from
the parked-current requirement and working outwards:

1. The 100/500 µA parked target allocates **200 µA** to the switch. The
   inherited IRF4905 screens **25 µA at 25 °C and 250 µA at 150 °C** at
   V<sub>GS</sub> = 0 — a known component bound that cannot fit its own
   allocation, which `COMPONENT_MARGIN_CLOSURE.md` §3 already recorded.
2. The only P-channel candidate the record found with a **hot** zero-gate
   drain-current maximum is **IPD50P04P4L-11**: 1 µA at 25 °C and **70 µA at
   125 °C**, at V<sub>DS</sub> = −32 V. Nexperia PXP062-60QL and Diodes
   DMP6023LE were screened and rejected for having 25 °C-only entries.
3. That part is rated **−40 V V<sub>DS</sub>**. So the entry clamp has to hold
   the board below 40 V with real margin.
4. The inherited **1.5KE30A clamps at 41.4 V** at its 36.2 A pulse current.
   That is above 40 V, and it was already above the 40 V V<sub>CEO</sub> of QI
   and QH and above the LM2678's 40 V operating ceiling — `DESIGN.md` §4 says
   so in as many words: *"These drivers cannot be carried into the proposed
   41.4 V clamp envelope. Select higher-voltage drivers or a lower coordinated
   clamp."*
5. Of the two, the lower clamp is the smaller change. **1.5KE20A-E3/54** is
   selected: 17.1 V standoff, 19.0–21.0 V V<sub>BR</sub> at 1.0 mA, **27.7 V
   clamp at 54.2 A** for 10/1000 µs, 1.0 µA maximum leakage at standoff,
   1500 W peak pulse, 6.5 W steady on an infinite heatsink at T<sub>L</sub> =
   75 °C, V<sub>BR</sub> temperature coefficient **0.090 %/K**.
   [Vishay 1.5KE table and notes](https://www.vishay.com/docs/88301/15ke.pdf).
6. At 85 °C that clamp is `27.7 × (1 + 0.00090 × 60) = 29.20 V`. Every part
   behind it then has **10.8 V of margin** to its 40 V rating.

So the clamp change is forced by the switch change, which is forced by the
parked budget. It is a deliberate deviation from the in-service keyless part,
and the reason is that keyless has neither a 40 V-rated DPAK switch nor a
30 V always-on LDO.

### 3.2 The envelope table

Computed in `check_layout_closure.py` §1 against the 29.20 V hot clamp.

| Part | Node | Rating | Kind | Margin |
|---|---|---:|---|---:|
| QP IPD50P04P4L-11 | P12 / VIN_SW | 40 V | absolute V<sub>DS</sub> | 10.80 V |
| QI 2N3904 | SINK = P12 when off | 40 V | absolute V<sub>CEO</sub> | 10.80 V |
| QH 2N3904 | SINK = P12 when off | 40 V | absolute V<sub>CEO</sub> | 10.80 V |
| QS BSS138P | SINK | 60 V | absolute V<sub>DS</sub> | 30.80 V |
| UREG LM2678 | VIN_SW | 40 V | operating V<sub>IN</sub> (45 V absolute) | 10.80 V |
| CIN EEUFR1H101 | VIN_SW | 50 V | rated WV | 20.80 V |
| C0 | P12 | 63 V | rated WV | 33.80 V |
| DREV SB360 | BATT_F / P12 | 60 V | absolute V<sub>RRM</sub> | 30.80 V |
| C_AON GRM32ER71H475KA88L | P_AON | 50 V | rated WV | 20.80 V |

The tightest number in the group is not in that table: cold V<sub>BR</sub>
minimum is `19.0 × (1 − 0.00090 × 65) = 17.89 V` against a 16 V operating
ceiling, so there is **1.89 V** between the top of the operating envelope and
the cold onset of clamp conduction. Leakage at 16 V and −40 °C is below the
1.0 µA standoff figure, because cold reduces it, but that is reasoning rather
than a tabulated point.

Keeping QI and QH as 2N3904 is a consequence of this choice, not an oversight:
the lower clamp gives them 10.8 V of margin where the inherited clamp exceeded
their absolute rating. Their hot off-state leakage under these actual base
networks remains unspecified and stays in the ledger as an allocation.

### 3.3 The A5 regulator gets its own second stage

29.20 V clears every 40 V part but **not** the contract's ≤28 V protected-rail
requirement, which exists solely because of TPS709's 30 V recommended input
maximum. The gap between its 30 V recommended and 32 V absolute is explicitly
not treated as usable headroom, so two parts close it:

```text
P12 -- R_AON 330R/0.25W/1% -- P_AON -- UA5 IN (pin 1)
P_AON -- DZ_AON BZX55C22 cathode; anode -- PGND
P_AON -- C_AON 4.7uF/50V X7R -- PGND
```

- **Worst P_AON = 25.70 V.** BZX55C22 is 20.8 / 22 / **23.3 V** at
  I<sub>ZT</sub> = 5 mA; with its 0.12 %/K maximum coefficient the 85 °C worst
  is 24.98 V, plus 0.72 V of dynamic drop at the 18.0 mA the 29.20 V clamp
  pushes through 330 Ω, using the 55 Ω maximum dynamic resistance.
  **2.30 V inside the 28 V contract and 4.30 V inside TPS709's 30 V.**
- **Dissipation:** zener 0.420 W against its 0.5 W rating, series resistor
  0.106 W against 0.25 W. Both are steady-state figures, so no pulse-power
  curve is relied on.
- **It never conducts in normal operation.** Cold V<sub>Z</sub> minimum is
  19.18 V, above the 17.1 V sustained ceiling §3.4 sets.
- **Leakage is specified with a hot point**, which is why this family was
  chosen over a part with a 25 °C-only figure: I<sub>R</sub> < 0.1 µA at 25 °C
  and < 2 µA at 150 °C, at V<sub>R</sub> = 18 V. The 150 °C figure is used as
  a conservative screen for 85 °C.
  [Vishay BZX55](https://www.vishay.com/docs/85604/bzx55.pdf).
- **The series drop is 0.167 V** at the 0.5 mA worst awake A5 load. At a 6 V
  P12 that leaves 5.833 V, still 0.333 V above the 5.5 V that TPS70950's
  500 mV / 50 mA dropout maximum implies for a 5 V output — and dropout is not
  specified below 50 mA at all. The 6–28 V P_AON design envelope therefore
  survives as written at the regulator's actual requirement, with the floor
  167 mV lower than at P12.
- **Startup:** `330 Ω × 4.7 µF = 1.55 ms`, inside the 100 ms A5 validity
  budget.
- EN is left **open** to enable. Its absolute maximum is 7 V; it is never tied
  to a rail. Pin 4 NC is left unconnected.
  [TI TPS709-Q1, SLVSCE6D, Table 4-1 and §5](https://www.ti.com/lit/ds/symlink/tps709-q1.pdf).

**Consequence for acceptance: the ≤28 V protected-rail criterion is measured
at TP_PAON, not at P12.** P12's own envelope is the 40 V chain of §3.2.

### 3.4 Fuse coordination, and the one exposure that is declared excluded

The clamp-only front end cannot do everything, and this is where it stops.

- **Reverse battery** is covered by DREV, which also keeps the unidirectional
  clamp out of forward conduction and is what makes P12 nonnegative at the A5
  regulator, as that regulator requires.
- **Transient**, 10/1000 µs: 1500 W, 54.2 A, clamping to 27.7 V cold and
  29.20 V hot. Within the declared bench and charging envelope.
- **Sustained overvoltage is not survivable, and is declared excluded.** At
  the 1 A branch fuse rating the clamp would dissipate about **19 W against
  its 6.5 W rating**, and a cartridge fuse carrying its own rating does not
  clear quickly. **The declared sustained ceiling at P12 is 17.1 V**, the
  clamp standoff — which covers 12–16 V bench operation and a 14.8 V charging
  rail with 2.3 V to spare, and explicitly excludes a 24 V jump start with
  the board connected.

There is no clamp that both stands off 24 V and limits to 28 V: the
V<sub>C</sub>/V<sub>WM</sub> ratio of this family is about 1.6, so a 24 V
standoff implies a clamp near 41 V, which is the part we just rejected. The
alternatives, with what each costs, for the reviewer rather than for silent
adoption:

| Option | What it buys | What it costs |
|---|---|---|
| **(a) Declare the exposure excluded** — selected | Nothing new to design; the whole 40 V chain keeps 10.8 V of margin | The owner must not jump start with the board connected, and that has to be written down rather than assumed |
| (b) Series overvoltage cutoff: a P-FET with a comparator or a shunt-regulated gate clamp ahead of QP | Survives a sustained 24 V by disconnecting | New topology, new parts, new failure modes, and a second series switch in the main power path — well beyond "complete the existing design" |
| (c) Raise the clamp to the inherited 1.5KE30A and replace the downstream parts | Keeps the in-service clamp | QI/QH/QMON/QRESET to 60 V+ BJTs, and a QP of ≥45 V with a hot I<sub>DSS</sub> maximum — which LRA-02's own screening did not find. The parked budget would reopen |

Required owner input to close this properly, unchanged from
`INTERFACE_CONTRACT.md` §6: exact feed, source and harness impedance and
inductance, expected jump-start and crank behaviour, pulse
amplitude/duration/repetition/temperature, wire sizing and the fuse interrupt
and clearing curves. None of that is needed to lay the board out.

**F1 stays on the board** as the board's own branch protection, and the
specification still puts a fuse at the feed source. An onboard fuse cannot
protect the upstream harness, so both exist for different reasons; `DESIGN.md`
§5 already says the feed-source fuse is the one that protects the wire.

### 3.5 The ignition and sense entries

One clamp, on the one harness entry that is not a high-impedance divider.

- **B11 carries both** the supply ADC divider and the ignition opto LED
  through 2.2 kΩ, so it is the cluster line where a transient has something
  low-impedance to drive. **TVS_B11 = 1.5KE20A-E3/54**, the same part as the
  entry clamp, so one qualification covers both. It costs nothing parked: B11
  is ignition-switched and logged dead with the key out.
- **The five divider inputs need no clamp of their own.** Each presents
  7.5–22 kΩ of series resistance before anything sensitive, so a 100 V
  transient delivers 4.5 mA into a 1N5819 rated 25 A of forward surge, and
  the axial resistors' own pulse withstand is far above the arriving voltage.
  This is the real difference from keyless, which fits seven P6KE30A: those
  lines drive ULN2803 outputs and relay loads, not dividers.
- The owner's four **P6KE30A** are recorded as a possible substitute only if
  the 41.4 V clamp is first checked against RI and RLED pulse ratings. They
  are not selected: the 1.5KE20A is strictly better here and halves the part
  count across the two clamp positions.
- **RI stays 2.2 k / 0.25 W.** At the 17.1 V sustained ceiling its
  dissipation is 0.112 W. The 0.318 W figure that would have forced a 0.5 W
  position came from the superseded 28 V number.
- **RLED is the measured 2.2 k, specified 0.5 W** (D15). At 17.1 V it
  dissipates 0.108 W; the 0.792 W that disqualified the 1 k candidate also
  came from the 28 V number. The fitted part's wattage is not recorded, which
  is why the position is specified rather than assumed.

---

## 4. X1 and X2–X5 — isolation, and the four branches that do not get it

### 4.1 Reachable-state table

The record had discussed two different criteria as one.
`REV_A_INTERFACES.md` §3.1 separates them; this table says, for each state,
which criterion applies and what each branch does in it.

| State | How it is reached | B2 (VSS) | B1, C14, C11, B11 |
|---|---|---|---|
| **Parked, key out** | normal | Energized at 4.669 V open circuit from an always-on source through 3,757 Ω — **measured** | **Dead** — B1 and C11 measured 0 V, C14 and B11 logged dead (`D-OFFSTATE-01`) |
| Running | key on, board powered | energized, switch closed, divider reads it | energized, dividers read them |
| HOLD window after key off | normal shutdown | dead within one PCM power-down | dead |
| Supervisor BAD, ignition absent | fault | relay opens in hardware when B5 falls | dead |
| Supervisor BAD, ignition present | fault | **QI holds the board powered** — so the board is not off | energized, board powered |
| EXPIRED with HOLD stuck | fault | ignition is absent by definition, so B2 is still energized but the relay is open | dead |
| Pico reset while ignition on | normal | QI holds power; 3V3 stays up | energized, board powered |
| USB only, key at II | bench | 3V3 is alive from USB; B5 is dead so the relay is open | energized, 3V3 alive |
| **Board dead, key at II** | **needs an upstream power fault**: J1 open, F1 open, DREV or QP failed open | relay open, B2 blocked | **energized into a dead 3V3 rail** |

The last row is the only state in which criterion B bites, and the table is
the argument: **it requires both the key on and a power fault**, because
ignition present drives QI, QI sinks the QP gate, and the board powers up —
with no firmware, no HOLD and no qualification involved. That interlock is
checked structurally off the netlist in `check_layout_closure.py` §5.

B2 is the exception to all of it, which is why B2 alone gets a switch: it is
energized with the key out, so the interlock argument does not cover it and
the parked criterion fails on measurement rather than on inference.

### 4.2 B2: the ASSR-601JV, and the enable the manager required

Part, package and leakage come from the LRA-11 return and are unchanged.
Verified again here directly from
[Broadcom ASSR-601Jx-DS105, June 17 2024](https://docs.broadcom.com/doc/ASSR-601Jx-DS):
I<sub>O(OFF)</sub> **1000 nA maximum at V<sub>O</sub> = 1000 V**, under a table
header reading *"Unless otherwise stated, all minimum/maximum specifications
are over recommended operating conditions"*, with recommended operating
temperature **−40 to +105 °C** for the JV and no 25 °C override on that row —
unlike the withstand row immediately above it, which states
"T<sub>A</sub> = 25 °C" explicitly. 4.669 V is applied against a limit quoted
at 1000 V; that 214× lower stress is noted, not claimed.

Three things the manager's follow-up required, and what each turned into:

**(1) Complete the driver: GPIO enable plus hardware PGOOD permission.**

```text
B5 -- R_ISO 270R/1% -- AN (pin 4)
                       CA (pin 5) -- QISO_PG drain
                                     QISO_PG source -- ISO_MID
PGOOD -- 1k -- QISO_PG gate ; gate -- 100k -- PGND
                                     ISO_MID -- QISO_EN drain
                                                QISO_EN source -- PGND
GP7 (ISO_EN) -- 1k -- QISO_EN gate ; gate -- 100k -- PGND
```

Both channels must conduct for LED current to flow. The reason the second one
exists is the manager's own correction: **BAD does not necessarily remove
B5**, because the original design gates only QH and QI can hold power with
ignition present. A rail-only argument therefore cannot carry the
fail-open-on-BAD requirement, and PGOOD can, in hardware, with no software
step. TPS3839's output is **push-pull** and sources at least V<sub>DD</sub> −
0.4 V at 2 mA, against the 50 µA that gate divider draws, so it drives the
gate directly.
[TI TPS3839, SBVS193D](https://www.ti.com/lit/ds/symlink/tps3839.pdf).

Per-state behaviour, all of it in hardware unless marked:

| State | Behaviour |
|---|---|
| No power applied | B5 = 0, no LED current whatever any gate does. Open **by construction**; the 100 k pulldowns are on the driver, not the isolation mechanism |
| Supervisor BAD | PGOOD falls, the permission channel opens, output opens within T<sub>OFF</sub> ≤ 0.5 ms. **No software step** |
| Pico 3V3 absent or resetting, B5 present | GP7 floats, its 100 k pulldown holds the enable channel off |
| USB only, A5 and B5 absent | no LED current; also no PGOOD |
| Normal shutdown | *firmware*: ISO_EN low, wait t_iso = 5 ms, **then** release HOLD |
| Startup | *firmware*: after B5 and the Pico are up, assert ISO_EN and wait 20 ms before trusting VSS edges |
| Unplanned rail collapse | B5 falls, LED goes dark, output opens |

**(2) R_ISO is 270 Ω, not 330 Ω — a correction, with a reason.** The ASSR's
turn-on maximum is specified at two LED currents: **4.0 ms at I<sub>F</sub> =
10 mA** and 1.0 ms at 30 mA, into V<sub>DD</sub> = 40 V and
R<sub>LOAD</sub> = 20 kΩ. The original 330 Ω puts the worst-case LED current
at 8.64 mA — *below* the 10 mA the maximum is specified at, which would leave
turn-on an extrapolation exactly where the requirement needs a specification.
270 Ω moves the corners to:

| Corner | I<sub>F</sub> |
|---|---:|
| B5 −5 %, V<sub>F</sub> 1.85 V, two channels at 5 Ω each | **10.26 mA** |
| Nominal | 12.32 mA |
| B5 +5 %, V<sub>F</sub> 1.25 V | 14.42 mA |

All inside the 7–30 mA recommended window, and the low corner is now at or
above the specified point. Resistor dissipation 57 mW. The awake cost rises
from ~10.3 mA to 12.3 mA, about +24 % on the ~51 mA branch baseline, drawn
only while recording.

**(3) Timing against the shutdown budget, with what is still conditional.**
t_iso = 5 ms is 10× the 0.5 ms turn-off maximum; the 20 ms startup wait is 5×
the 4.0 ms turn-on maximum. Isolate-then-release consumes 5 ms of the 1000 ms
between the 1800 s deadline and the 1801 s release limit, leaving 995 ms, so
the ordering costs nothing in the deadline. The enable-side 20 ms happens
after HOLD is already asserted, so it does not enter the ≤900 ms retention
path either. **Still conditional, and carried as a bring-up measurement:** the
turn-on maximum is specified into a 20 kΩ load and this branch presents 55 kΩ,
and the 190 pF output capacitance is a typical value with no maximum. Neither
5 ms nor 20 ms is promoted to a guarantee.

**Signal path.** R<sub>ON</sub> 300 Ω maximum (at I<sub>O</sub> = 2 mA) in the
22 kΩ top leg takes the divider ratio 0.600000 → 0.596745, a **−0.54 % shift,
−16.3 mV** referred to a 5 V pulse; the high level lands at 2.98 V against an
RP2040 V<sub>IH</sub> of about 2.0 V. The signal current is 90.4 µA, two
decades below the current R<sub>ON</sub> is specified at, so 300 Ω is used as
an upper bound. Because no series element enters the **fuel or supply** top
leg, the ≤25 Ω and ≤100 Ω limits of `REV_A_INTERFACES.md` §3.4 and the
card-header calibration problem of its §8.2 both fall away: `log.adc.fuel
div=7500/4700` still has every term it needs.

**Footprint.** Created locally and verified against the manufacturer drawing
rather than the summary: 12 pads at numbers 1–10, 15 and 16, 1.270 mm pitch,
pad 2.871 × 0.65 mm, pad centres at ±4.3815 mm, from the recommended land
pattern's 11.634 mm overall span and 8.763 mm centre spacing and its 0.635 mm
minimum pad width. **Pins 11–14 do not exist** and that gap is left clear.
**Pin 3 is "do not connect" — internally tied to pin 5** — and
`check_capture.py` asserts it is unconnected. A stock `SOIC-16W` footprint
would put pads where there are no leads, which is the error LRA-11 flagged.
Neither creepage figure is load-bearing at these voltages — the device is used
for off-state blocking, not for safety isolation, and
`REV_A_INTERFACES.md` §4 already records that this installation is not
galvanically isolated — but the drain gap is kept clear anyway because it is
free.

**Finite leakage, stated as such.** "Eliminated" and "no conductive path of
any kind" are overstatements and are not repeated. The bound is 1 µA maximum
over the operating range, 1.0/1.0 µA in the ledger, against the 8/20 µA
reserved for all five branches. Open-state coupling is 0.173 µA average at
91 Hz through the typical 190 pF, which is a typical value, not a maximum.

**Availability is the one open item**, unchanged: distributor lifecycle data is
contradictory. Panasonic **AQY221N2S** remains the documented fallback — a
strictly smaller part inside the same keepout, better on every axis except the
one that decides it, since its 10 nA leakage maximum is from a 25 °C-only
table. If it is chosen, hot leakage must be measured.

### 4.3 X2–X5: bypass, decided

**Decision: no isolation device on B1, C14, C11 or B11.** Grounds:

1. **Criterion A is met with nothing fitted, and better than with a switch.**
   All four are ignition-fed and measured or logged dead with the key out, so
   the parked injection is zero rather than four devices' leakage.
2. **Criterion B needs a power fault as well as the key on** (§4.1), and in
   that state the fitted series resistance bounds each branch: 0.659 mA for
   the tach at 14.8 V, 0.627 mA for the brake at 14.1 V, 0.668 mA for the
   supply at 15 V, 0.906 mA for the fuel channel at its 8 V ceiling through
   7.5 k + 1 k. **Criterion B's 0.3 V dead-rail limit is not met in that
   state, and that is reported rather than claimed closed.** Isolating B2
   lowers the criterion-B total from 3.07 mA to 2.86 mA rather than raising
   it.
3. **The cost is concrete.** Four more ASSR relays would add 4 × 12.3 mA =
   49 mA of awake LED current — about doubling the awake branch baseline — and
   four 10.4 × 7.5 mm packages on a board with a 1.52× area allowance, against
   a fault-only benefit.
4. Series resistance in the fuel or supply top leg would also re-open the
   card-header calibration question for no gain.

Carried forward unchanged: the five divider ratios, the 1N5819 digital clamps
and the fitted ADC protection. **D11 stays open** — the tach cell's clamp
margin is smaller than estimated, because the measured 159 mV at 109 µA shows
V<sub>F</sub> keeps falling below a 0.3 V assumption. LRA-12 changes no ratio
and claims no clamp margin; resolving D11 needs U-08 first and is not a layout
blocker.

---

## 5. X6 and X8 — capturing circuits that already existed

Both were capture work, not design work: `LAYOUT_READINESS_2026-10-29` is
right that the sources specify them component for component. They are
transcribed from `CUTOFF_MARGIN_REVIEW.md` §§1–2 and `MAX_ON_CUTOFF.md`'s
connection table, and `check_capture.py` asserts every pin of every package
against those tables, plus all eleven Boolean equations read back off the
netlist by package pin.

What needed a decision rather than a transcription:

**The opto rewire (X6).** The collector goes to A5 and the emitter to IGN_A,
an emitter follower into the 47 k / 220 k / 1 µF filter. The old
collector-to-GP5 wiring is gone, as `D-RA-03` requires. CTR margin at the
measured 2.2 k: at the 9 V characterisation point the LED takes 3.39 mA, and
the ≥50 % CTR at 5 mA makes at least 1.7 mA of collector current available
against the 95.7 µA the 47 k load needs at the 4.5 V ON endpoint — about 15×.
Hot CTR and the endpoints themselves stay open (LRA-07).

**The report node carries no capacitor.** That answers the open half of D1:
with the 10 k pullup against roughly 30 pF of node capacitance the edge is
under a microsecond, so the report delay is nowhere near the 10 ms observation
budget. The fitted 100 nF across the old opto output is not carried forward
because the node it filtered no longer exists.

**Where the cutoff interrupts HOLD (Q6).** QS sits between SINK and the QH
collector, drain to SINK, source to the collector, so its body diode points
from the collector toward SINK and blocks the sink direction when off. QH
keeps its emitter grounded; interrupting the emitter instead would couple
fault voltage into the HOLD interface. QI stays wired straight to SINK, so raw
ignition still overrides the cutoff. RGS changes from 100 k to 10 k, which is
what makes the added series switch tolerable: the 0.2 V off-gate limit then
allows 19.80 µA of total sink leakage instead of 2 µA.

**The accelerated-cutoff provision, kept distinct from the production
selection and from the maintenance link.** Three different things, three
different parts:

| Part | What it is | Default |
|---|---|---|
| **JH** | Maintenance HOLD link: open it for USB work so a USB-driven HOLD cannot keep the battery circuit on | fitted |
| **R_EXPP** 0 Ω | Production period select: EXPIRED from UCOUNT Q13, nominal 2048 s | **fitted** |
| **R_EXPT** 0 Ω | Accelerated test select: EXPIRED from Q8, 128 / 2 = 64 s | **DNP** |

Link options rather than a jumper header, so the production state cannot be
changed by something falling off, and **exactly one is ever fitted** — they
are two counter outputs and must never be shorted together. A 100 k pulldown
(R_EXP) keeps EXPIRED defined if neither is fitted, costing nothing parked
because EXPIRED is low until the deadline. An accelerated run does not
substitute for one full-duration test.

**Every unused CMOS input is tied to a rail** — ULATCH pins 12 and 13 to
ground — and **every package has its own 100 nF across its own supply pins**.
Both are layout requirements as much as BOM lines.

What the cutoff still does not cover, unchanged and restated so nobody reads
more into the drawing: a stopped clock, failed timer logic, a shorted QS or
QP, an ignition line stuck high, repeated raw pulses that energize QI, or
external backfeed. A5 faults can remove power before the deadline. No SD
integrity claim survives a forced cutoff.

**A procurement note on the oscillator, not a redesign:** the selected
OV-7604-C7-32.768KHZ-20PPM-**TA-QC** is commercial grade. Micro Crystal offers
the same package as **QA**, AEC-Q200 qualified. That is an ordering decision
for the owner, and the design is unchanged either way. Its −40 to +85 °C TA
range, 0.3/0.5 µA at 3.0 V with CLKOE low and 0.5 s maximum startup are from
[the datasheet, version 4.5/08.2023](https://www.microcrystal.com/fileadmin/Media/Products/kHzOSC/Datasheet/OV-7604-C7.pdf),
whose −0.035 ppm/K² curvature reproduces the 188.65 ppm term in the ±220 ppm
first-year envelope the 2048 s arithmetic uses.

---

## 6. Grounding, the LED return, and the connectors

### 6.1 R06-REV-2 and Q2: the opto LED returns to PGND

**Decision: U2 pin 2 goes to PGND, not to the B16 cluster conductor.**

The conflict was real and could not stand: `AS_BUILT` §3.4 records the fitted
LED cathode going to B16 "with nothing in series", while §4 and delta D5 make
B16 a reference that "must never become a power return" — and with B16 bonded
to the single ADC return node, the fitted cell put 4.7–5.8 mA of
*signal-dependent* current through the node both ADC channels reference. A
common-mode offset largely self-cancels in the fuel computation; a few
milliamps of signal-dependent current in the reference does not.

Moving the return costs nothing, is the arrangement `DESIGN.md` §3 already
specified, and puts DR directly antiparallel with the LED, which is the
position that actually limits LED reverse voltage against the PC817's 6 V
input rating.

What B16 still carries, stated so the decision is not oversold: the two
divider return currents, at most about 0.65 mA combined and only while the
cluster is energized. Those are intrinsic to a ratio measurement referenced
to cluster ground. The LED current was not.

The consequence, recorded rather than hidden: the LED current now returns
*into* the board instead of off-board. It cannot reach a switched rail — the
opto's output side is in the A5 domain and galvanically separate from its LED
— so this removes an injection path rather than relocating one.

### 6.2 Pico-internal ground continuity

AGND and PGND **are already joined inside the Pico module** (`AS_BUILT` §3.3),
so separate net labels do not isolate those conductors. That junction is the
single point, which means **layout must not add a board-level bond between
AGND and PGND**: a second connection would make a loop and give the ADC
return a parallel path, which is exactly what D5 exists to prevent.
`check_capture.py` asserts that the two nets stay separate on the board and
that no two-terminal part bridges them.

The three ground loops follow the keyless pattern: TP_GND_BUCK and
TP_GND_PICO on PGND, TP_GND_HARNESS on the bonded B16/AGND sense node.

### 6.3 Connectors

Both from the Molex Mini-Fit Jr. 4.20 mm family, which `D-POWER-03` records as
in service in this car on the keyless body harness, so the mating housings and
crimp tooling already exist.

| | Part | Footprint | Mating |
|---|---|---|---|
| **J1** power, 2 circuits | Molex **39-30-1020** (5569-02A2), right-angle with PCB peg | `Connector_Molex:Molex_Mini-Fit_Jr_5569-02A2_2x01_P4.20mm_Horizontal` | Mini-Fit Jr. 5557-series receptacle housing with 5556 female crimp terminals, 16–24 AWG |
| **J2** cluster harness, 8 circuits | Molex **39-30-1080** (5569-08A2) | `...5569-08A2_2x04_P4.20mm_Horizontal` | same family |

Pin numbers are Molex cavity numbers. 9 A per circuit against a 1 A branch, so
the margin is in the crimp rather than the contact. `REV_A_INTERFACES` §5.1
requires J2 to mate with the **existing** cluster breakout, whose taps are
already this family, so the choice is constrained rather than preferred. Exact
order codes for plating and packaging are procurement, not a design gate.
Connector *placement* is the layout owner's.

### 6.4 Tap-end fuses versus an onboard FIGN (Q4)

**The onboard FIGN is dropped.** `REV_A_INTERFACES` §5.1 and delta D10 put
per-branch fuses at the tap end, "which is where the specification puts them
and where a chafed wire is actually backed by vehicle current". An onboard
fuse cannot protect the upstream harness, and the board cannot draw enough
through RI and RLED — 1.1 kΩ together — to need one. C11 and B11 already have
their tap-end fuses; D10 extends the same 100 mA fuse to B2, B1 and C14 and
remains the owner's.

### 6.5 J4 (Q5)

**J4 is the RUN-to-GND reset pair and nothing else**, shorted with a link for a
reset without cutting power, following keyless J7. The service UART that §5.1
also wanted there is dropped: GP0/GP1 must stay free, firmware already builds
with `pico_enable_stdio_usb` so the USB CDC console *is* the service path, and
a UART header would be another externally powered pull-up aimed at an off
GPIO. A header with NC pins was the contradiction; this has none.

### 6.6 Communications

Bounded in [communications/REV_A_PROVISION.md](../communications/REV_A_PROVISION.md).
In one line: a passive 8-way expansion header for a **DNP daughterboard**, no
transceiver or bias or termination on this board, switched power only, the
tied DE//RE line kept and every claim that depended on an unreachable shutdown
state dropped.

---

## 7. The parked ledger, and a re-allocation to propose

Recomputed in `check_layout_closure.py` §4 with the LRA-12 part changes. Every
figure is a datasheet maximum **at the stated condition** — a mixed-condition
screen, not an assembled maximum, and not a prediction.

| | Room screen, µA | Hot screen, µA |
|---|---:|---:|
| A5 domain subtotal (14 rows) | 59.98 | 346.85 |
| QP IPD50P04P4L-11 drain | 1.00 | 70.00 |
| Gate sink paths, QS + QI + PCB | 10.00 | 19.80 |
| Entry clamp at P12 | 1.00 | 10.00 |
| UISO, from the B2 source | 1.00 | 1.00 |
| Other four vehicle branches | 0.00 | 0.00 |
| QMON / QREPORT / QH injection | 2.00 | 5.00 |
| **Whole-system screen** | **74.98** | **452.65** |
| Unchanged acceptance target | 100 | 500 |

**The whole-system targets close as component screens**, with 25 µA and 47 µA
of headroom, and they are not relaxed.

**The sub-allocations do not, and that needs a reviewer decision.** The A5 row
is allocated 50 / 250 µA and screens 59.98 / 346.85 — over by 10.0 and
96.9 µA. The reason is not a defect: the QP change freed 180 µA of hot
headroom from the 200 µA switch allocation, so the money is there, in the
wrong row.

**Proposed re-allocation, totals untouched:**

| Allocation | Old room / hot | Proposed room / hot |
|---|---:|---:|
| A5 supply + complete timer/logic/filter leakage | 50 / 250 | **65 / 355** |
| QP drain and gate leakage into the switched stage | 30 / 200 | **15 / 70** |
| Gate sink paths, entry protection, other PCB leakage | 10 / 25 | 12 / 50 |
| All other energized signal/interface paths | 10 / 25 | 8 / 25 |
| **Total** | **100 / 500** | **100 / 500** |

`INTERFACE_CONTRACT.md` §7 already invites this kind of explicit
reallocation — it made one itself, moving 10 µA from interfaces to A5 — and
says reviewers may redistribute within the total. This needs manager and
electrical acceptance; it is recorded as a proposal, not applied.

The two largest hot rows are the HC counters at 80 µA each and the clock
reservoir at 66.25 µA. One bounded option exists for the last of those and is
**not** taken: the real VCLK load is about 3 µA, not the 100 µA the ramp
calculation conservatively allowed, so a 10 k / 2.2 µF pair would give the
same 0.232 V/ms slew with a fifteenth of the capacitance and a 0.03 V static
drop. It is not taken because it re-opens the oscillator slew and startup
qualification that `CUTOFF_MARGIN_REVIEW` §1 settled, for a saving the whole
system does not need. Recorded with its numbers so the next reviewer does not
have to re-derive it.

Still open as engineering, unchanged: the A5 regulator's ground current below
100 µA of load and its low-load output accuracy; the hot leakage of QP, QI,
QH, QMON, QS, QREPORT and the opto under their actual networks; and the
capacitor approval-sheet bias, aging and insulation-resistance data. **No
permanent preload may be added to buy a regulation specification** — it
defeats the budget.

---

## 8. Fit on 80 × 120 mm

Recomputed from the footprints actually assigned, by `../kicad/fp_area.py`,
which measures each part's F.CrtYd courtyard bounding box and writes
`validation/courtyard_study.csv`. The earlier 5,031 mm² figure was nominal
package areas over a part set that had ten parts with no footprint and none of
the power logic, so it could not be re-quoted.

| | |
|---|---:|
| Parts with a footprint | **141 of 141** |
| Courtyard sum, fitted parts | **6,315 mm²** |
| Board 80 × 120 | 9,600 mm² |
| **Allowance** | **1.52×** |
| Measured from pads rather than a courtyard | none |

A courtyard sum is an occupancy floor including each part's own clearance, not
a placement: it says nothing about routing channels or connector access. It is
a tighter measure than the "nominal package area" the 1.6–2.0× guidance was
written against, so 1.52× on courtyards is roughly comparable to about 1.9× on
raw package area. **It fits, with 3,285 mm² free, and the margin is real but
not generous.**

The five largest items are the Pico module (1,243 mm²), J2 (423), the two
DIP-16 counters (203 each) and the three DIP-14 logic packages (178 each).

Two choices already taken in favour of area, both defensible on other grounds:

- **Axial parts take the keyless board's vertical mountings.** 62 axial parts
  measure 1,588 mm² vertical against 2,208 mm² horizontal — **620 mm², 6.5 %
  of the board** — and it is the convention already soldered and running in
  this car.
- **The SD bulk is a 6.3 mm can**, not a 10 mm one, because 47 µF is sized
  from the duty rather than from the top of D6's range.

If the owner's placement does not close, the reductions available, in the
order worth taking them:

| Change | Saving | Cost |
|---|---:|---|
| Glue logic DIP-14/16 → SOIC-14/16 | **582 mm²** → 1.67× | Loses easy probing and socketing on a board with five bench test groups still ahead |
| Drop the five ground and spare test points | ~65 mm² | Loses the three-loop return measurement the keyless pattern exists for |
| Passives → 0805 SMD | ~1,300 mm² | Against the owner's through-hole preference; last resort |

**The board is not silently enlarged, and no mechanical blocker is claimed.**

---

## 9. Reproducing the checks

From the repository root:

```sh
# schematic, symbols and BOM are generated from one parts table
cd logger/hardware/kicad
python3 tools/gen_custom_sym.py Custom.kicad_sym
python3 tools/gen_logger_sch.py .

export HOME=$(mktemp -d)                 # temporary KiCad configuration
mkdir -p "$HOME/.config/kicad/9.0"
cp /usr/share/kicad/template/sym-lib-table \
   /usr/share/kicad/template/fp-lib-table "$HOME/.config/kicad/9.0/"
kicad-cli sch erc --format json --severity-all -o validation/erc.json \
    accord-logger.kicad_sch
kicad-cli sch export netlist --format kicadsexpr -o validation/netlist.net \
    accord-logger.kicad_sch
kicad-cli sch export svg --no-background-color --exclude-drawing-sheet \
    -o validation accord-logger.kicad_sch
mv -f validation/accord-logger.svg validation/schematic.svg

python3 check_capture.py        # 652 structural checks against the netlist
python3 fp_area.py              # courtyard study and the 80 x 120 fit
cd ../../..
python3 logger/hardware/power/check_layout_closure.py     # 49 + 2 reported
python3 logger/hardware/power/check_cutoff_margins.py     # 8
python3 logger/hardware/power/check_max_on_logic.py       # 11
python3 logger/hardware/power/check_interface_contract.py # 14
python3 logger/hardware/power/check_component_margins.py  # 11
python3 logger/hardware/isolation/check_b2_isolation.py   # 24
python3 logger/hardware/as-built/check_as_built_numbers.py
```

Results on this session: **ERC 0 violations at `--severity-all`**;
`check_capture.py` 652/652; `check_layout_closure.py` 49/49 with the two
sub-allocation overruns of §7 reported explicitly; all 68 pre-existing checks
pass unchanged.

`kicad-cli` does not signal violations through its exit code unless
`--exit-code-violations` is passed, so a zero exit is not evidence of a clean
design — the result is read from `validation/erc.json`.

**What these prove and do not prove.** `check_capture.py` proves the drawing
agrees with the written design, connection by connection, read from the
exported netlist rather than from the table that generated it.
`check_layout_closure.py` is arithmetic over datasheet limits plus one
topology audit on the netlist. Neither is SPICE, a measurement, or a component
qualification. Every conditional input says it is conditional.

One thing this session could not do: **no SVG rasterizer exists on this host**,
so `validation/schematic.svg` was never rendered and looked at. Legibility was
handled structurally — every part is placed on the 1.27 mm connection grid,
labels sit at the end of 2.54 mm stubs, and the thirteen block frames and the
notes column are laid out on an A0 sheet — but **a reviewer should open the
project or the SVG once.** That is the one acceptance item that cannot be
closed from here.

---

## 10. Residual risks

Classified in full in [LRA12_HANDOFF.md](../LRA12_HANDOFF.md) §5, with a
concrete test or provision and a limit for each. None is a layout blocker.
In summary: one order gate the design depends on (ASSR availability, with a
specified fallback), a group of bring-up measurements that are conditional
datasheet readings rather than guarantees, the vehicle exposures the owner
must state, and one firmware contract — the ISO_EN sequencing — that the
hardware is safe without, because every default is open.

> **Required agent attribution:** Follow `logger/coordination/AGENT_ATTRIBUTION.md`
> relative to this project root. Use your own tool, role and verified current
> session ID for Git author and committer identity (`<Tool> <role> [<short-id>]`),
> with per-command settings. End each new commit message with `Agent-Session: <role>`
> and your full tool-specific session-ID trailer (`Codex-Session-ID`,
> `Claude-Session-ID` or `Antigravity-Session-ID`). This includes documentation-only
> commits. Identify yourself and your resume command in new coordination documents
> and dated updates. Preserve predecessor bookmarks and original attribution when
> transporting existing commits. If your ID is unavailable, say so rather than
> inventing one. Include this requirement in any seeds or handoffs you create.
