# LRA-12 return — the electrical design is ready for layout

Prepared October 29, 2026 by Claude Code `logger-electrical`, session
`b690946d-3a88-4626-8e7b-b321126a3d16`.
Resume: `claude --resume b690946d-3a88-4626-8e7b-b321126a3d16`.
Session ID read from this session's harness-assigned working paths and
confirmed against its transcript file; this tool exposes no second identifier
to cross-check it against, so that is stated rather than implied.

Branch `task/LRA-12-b690946d`, from public `main` at
`5ffcb26958d2b7154b4d1417431fad22246cedd9`.
Packet: [LRA-12](../../coordination/handoffs/LRA-12_LAYOUT_ELECTRICAL_CLOSURE.md).

**Role claim, for the manager's tracker:** this session took the unclaimed
LRA-12 electrical/KiCad assignment and worked only inside the single edit
scope the packet grants. It is the engineer the
[current manager handoff](../../coordination/handoffs/PCB_MANAGER_LAYOUT_HANDOFF_2026-10-29.md)
recorded as occupied and waiting on usage.

---

## 1. Is the electrical layout handoff ready?

**Yes, for placement and routing. No, as an approved board — and those are
different gates.**

| Acceptance item from the packet | Result |
|---|---|
| Schematic completeness: no X1–X8 placeholder remains | **Met.** All eight resolved: five with real circuits, four branches with a recorded justified bypass. No dashed body remains; `check_capture.py` asserts that no placeholder symbol survives |
| Interface coherence: one GPIO/domain/enable/state table, no 5 V GPIO pullups, no unexplained alternate power paths | **Met.** One pin map asserted pin by pin against `REV_A_INTERFACES` §1; the only GPIO pullup is RIGN to **switched** 3V3, asserted; GP7 taken up as ISO_EN with its reason recorded in the contract change record |
| BOM/footprints: one population BOM, exact MPN or a precise interchangeable specification, selected connectors, verified pad mappings, no hidden mandatory TBD | **Met.** 141 rows, one file, with a population column. Every part has a footprint. Two local footprints built from manufacturer drawings. Connectors selected from the in-service family with mating housings named |
| ERC and net audit: fresh ERC with zero unresolved errors, every warning dispositioned, netlist checks for connectivity, polarity and cutoff paths | **Met.** **0 violations at `--severity-all`** — no errors and no warnings, so nothing to disposition. 652 netlist checks including every polarised part by pin number and the cutoff path by net identity |
| Checks: rerun the existing scripts, update the capture assertions, add meaningful state/corner checks | **Met.** All 68 pre-existing checks pass unchanged; `check_capture.py` rewritten to 652; new `check_layout_closure.py` adds 49 envelope, corner, ledger and topology checks plus 2 reported sub-allocation overruns |
| Layout handoff: fit, keepouts, high-current loops, return strategy, trace rules, test points, assembly constraints | **Met.** §4 below |
| Residual risks classified with a concrete test and limit | **Met.** §5 below. **No layout blocker remains** |
| Publication: public-safe, owned paths only, own attribution, pushed branch and full commit IDs | **Met.** §6 below |

**What "ready for layout" does not mean.** Nothing is frozen, ordered,
fabricated, flashed, wired or deployed. The power stage is bench-rated: QI and
QH are 2N3904 for a 12–16 V bench, F1 assumes a current-limited supply, and a
24 V jump start with the board connected is a declared excluded exposure. A
complete, routable design is not an approved board.

---

## 2. Decisions

Full reasoning and calculations in
[power/LAYOUT_CLOSURE.md](power/LAYOUT_CLOSURE.md). One line each:

| ID | Decision |
|---|---|
| **X7 entry clamp** | **1.5KE20A-E3/54** replaces the inherited 1.5KE30A, at P12 and at the B11 harness entry. Forced: the only P-FET with a hot leakage maximum that fits the parked budget is rated 40 V, and 41.4 V was already above QI/QH V<sub>CEO</sub> and the LM2678 ceiling |
| **X7 second stage** | **R_AON 330 Ω + BZX55C22 + C_AON** give the A5 regulator its own envelope. Worst P_AON **25.70 V**, so the ≤28 V criterion is met at TP_PAON. The hot clamp is 29.20 V, which clears every 40 V part by 10.8 V but not a 28 V target |
| **X7 exposure** | Sustained P12 is declared **≤17.1 V**. A 24 V jump start with the board connected is excluded, with the two alternatives costed for review |
| **QP / DZ** | **IPD50P04P4L-11 + BZX55C10**, the LRA-02 paired proposal, taken. Resolves the IRF4905's 250 µA hot screen against its own 200 µA allocation |
| **X1 isolation** | **ASSR-601JV** in the B2 divider top leg, with **R_ISO 270 Ω** (not 330 Ω, so the worst-case LED current reaches the 10 mA the turn-on maximum is specified at) |
| **X1 enable** | **GPIO enable in series with a hardware PGOOD permission**, two BSS138P channels. BAD opens the branch with no software step, which a B5-only argument could not do because QI can hold power through a BAD event |
| **X2–X5** | **Justified bypass**, on the ignition interlock plus the fitted series resistance, with a nine-state reachable-state table. Criterion B is **not** met in the key-on-plus-power-fault state and that is reported, not claimed closed |
| **X6** | Captured component for component from `CUTOFF_MARGIN_REVIEW.md` §2, including the opto rewire into the A5 domain and **no capacitor on the report node**, which closes the open half of D1 |
| **X8** | Captured from `MAX_ON_CUTOFF.md`, with **QS between SINK and the QH collector** (Q6) and QMON sensing ahead of JH |
| **Period select** | **R_EXPP 0 Ω fitted** for the production 2048 s, **R_EXPT 0 Ω DNP** for the 64 s accelerated test, kept distinct from the JH maintenance link. Fit exactly one |
| **R06-REV-2 / Q2** | Opto **LED cathode moves from B16 to PGND**. The fitted cell put 4.7–5.8 mA of signal-dependent current through the ADC reference node |
| **Grounds** | AGND and PGND are already joined **inside the Pico module**; that is the single point and layout must not add a board-level bond |
| **J1 / J2** | **Molex Mini-Fit Jr.** 39-30-1020 and 39-30-1080, right-angle, the family already in service in this car. J2's mate is the existing cluster breakout, so the choice is constrained |
| **Q4** | Onboard **FIGN dropped**; per-branch fuses belong at the tap end (D10, owner's). F1 stays as the board's own branch protection and does not protect the harness |
| **Q5 / J4** | **J4 is the RUN/GND reset pair only.** The service UART is dropped: USB CDC is already the console |
| **Communications** | **Passive DNP expansion header**, no transceiver, bias or termination on this board. LRA-04's two contradictions resolved; LRA-04 itself stays returned with revisions required |
| **C_SD** | **47 µF/16 V** selected from the duty, replacing the 10–100 µF range |
| **Footprints** | Axial parts take the keyless board's **vertical** mountings: in service in this car, and worth 620 mm² |
| **Ledger** | A **re-allocation** within the unchanged 100/500 µA totals is proposed. The totals close at 74.98/452.65 µA; the A5 sub-allocation does not, and the QP change freed the headroom to fix it |

---

## 3. Changed artifacts

All inside the single edit scope the packet grants. Nothing outside it was
touched: no keyless file, no other agent's worktree, no file pinned by a
`SOURCE_MANIFEST.json`, no firmware, no root or coordination document.

| Path | Change |
|---|---|
| `logger/hardware/kicad/accord-logger.kicad_sch` | Regenerated: 141 parts, 81 named nets, thirteen block frames, twelve note blocks |
| `logger/hardware/kicad/BOM.csv` | Regenerated: 141 rows, new `population` column |
| `logger/hardware/kicad/Custom.kicad_sym` | Nine symbols. Five LRA-06 placeholders retired; eight parts added that the installed libraries do not carry |
| `logger/hardware/kicad/tools/gen_logger_sch.py` | Extended to the complete design. **Not retired** — it is still the single source for the schematic and the BOM together, which is why they cannot drift apart. Edit the generator, not the `.kicad_sch` |
| `logger/hardware/kicad/tools/gen_custom_sym.py` | `ic_box()` added; placeholders no longer emitted, with the mechanism kept and documented |
| `logger/hardware/kicad/check_capture.py` | Rewritten for the completed design: 652 checks |
| `logger/hardware/kicad/fp_area.py` | **New.** Courtyard study and the 80 × 120 fit, from the assigned footprints |
| `logger/hardware/kicad/accord-logger.pretty/` | **Two new footprints** from manufacturer drawings, plus its README |
| `logger/hardware/kicad/validation/` | Fresh `erc.json`, `netlist.net`, `schematic.svg`; new `courtyard_study.csv`; updated `COMMANDS.txt` |
| `logger/hardware/kicad/CAPTURE_NOTES.md` | LRA-12 status header with a per-section supersession table. The LRA-06 record below it is unchanged |
| `logger/hardware/power/LAYOUT_CLOSURE.md` | **New.** The decisions and their calculations |
| `logger/hardware/power/check_layout_closure.py` | **New.** Envelope, corner, ledger and netlist topology checks |
| `logger/hardware/power/INTERFACE_CONTRACT.md` | One pointer near the top and a new **§10 change record**, L01–L12. The reviewed body text is otherwise unchanged |
| `logger/hardware/isolation/ISO_ENABLE.md` | **New.** The implemented enable circuit and the answer to the manager's four qualifications. `B2_ISOLATION.md` is unchanged and keeps its own authorship |
| `logger/hardware/communications/REV_A_PROVISION.md` | **New.** The bounded provision |
| `logger/hardware/LRA12_HANDOFF.md` | This file |

**Core documents that need the manager, not me.** `logger/hardware/README.md`
and `logger/hardware/REV_A_CONTEXT.md` are core entry points and were in the
manager's own staged working tree while this ran, so they are deliberately not
edited here. They will need the LRA-12 state and the `communications/`
directory added when this is integrated. The tracker claim and
`PROJECT_MILESTONES.md` are the manager's alone.

**Retain `accord-logger.kicad_pro`**, the project-local libraries and the
designator-to-source mapping: unchanged, and the `Source_designator` field and
BOM column still let a reviewer diff against `DESIGN.md` §3 and the connection
tables.

---

## 4. Layout guidance

The agreed envelope is **80 × 120 mm**, a generic rectangle, no enclosure.
Placement and routing are the owner's; this is the constraint set, not a
floorplan.

### 4.1 Fit

| | |
|---|---:|
| Parts with a footprint | 141 of 141 |
| Courtyard sum, fitted | **6,315 mm²** |
| Board | 9,600 mm² |
| Allowance | **1.52×** |

Measured by `kicad/fp_area.py` from each part's F.CrtYd bounding box, written
to `kicad/validation/courtyard_study.csv`. It is an occupancy floor including
each part's own clearance, not a placement. Five items are 40 % of it: the
Pico module (1,243 mm²), J2 (423), two DIP-16 counters (203 each), three
DIP-14 logic packages (178 each).

**If placement does not close**, in the order worth trying: glue logic
DIP → SOIC-14/16 saves **582 mm²** (→1.67×) at the cost of easy probing and
socketing; dropping the five ground and spare test points saves ~65 mm² at the
cost of the three-loop return measurement; passives → 0805 saves ~1,300 mm²
against the owner's through-hole preference. **Do not silently enlarge the
board.**

### 4.2 Four blocks that want to stay together

1. **Buck switching loop — the only genuinely critical one.** CIN, UREG
   pins 2 and 4, DCATCH and L1. The input loop is CIN(+) → UREG VIN → SW →
   L1 → COUT → PGND → CIN(−), carrying up to 1.14 A peak at 260 kHz with
   0.77 A of ripple at the worst corner. Keep CIN within a few millimetres of
   UREG pins 2/4 and DCATCH's cathode at SW with its anode on the same
   PGND node as CIN(−). CBOOST between SW and pin 3 must be short.
   `DESIGN.md` §3 is explicit: do not build this on long leads.
2. **A5 domain and the cutoff logic.** UA5, USUP, the clock block and the five
   logic packages, each with its own 100 nF **across its own supply pins** —
   that is a placement requirement, not just a BOM line. Keep this group away
   from the buck loop; it is the group whose leakage the parked budget
   depends on.
3. **Analog island.** Both ADC dividers' bottoms, their 1 µF filters, their
   four 1N5819 clamps, J2 pin 6 (B16) and the Pico's AGND pin on one node.
   **No board-level AGND-to-PGND bond** — the junction inside the module is
   the single point, and a second one makes the loop D5 exists to prevent.
4. **Isolation relay.** UISO with its 270 Ω and two BSS138P. Keep the pin
   11–14 gap clear of copper and vias (marked on `User.9`).

### 4.3 Return strategy

- **PGND** carries the buck return, the Pico GND pins, the opto LED return
  (now, by decision), the digital divider bottoms, the logic grounds and all
  the gate pulldowns. On a two-layer board, give it as much contiguous copper
  as routing allows, with the buck loop's return kept local to that loop
  rather than shared with the A5 logic.
- **AGND** is a separate area, joined to the rest only through the Pico
  module. Route it as an island reaching the Pico AGND pin, with the two
  divider bottoms, both filters, both lower clamps and J2.6 inside it.
- **Three ground test loops**, following keyless: TP_GND_BUCK and TP_GND_PICO
  on PGND at those two physical locations, TP_GND_HARNESS on the AGND island.
  They are only useful if they are actually at the three places.

### 4.4 Trace and clearance requirements

| Net group | Requirement |
|---|---|
| BATT_IN, BATT_F, P12, VIN_SW, SW, B5, and their PGND returns | ≥0.8 mm (32 mil) on 1 oz copper; the buck loop as wide and short as the layout allows |
| VSYS, P3V3_SW | ≥0.5 mm; the SD write spikes are 100–200 mA |
| GATE, SINK, QH_C | ≥0.5 mm, and see the leakage note below |
| Signals and logic | 0.25 mm is ample |
| QP tab | **The DPAK tab is DRAIN** and carries switched battery voltage. Give it clearance from PGND and from the P12 pour, and copper area for heat |
| UREG | TO-220-7 vertical. About 0.5 W at 0.5 A out; copper at the tab, no heatsink needed in the bench envelope |
| P12 to PGND clearance | Size for 29.2 V of clamped transient, not for 12 V |

**Leakage-sensitive nodes, which are a layout matter and not only a procedure.**
Four nodes have budgets in the tens of microamps and will be spoiled by flux
residue or by a neighbouring high-voltage trace:

| Node | Budget | Why |
|---|---|---|
| GATE / SINK | **19.80 µA total** sink leakage | The 0.2 V off-gate limit through 10.1 kΩ. Keep away from P12 and VIN_SW; a PGND guard between them is cheap |
| IGN_A | **6.32 µA** | The 0.3 V OFF endpoint across 47 kΩ. Keep away from A5 |
| QUAL_N_REPORT | — | High impedance against a 10 kΩ pullup; keep it short and away from A5 |
| B2_TAP / B2_ISO | 1 µA device leakage | PCB leakage across the relay would defeat the part. Do not run anything between its input and output pads |

Clean assembly matters here: no-clean flux residue across these nodes can
exceed the whole budget on its own.

### 4.5 Access, keepouts and mounting

- **CYW43439 antenna keepout.** No copper, pour or plane under or beside the
  antenna end of the Pico module. Place the module with that end at a board
  edge. Wi-Fi delivery is load-bearing for the data path.
- **SD card removable without removing the board.** The module is 16 × 16 mm
  plus a `PinHeader_1x06_P2.54mm_Vertical`; let it overhang an edge so the
  card can be pulled.
- **USB reachable with the panel off** — `pico-flash` needs physical USB, and
  `pico_enable_stdio_usb` is already set so the 1200-baud reset interface
  exists. Permanently exposed is not required.
- **JH, J4 and the two 0 Ω period links** must be reachable without
  disassembly, and silkscreen-labelled: JH = maintenance HOLD, J4 = reset,
  R_EXPP = production 2048 s, R_EXPT = **DNP, 64 s test only**.
- **Current-sensitive test points** must be measurable without the instrument
  supplying the current being measured, and probes must come off for the
  final leakage reading. TP_PAON, TP_A5, TP_P12 and TP_GATE are the ones that
  matter.
- **Generic corner mounting holes**, committing to no particular mounting
  method, per `D-ENVELOPE-01`.
- Two-layer through-hole is the assumption throughout. The SMD parts are
  SOT-23/SOT-353, 1210, a DPAK, a tantalum D case, the SO-16 relay and the
  SON-4 oscillator — all hand-solderable, which is why the hand-solder
  footprint variants are used.

---

## 5. Residual risks, classified

**No layout blocker remains.** Everything below is an order gate, a
fabrication/bring-up gate, a vehicle gate or a firmware follow-up.

### 5.1 Order gates — resolve before committing money

| Item | Limit / test | Note |
|---|---|---|
| **ASSR-601JV availability** | Authorized-distributor check | Distributor lifecycle data is contradictory; about USD 6.25 at unit quantity. Fallback **AQY221N2S** is fully specified and is a strictly smaller part inside the same keepout; if chosen, its hot leakage must be **measured**, because its 10 nA maximum is 25 °C only |
| Fuse family, DC interrupt rating, time-current curve | Owner exposure inputs | F1 is 1 A; the curve matters for the sustained-overvoltage case §5.3 |
| Capacitor approval-sheet data | Bias, aging and insulation resistance for CIN, COUT, CCLK, the three 1210 ceramics and CQUAL | The selections are conditional on effective-C retention: ≥1 µF at P_AON, ≥2.2 µF at A5, 22–60 µF effective at VCLK |
| Oscillator grade | QC is commercial; **QA is AEC-Q200** in the same package | An ordering decision; the design is identical |
| 2N3904 and BSS138P manufacturer identity | Named-part sourcing | `BOM_DELTA.csv` already says generic kit names do not inherit the specifications |

### 5.2 Fabrication and bring-up gates

| Item | Limit / test |
|---|---|
| A5 ground current below 100 µA of load, and low-load output accuracy | Measure 4.89–5.11 V and ≤10 µA over the actual parked load, 6–28 V in, −40/25/85 °C. **No permanent preload may be added** to buy the specification |
| Hot leakage of QP, QI, QH, QMON, QS, QREPORT and the opto under their actual base networks | Measure at 20/25/30/85 °C before and after cutoff, with stuck HOLD, reset, JH open and an unpowered GPIO. Test QP at V<sub>GS</sub> = 0 and at the worst permitted −0.2 V |
| Clock startup and loaded supply ramp | Confirm ≤0.5 V/ms slew, VCLK ≥4.789 V, startup over temperature, and total XO_OUT load ≤10 pF including probe capacitance |
| Opto ON/OFF endpoints | ON ≥4.5 V and OFF ≤0.3 V at IGN_A, with all leakage, across the rail and temperature range. 104–376 ms ON and 119–590 ms OFF are **from settled endpoints only** |
| ASSR turn-on into 55 kΩ rather than the specified 20 kΩ | Scope the first VSS edge after the 20 ms wait, hot and cold. Also R<sub>ON</sub> at 90 µA and its drift |
| Assembled rail decay with the larger COUT | The bleeder-only screen is **5.39 s against the 5 s criterion**, so measure the cascade; CIN can keep feeding the buck while COUT decays |
| LM2678 loop stability with the selected output capacitor | Load steps to 0.5 A; a ripple rating is not a stability proof |
| Entry clamp cold margin | 1.89 V between the 16 V operating ceiling and cold V<sub>BR</sub> minimum; confirm no conduction at −40 °C/16 V |
| Accelerated cutoff, then one full duration | Fit R_EXPT for the 64 s run, then R_EXPP for a full 2048 s with the clock frequency and temperature recorded |
| Criterion B, the four bypassed branches | Inject each energized branch with the board dead and confirm the injection matches the 0.63–0.91 mA computed, and that no unintended rearm follows. **The 0.3 V dead-rail limit is not expected to be met in that state** |
| Parked current, assembled | ≤100 µA at 20–30 °C and ≤500 µA at 85 °C, settled, IGN off, USB absent, harness attached, every independently energized source logged separately |

Fixture limits, instrument setup and the staged current limits are in
`power/COMPONENT_MARGIN_CLOSURE.md` §5 and `power/PROTOTYPE_TEST_PLAN.md` and
are unchanged.

### 5.3 Vehicle gates

| Item | What it needs |
|---|---|
| **Sustained overvoltage / jump start** | Owner statement. A 24 V jump start with the board connected is **declared excluded**; the two alternatives are costed in `LAYOUT_CLOSURE.md` §3.4 |
| Load dump | Not covered. The clamp absorbs 1500 W for 10/1000 µs; a real load dump is three decades longer |
| Harness impedance, inductance, pulse amplitude/duration/repetition, fuse clearing | Owner inputs listed in `INTERFACE_CONTRACT.md` §6 |
| Long-duration hot and cold operation | Separate gate; the 85 °C parked screen is not an 85 °C operating rating, and the supervisor is specified only to +85 °C |
| D11, the tach clamp margin | Still open, and still needs U-08 first. LRA-12 changes no ratio and claims no margin |

### 5.4 Firmware follow-up

For the firmware reviewer (R01, still unclaimed and unaccepted). **The
hardware is safe before any of this exists**, because every default is open:
GP7 floats out of reset into a pulldown, so the relay never closes and the VSS
channel simply reads nothing.

| Contract | Value |
|---|---|
| **ISO_EN pin** | GP7, physical pin 10, output, 3V3 domain, default LOW |
| **Startup** | After B5 and the Pico are up, drive ISO_EN HIGH, **wait 20 ms**, then trust VSS edges on GP2. Edges before that may be a partially conducting switch |
| **Shutdown** | Drive ISO_EN LOW, **wait 5 ms**, **then** release HOLD. Isolate-then-release, never the reverse |
| **Budget impact** | The 5 ms consumes 0.5 % of the 1800→1801 s release allowance; the 20 ms is after HOLD is asserted, so it does not enter the ≤900 ms retention path |
| **Reset** | Latch ISO_EN LOW before enabling the output, as GP6 already requires |
| **GP5 semantics** | Unchanged from `D-RA-03`: GP5 is now **hardware-qualified** ignition, active low, with no second software debounce or rearm rule. With A5 absent and USB-only power, QREPORT is off and GP5 reads HIGH, which firmware must treat as ignition OFF |
| **Unchanged** | GP6 4 mA / 2.6 V, the 1770/1800/1801 s policy, the generation and race rules, the watchdog proposal, the recorded `ign` column |
| Not reserved | GP8/GP9/GP10/GP13 go to the expansion header as **offers**; firmware should not claim them |

### 5.5 Tests not run

No bench work of any kind was performed or authorized: no measurement, no
oscilloscope trace, no current reading, no temperature run, no assembly, no
wiring, no purchase, no fabrication, no firmware build or flash, no service or
database change. Every number in this return is a datasheet limit, an
arithmetic result from datasheet limits, or one of the owner's existing
measurements, and each is labelled as such.

One check this session could not do at all: **no SVG rasterizer exists on this
host**, so `kicad/validation/schematic.svg` was never rendered and looked at.
Legibility was handled structurally — everything on the 1.27 mm grid, labels
at the end of 2.54 mm stubs, thirteen titled block frames and a notes column
on an A0 sheet — but **a reviewer should open the project or the SVG once.**
That is the one acceptance item that cannot be closed from here.

---

## 6. Commands, results and publication

### 6.1 The exact KiCad entry point

```
logger/hardware/kicad/accord-logger.kicad_pro
```

Open that project. The schematic is `accord-logger.kicad_sch`, one A0 sheet.
The project-local libraries are `Custom.kicad_sym` and
`accord-logger.pretty/`, both registered `${KIPRJMOD}`-relative in
`sym-lib-table` and `fp-lib-table`, so the project is portable.

**The schematic and `BOM.csv` are both generated from one parts table** by
`tools/gen_logger_sch.py`. That is deliberate and is not retired: it is what
keeps the drawing and the BOM from drifting apart, and it is how the next
electrical change should be made. If you edit the `.kicad_sch` in the GUI
instead, re-running the generator will overwrite it — so either make the
change in the generator, or delete the generator first and say so in
`CAPTURE_NOTES.md`. For **layout** work this does not arise: the generator
writes no PCB file and nothing in it touches `.kicad_pcb`.

### 6.2 Results

```
ERC, kicad-cli 9.0.2, --severity-all           0 violations   (141 parts)
kicad/check_capture.py                         652/652
kicad/fp_area.py                               141/141 footprints, 1.52x
power/check_layout_closure.py                  49/49, 2 overruns reported
power/check_cutoff_margins.py                  8/8
power/check_max_on_logic.py                    11/11
power/check_interface_contract.py              14/14
power/check_component_margins.py               11/11
isolation/check_b2_isolation.py                24/24
as-built/check_as_built_numbers.py             all derived numbers reproduce
```

The two reported overruns are the A5 sub-allocation of §7 of
`LAYOUT_CLOSURE.md`, deliberately surfaced rather than summed away; the
unchanged 100/500 µA whole-system targets close at 74.98/452.65 µA. Exact
commands are in `kicad/validation/COMMANDS.txt` and `LAYOUT_CLOSURE.md` §9.

### 6.3 Publication

Staged contents were inspected before each commit. Only the paths of §3 are
touched. Nothing private is included: no credentials, no `secrets.h`, no
configured binary, no inventory export, no personal recording, no runtime
data. The two new footprints and all nine symbols are original work or are
derived from published manufacturer drawings, and the local `3d/` exclusion
elsewhere in the repository is untouched.

Commit IDs are recorded in §7 below.

---

## 7. Commits

| Commit | Contents |
|---|---|
| `7ec53daf95f539c1cdb0896ed1869dd6bba0a547` | The completed electrical design: schematic, symbols, two local footprints, BOM, validation exports, rewritten and new check scripts, `LAYOUT_CLOSURE.md`, `ISO_ENABLE.md`, `REV_A_PROVISION.md`, the `CAPTURE_NOTES.md` status header and the `INTERFACE_CONTRACT.md` change record |
| *(this file)* | The return handoff |

Author and committer identity on both: `Claude logger-electrical [b690946d]`,
set per command, with `Agent-Session: logger-electrical` and the full
`Claude-Session-ID` trailer. The shared and global Git identity is unchanged.

---

## 8. For the reviewer, in priority order

1. **Open the schematic once.** §5.5: the one acceptance item this session
   could not close.
2. **Accept or reject the ledger re-allocation**, `LAYOUT_CLOSURE.md` §7 and
   `INTERFACE_CONTRACT.md` L07. The totals are unchanged; one sub-allocation
   moves. Nothing else waits on it.
3. **Accept or reject the declared sustained-overvoltage exclusion**, L04. If
   the owner wants a 24 V jump start survived, option (b) or (c) of §3.4 is
   new scope and should be a separate task rather than folded in here.
4. **Check the entry-clamp chain**, `LAYOUT_CLOSURE.md` §3.1. It is the one
   decision that changes an in-service part, and the argument is a chain: if
   any link is wrong the clamp choice should be revisited. The counter-case is
   asserted in the check script, so it fails loudly if the premise changes.
5. **Note the four bypassed branches honestly**, L09: criterion B is not met
   in the key-on-plus-power-fault state, and the defence is an interlock plus
   bounded injection, not isolation.
6. Then record the claim, the branch and the commits in the tracker, and
   update `README.md` and `REV_A_CONTEXT.md`, which this session deliberately
   left to the manager.

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

## Revision LRA-12R — October 29, 2026

Prepared by Codex `logger-electrical`, session
`01a18a47-2dc2-7aa3-a0d2-a4978e2b1ebc`.
Resume: `codex resume 01a18a47-2dc2-7aa3-a0d2-a4978e2b1ebc`.
Identity verified from matching CODEX_SESSION_ID and CODEX_THREAD_ID.
Branch: `task/LRA-12R-01a18a47`, based on the original return
`ad4f9188a9cbef25b0c1717418076c5e9b92cda1`, in a separate worktree.
The original return above and its authorship are preserved. This section
supersedes its clamp rationale, A5 stage, exclusion wording and pending
manager-allocation decision. The manager owns integration and tracker updates.

**Decision:** retain 1.5KE20A and IPD50P04P4L-11 by choice, withdrawing the
claim that a hot-specified 60 V QP could not be found. Verified Vishay
SQD50P06-15L Rev. E: 60 V, ±20 V gate, AEC-Q101, TO-252, IDSS
1/50/150 µA at 25/125/175 °C, VDS=−60 V and VGS=0.
It fits the accepted hot QP allocation. The 1.5KE30A hot clamp screen is
43.80948 V (0.097 %/K), not 43.5 V; LM2678 would return to its working
keyless precedent, with 40 V operating / 45 V absolute and 1.19 V absolute
margin. That precedent is accepted, not dismissed.

The logger-specific reason for retaining the lower clamp is the new A5
supply: the unchanged 330 Ω/BZX55C22 stage screens 1.46 W under 43.81 V.
With 85 °C leads its rating is only 0.30 W. A resistor-only change cannot
both protect that shunt and preserve the 6 V dropout floor. A higher-power
or different A5 stage is possible; this return chooses the lower clamp's
10.80 V LM2678 operating margin and a bounded A5 resistor correction.
The ≥60 V BJT replacements and complete 30A redesign are not implemented
or presented as verified. The option comparison is in LAYOUT_CLOSURE §3.1/3.4.

**Changed part:** R_AON (R22) 330 Ω → **820 Ω/1%**, with procurement condition
≥0.15 W allowable at 85 °C in its existing footprint. BZX55C22 remains,
but its assessment now includes lead-temperature derating and junction
heating: ≤0.263 W, thermal screen Tj≤163.75 °C with leads≤85 °C;
voltage model ≤27.90 V. At P12=6 V, a 0.510 mA input-current screen leaves
P_AON≥5.5776 V. Loaded input RC startup is 18.3 ms. These are conditional
screens, not bench qualification or a guaranteed large-signal zener curve.
The zener leakage test voltage is corrected from 18 V to **16 V**.

**Exposure:** any sustained P12 above **17.1 V**, including an
**alternator/regulator overcharge fault** as well as a 24 V jump start,
is excluded. D-OVERVOLT-04 defers this as a named vehicle-acceptance risk.
This revision does not imply all voltages through 17.1 V meet parked-current
limits: the zener's published leakage screen ends at 16 V.

**Ledger:** manager-accepted redistribution is recorded; system targets stay
100/500 µA and the mixed-condition screens stay 74.98/452.65 µA. QP remains
1/70 µA. The original “180 µA freed from 200” was an arithmetic error:
200−70=130 µA. Electrical/assembled acceptance remains open.

**UUIDs:** a fixed UUID5 namespace plus stable source designator and element
role gives symbol and pin identity independent of drawing position, BOM
order, value and numeric reannotation. Graphics use deterministic geometry
keys. Root identity is fixed. This is a one-time replacement of the old
random IDs; an already-created PCB linked to those IDs would require deliberate
reassociation once. Future generated files retain identity. The generator
still owns the schematic and does not write the PCB.

Commands and evidence: `kicad/validation/COMMANDS.txt`; both generators,
ERC with `--severity-all`, netlist and SVG export, `check_capture.py`,
`fp_area.py`, `power/check_layout_closure.py`, and the added
`tools/check_uuid_stability.py` were run.

| Check | Result |
|---|---|
| Consecutive schematic generation | byte-identical; SHA256 `6dbdd785955f6332bae98439328e57ad8609839daf0031cc731f936b9dd0dd7a` |
| UUID regression / uniqueness | passes; 1383 unique UUIDs |
| ERC, KiCad 9.0.2, JSON count | 0 violations at severity-all |
| Capture | 652/652 |
| Footprints / courtyard allowance | 141/141, 1.52× on 80 × 120 mm |
| Closure | 63/63, zero allocation overruns with accepted redistribution |

All scope changes are under the packet's permitted paths. Generated CSV
CRLF and SVG trailing whitespace are retained. No bench work, wiring,
purchase, deployment, firmware or database change occurred.

Still open: manager review of this explicit lower-clamp tradeoff; owner
layout and schematic visual review; R_AON hot-rated procurement and zener
lead-temperature condition; measured A5 clamp/startup/dropout; all original
vehicle, leakage, waveform, fuse and firmware acceptance gates not superseded
above. The ≤28 V zener result extrapolates small-signal impedance and must
not be treated as a manufacturer's DC guarantee. No new vehicle exposure
acceptance is claimed. Main and the original engineer's worktree are untouched.

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


### Revision LRA-12R, R12-REV-4 follow-up — October 29, 2026

Codex `logger-electrical`, session `01a18a47-2dc2-7aa3-a0d2-a4978e2b1ebc`.
Resume: `codex resume 01a18a47-2dc2-7aa3-a0d2-a4978e2b1ebc`.
Same branch `task/LRA-12R-01a18a47`; follows REV-1–3 commit
`50d93c815ca4eac6a1536841a630f123b42f7394`. Scope added by manager packet on
main at `6f54be7`, and owner approved the interim four-position connector.

**Delivered:** onboard keyless RS-485, replacing the passive J3 provision.
The keyless schematic was exported read-only and its U5 pin map and all
RS-485 footprints checked. Logger U15/U485 is MAX3485EPA+ in the same
DIP-8 socket footprint, C24 is the same 0805 100 nF, and R_DE retains the
same 10 k axial pulldown. GP8 TX, GP9 RX and GP10 tied DE//RE connect only
to the onboard circuit. No unreachable-shutdown current claim remains.
R47/R48 use 390 Ω per direction (keyless schematic 270 Ω versus PCB 390 Ω
is recorded without editing keyless). R49 and JP2 retain 120 Ω selectable
termination with the same footprints. Added JP3/JP4 isolate both bias legs.
All three headers are fitted **without shunts** by default.

J3 is now four pins: B5/PGND/switched-3V3/GP13. Interim J6 is a four-position
Mini-Fit Jr 39-30-1040: 1 A, 2 B, 3 PGND bus return, 4 NC. It does not use
B16/AGND. Owner connector consolidation is separate; no placement work was
done. No A/B TVS is added, matching keyless.

Switched 3V3 does not eliminate external-bus exposure. The conditional
bus-side screen is up to 2.0 mA total with both A/B at +12 V (or 1.6 mA
magnitude at −7 V), outside the 2/5 µA allocation. If the high bias is
linked, a stiff external A line can additionally inject 8.55 mA at 3.3 V,
or 31.08 mA / 0.373 W at 12 V into a held-dead rail. Default-open bias
removes that resistor path, not MAX3485 input current. No dead-rail voltage
or zero-injection guarantee is inferred. These are explicit bench/vehicle
gates in `communications/REV_A_PROVISION.md`; the earlier 74.98/452.65 µA
screen applies without an energized external bus. Final node count, idle
margin, jumper ownership and bus waveform remain acceptance work.

The ERC `lib_symbol_mismatch` was a generator flattening issue: KiCad
inherits a parent's footprint when the derived footprint is empty. The
library resolver now does the same; no ERC exclusion was added, and the
placed MAX3485 footprint stays DIP-8 as requested.

| Final rerun | Result |
|---|---|
| Both generators, two consecutive schematic runs | byte-identical; SHA256 `bbfcba624c1ab658f25690dfadf0b9ae56eebc7b105e4850ddfb581423e74dd6` |
| ERC JSON, KiCad 9.0.2, severity-all | 0 violations |
| Capture, including pin maps, footprints and open/closed jumper paths | 711/711 |
| Closure, including conditional external bus currents | 67/67, zero allocation overruns |
| Footprints / fitted courtyard / allowance | 150/150; 6759 mm²; 1.42× on 80 × 120 mm |
| UUID identity regression | passes; 1459 unique UUIDs |

Netlist and SVG exports were refreshed; exact commands are in
`kicad/validation/COMMANDS.txt`. The preceding 141-part counts and passive
communications statements are historical. Existing component UUIDs remain
stable across this addition. All original REV-1–3 thermal/vehicle limitations
remain. No hardware, firmware, deployment, purchase or keyless edit occurred.
Per the final owner instruction, this return ends after commit and push;
connector consolidation and further tasks are not undertaken.
