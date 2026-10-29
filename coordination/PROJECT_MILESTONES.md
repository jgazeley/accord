# Accord — current status and task authority

Prepared October 28, 2026 by Codex `pcb-manager`, session `01a17045-1855-7af2-b76a-32c2b778cd64`. Historical bookmark: `codex resume 01a17045-1855-7af2-b76a-32c2b778cd64`. Successors use their own identities.

October 29, 2026 update by Codex `pcb-manager`, session `01a18447-07c2-7bb3-8318-9b276cfdb3b8`
(`codex resume 01a18447-07c2-7bb3-8318-9b276cfdb3b8`). Identity verified from
matching `CODEX_SESSION_ID` and `CODEX_THREAD_ID`. That shift ended mid-integration.

October 29, 2026 preceding handover: the manager was Claude `pcb-manager`, session
`630dea87-5e4d-4bad-a1ff-d41b3a5f509b`
(`claude --resume 630dea87-5e4d-4bad-a1ff-d41b3a5f509b`). Identity read from this
session's harness-assigned working paths and confirmed against its transcript
file. The predecessor bookmarks above are historical attribution.

October 29, 2026 resumption: Codex `pcb-manager`, session
`01a18447-07c2-7bb3-8318-9b276cfdb3b8`
(`codex resume 01a18447-07c2-7bb3-8318-9b276cfdb3b8`), resumes at the owner's
request after the Claude shift. Identity re-verified from matching session/thread
environment values. Active scope: root/coordination and reviewed LRA-11
integration; audit the missing electrical capture against existing power sources.
No specialist is assumed still active. No transcript/history reconstruction.

This is the **single active project task tracker**. Owner direction, October 28:
new work and coordination start in `jgazeley/accord`; `accord-logger` becomes a
historical reference and a source of missing material. Old runtime locations
remain in use until separately migrated. Do not maintain another active tracker.

## Current snapshot

- **Priority:** a safe, testable logger Rev A PCB replacing breadboard wiring,
  with autonomous power and a reasonable RS-485/CAN expansion path.
- **Working, recorded hardware evidence:** configured logger v0.8.1-dev, Pico-only
  SD acquisition and ignition-off Wi-Fi delivery; owner-confirmed Pi-disconnected
  road legs. Pi 4 is the portable flashing/observation bench under manual power.
  Full unattended power and vehicle acceptance remain open.
- **Working deployment, read-only status checked Oct 28 20:24 UTC:** VM receiver
  running, guarded intake healthy, no admission holds/source errors, dashboard
  current. This is heartbeat evidence, not a new hardware test or DB audit.
- **Public source complete so far:** keyless firmware/KiCad, logger firmware,
  raw receiver/canonical conversion, tests and deployment templates (`8261314`).
  Public extraction did not change installed firmware or live services.
- **Power continuation baseline:** owner reaffirmed October 28: reuse the existing
  `9527a14` circuit; no fresh topology research without a specific demonstrated
  gap. Manager located ten unchanged engineering/continuation files and reran
  all 19 conditional checks successfully. The reviewed
  [power export](../logger/hardware/power/README.md) now contains the existing
  candidate, BOMs, handoffs and scripts with provenance; private access is not
  required for LRA-01 review.
- **First blockers to resolve:** qualify the opt-in firmware's shutdown/reset
  behavior and close the cutoff candidate's power-budget/protection/isolation gaps.
- **Next action:** LRA-05 `0745d5b` reviewed/integrated as an opt-in firmware
  candidate; manual power remains default. Nine native suites, 12 converter
  cases, 44 power checks and both dummy builds pass independently. The masked-
  interrupt/watchdog release-bound limitation remains an acceptance blocker;
  see [LRA-05 review](reviews/LRA05_REVIEW_2026-10-29.md). LRA-03 is **integrated**
  at `dc07292`: the revised return `f23e51c` applied all six findings of the
  [review](reviews/LRA03_REVIEW_2026-10-29.md), and the merge adds a documentation
  reconciliation only. The consolidation is now the documented baseline for
  LRA-06. An LRA-04 browser return arrived the same day and is **reviewed,
  revisions required**; see [that review](reviews/LRA04_REVIEW_2026-10-29.md). Analog acceptance, electrical R02–R05 and physical acceptance
  remain open.
- **Authority:** Claude `pcb-manager`, session `630dea87-5e4d-4bad-a1ff-d41b3a5f509b`,
  owns root/coordination from October 29 and integrated LRA-03. Codex
  `pcb-manager`, session `01a18447-07c2-7bb3-8318-9b276cfdb3b8`, held the role
  before it and completed the firmware and LRA-01/02/03/05 reviews. LRA-01/02/05
  returns: Codex `logger-power`, `01a18463-5ed7-7041-ad90-ec3a7480c4e6`.
  LRA-03 return: Claude `hardware-integrator`,
  `23d6d0fb-9656-4e03-acb3-922537019a5b`. Follow-up implementation and
  communications claims remain unacknowledged; receipt does not imply an agent
  is still running.

## Milestones (existing IDs retained)

| ID | Outcome | Present disposition |
|---|---|---|
| M1 | Reliable capture and canonical trip record | Operational evidence exists; clock/reset/storage fault coverage and historical corrections remain |
| M2 | Autonomous logger power | Candidate design only; LRA-01/02/05/07 |
| M3 | Automatic Pi-free data path | VM guarded intake delivered; production-host migration and parallel feed separate |
| M4a | Manually powered Pi-free trial | Road capture/upload demonstrated; explicit keyless independence/repeatability remains |
| M4 | Fully unattended Pi retirement | Open; requires accepted power/data lifecycle and keyless/bus disposition |
| M5 | Logger design ready for prototype order | Rev A task graph below; order approval separate |
| M6 | Assembled board accepted | Future staged bring-up and vehicle acceptance |

Fuel calibration, dashboard improvements, future modules and a complete CAN
implementation are not M5 prerequisites unless they identify a concrete hardware
requirement. Do not import every historical proposed signal into Rev A.

## Task graph — roles are owners; sessions are replaceable claimants

State: ready / active / blocked / candidate / accepted / deferred. `Active`
requires an acknowledged claimant and date. Candidate is not deployed/accepted.
LRA-01 electrical claim and returned candidate are recorded below. Other
specialist claims remain unacknowledged. Every row requires a
task packet before dispatch; record the claim and evidence here, not in a second tracker.

| ID | Responsible role | State / dependencies | Outcome and acceptance |
|---|---|---|---|
| [LRA-01](handoffs/LRA-01_POWER_INTERFACE.md) | Electrical lead; firmware reviewer; manager integrates | Reviewed candidate `a85f185`; R01 disposition delivered by manager `01a18447-07c2-7bb3-8318-9b276cfdb3b8` in FIRMWARE_REVIEW.md; suitable for isolated 05 implementation, electrical/bench gates open | One agreed qualified-IGN/HOLD/startup/shutdown/reset/USB contract; numerical assumptions and faults explicit; current/protection decisions and reviewer disposition |
| [LRA-02](handoffs/LRA-02_COMPONENT_MARGINS.md) | Electrical return by logger-power `01a18463-5ed7-7041-ad90-ec3a7480c4e6` | Candidate `c946f6f`, bounded paper return reviewed/integrated; R03/R04 remain open, no accepted consolidated BOM | Coherent power schematic/BOM, compatible protection, effective capacitance and current/leakage allocations; off-state paths and bench checklist |
| [LRA-03](handoffs/LRA-03_AS_BUILT.md) | Returned by Claude hardware-integrator `23d6d0fb-9656-4e03-acb3-922537019a5b`; analog acceptance open | **Integrated** October 29 at `dc07292`. First return `a9c828b` reviewed, revisions R03-REV-1–6 applied in `f23e51c`, merge adds a documentation reconciliation. Baseline for LRA-06; accepts no hardware | Current as-built consolidated with unknowns, frozen Rev A pins/connectors/input loading/protection/grounds/mechanics/test points; no full fuel model |
| [LRA-04](handoffs/LRA-04_COMMUNICATIONS.md) | Browser return, session identifiers unavailable; hardware/firmware accept | **Returned, revisions required.** Owner-supplied browser return preserved at `logger/coordination/LRA04_GROK.md`; [review](reviews/LRA04_REVIEW_2026-10-29.md) records five standing findings, two of them contradictions in the proposed topology; a sixth was withdrawn as the reviewer's error, not the return's. No bus selected, no pin reserved, nothing integrated | RS-485/CAN/daughterboard comparison with usable GPIO/peripheral/current/voltage/power-off contract; recommendation and fallback |
| [LRA-05](handoffs/LRA-05_FIRMWARE_POWER.md) | Returned by logger-power `01a18463-5ed7-7041-ad90-ec3a7480c4e6`; manager reviewed | Candidate `0745d5b` integrated October 29; manual default, opt-in qualified mode. Masked-IRQ release-bound analysis and physical qualification remain open; no active follow-up claimant | Isolated shutdown candidate: early HOLD, bounded SD finalization, IGN-return/reset/watchdog behavior; build/fault/replay tests and rollback; no implicit flash |
| [LRA-06](handoffs/LRA-06_SCHEMATIC_CAPTURE.md) | Returned by Claude `logger-schematic` `73d7d954-f82a-4038-8ff3-546a23fc5fa9` | **Integrated onto `main`** October 29; electrically sound as drawn. Candidate `c66fba6`, merged so the accepted capture is visible in the default checkout rather than only on its task branch. `logger/hardware/kicad/accord-logger.kicad_pro`. Integration of a reviewed candidate, **not a freeze**. [Review](reviews/LRA06_REVIEW_2026-10-29.md): R06-REV-1 (B16 orphaned from the ADC return), REV-3 and REV-4 (input TVS reversed) all closed and independently verified — 14/14 diode polarities correct, ERC 0, 224/224 checks, and the new orientation-opacity guard tamper-tested by reversing the TVS in a copy of the netlist. Both blocking findings shared one root cause: checks asserting the symbolic record instead of the physical fact. **Not integrated or frozen.** R06-REV-2 is with the electrical lead and blocks a freeze: bonding B16 put the opto LED cathode on the ADC return node, so D5 and the fitted LED return cannot both stand. Owner's GUI legibility pass outstanding; this host has no rasterizer | Consolidated schematic/export/BOM, pin/part/footprint checks and ERC dispositions; explicitly unpopulated options |
| LRA-07 | Local bench role; owner operates hardware | Blocked on testable 02/03 circuit and authorized bench setup; combined tests use 05 | Measured rails/startup/cutoff/reset/USB/energized-input-with-board-off results; conditions, limits, exceptions and artifacts |
| LRA-08 | PCB layout owner, unclaimed | **Envelope resolved, no longer blocked on U-11.** Baseline is the integrated capture at `logger/hardware/kicad/`; outline is a generic 80 × 120 mm rectangle per `D-ENVELOPE-01`. **Now blocked on [LRA-11](handoffs/LRA-11_B2_OFFSTATE_ISOLATION.md)**, which resolves D4 for X1, and on the four placeholders under analog review. Resolve R06-REV-2 and any LRA-07 material changes before release. No packet written yet | Placement/routing, returns/current loops, antenna keepout, connectors, SD/USB access, mechanical review, DRC/parity dispositions |
| LRA-09 | Manager and independent reviewer | Blocked on 06/07/08; 05 interface feasibility/bring-up path | Frozen prototype-order review package, hashes, BOM, test restrictions and residual-risk matrix; owner approval still required |
| LRA-10 | Local bench/firmware | Blocked on 09 and owner order/assembly/testing authorization | Actual-board bring-up evidence, then separate unattended-vehicle acceptance |
| [LRA-11](handoffs/LRA-11_B2_OFFSTATE_ISOLATION.md) | Returned by Claude `analog-isolation`; **session ID genuinely unavailable** (ran as a subagent; declined to borrow or invent one, which is correct). **No resume bookmark exists** — re-dispatch as a top-level session if one is needed | **Returned, recommendation accepted as a candidate.** `d8a67f7` on `task/LRA-11-analog-isolation`. [Review](reviews/LRA11_REVIEW_2026-10-29.md). Recommends **Broadcom ASSR-601JV** photo-MOSFET relay in the B2 top leg, LED from switched B5. Verified independently: it corrected two of the manager packet's own numbers and both corrections are right. **Its most valuable result is not the part** — clamp-topology changes are dead on every branch, because the back-feed diode is the RP2040's own pin-to-IOVDD ESD structure, which closes rows 1–5 of §6. **R11-REV-1:** requirement 7 is not met as written — MAX_ON is unimplemented and even implemented its ARM gates only the QH branch, so BAD cannot drop B5 with ignition present; but a B5-fed LED tracks board power by construction, which may be the better reading. Electrical lead to rule. **Gating integration:** the leakage spec rests on a reading of Broadcom's table convention, not an explicit statement, and that exact distinction killed two rejected candidates. Availability checked and fine; the JV is the automotive variant | Selected part or topology with datasheet-backed evidence, enable path, failure behaviour, fallback and a placeable package |

Critical path: 01 → 02 and 05 → 07 → 09; in parallel 03 + 04 → 06 → 08 → 09.
**As of October 29 the live critical path is `11 → 08 → 09`.** LRA-06 is integrated and the envelope is
fixed, so LRA-11 is the only thing standing between here and layout.
One agent may perform successive responsibilities; do not create sessions merely
for every row. Remote electrical work and local physical validation are distinct.

### Other workstreams — do not silently expand the PCB gate

| ID | Role | State / next evidence |
|---|---|---|
| OPS-01 | Manager/bridge/DB | Operational monitoring; automation already delivered. Keep old runtime/data intact; investigate concrete errors only |
| DATA-01 | DB owner | Ready for audit, claimant unknown: historical wrong-date/fill-entry corrections. Current completion not independently established; no duplicate reimport |
| FUEL-01 | Fuel analyst | Prepared post-fill assignment, successor delivery unverified. Existing data can support analysis; personal fixtures stay private |
| STORE-01 | Logger/bridge | Ready: inspect actual capacity and define rotation/verified-retention policy; no automatic deletion currently |
| TIME-01 | Logger/bridge | Deferred design: reset/offline time and retrospective drift policy; hardware reservations feed 03/04 if concrete |
| KEY-02 | Keyless role | **Dead reference fixed; import still optional and unclaimed.** The sketch now states once that `cm5sim` is the host-side CM5 stand-in, reached through `hp`, and is not part of this repository, so no reader chases a file that is not here. The stale "no MAX3485 fitted" / "once U5 is soldered" / "needs U5 fitted" comments are corrected in the same pass. Importing the tooling itself remains optional: nothing is blocked, the logger has no RS-485 today, and it becomes a real need only at LRA-07 bench work or if Rev A puts a bus on the logger. See `D-KEYLESS-485-01` |
| KEY-01 | Proximity/keyless | Owner participation required: threshold/repeatability and parked operation independent of Pi/logger; installed settings unknown |
| DIST-01 | Bridge/DB | Deferred: production-host cutover, packet checkpoints and independent server/VM comparison; not yet implemented |
| DOC-01 | Claude pcb-manager, `630dea87-5e4d-4bad-a1ff-d41b3a5f509b` | Active manager from October 29. LRA-01/02/05 reviewed and integrated as candidates by the predecessor session; LRA-03 revised return reviewed and integrated at `dc07292`. LRA-04 browser return triaged: revisions required, not integrated. LRA-06 dispatched, claimed, returned and reviewed October 29: candidate `5fb1598`, revisions required, R06-REV-2 escalated to the electrical lead. Owner's U-10/U-08/U-14/U-07 measurements recorded the same day as `D-OFFSTATE-01`. **Next:** the corrected LRA-04 pass, R06-REV-2, the owner's U-11 envelope which blocks LRA-08 outright, and a GUI legibility pass on the schematic that this host cannot perform. No automatic-power deployment accepted |

## Decisions and gates

- **D-POWER-03 — owner correction, October 29:** the logger power front end is
  **not new work**. The keyless board already carries it, on a permanent 12 V
  body-harness feed, in the car, surviving cranking, and it was designed from
  study of the original Honda keyless PCB. Verified from
  `keyless/hardware/hondaPico.kicad_sch` by `kicad-cli` BOM export:

  | Block | Keyless, in service | Logger candidate | |
  |---|---|---|---|
  | Regulator | U3 LM2678T-5.0 | UREG LM2678T-5.0/NOPB | identical |
  | Input TVS | RV20 **1.5KE30A** | TVS **1.5KE30A-E3/54** | identical |
  | Output bulk | C30 820 µF 16 V | COUT 820 µF/16 V | identical |
  | Input bulk | C20 100 µF 50 V | CIN 100 µF/50 V | identical |
  | Boost | C15 10 nF | CBOOST 10 nF/50 V | identical |
  | Inductor | L1 22 µH 2 A, D10.0 | L1 22 µH Bourns RLB0912, D8.7 | same value, **keyless part is larger** |
  | Catch | D30 SS34 / STPS5L60 3 A | DCATCH SB360-E3/54 3 A | equivalent |
  | Reverse block | D20 1N5822 3 A | DREV SB360-E3/54 3 A | equivalent |

  **The delta is only the autonomous switching** — QP, QI/QH, DZ, DOR and the
  MAX_ON logic — which keyless does not need because it never turns off. The
  supply itself is the same circuit with the same parts.

  **Consequences.**
  1. **R02 is better supported than the record says.** `BOM.csv` marks the TVS
     `CANDIDATE_NOT_VEHICLE_APPROVED` and "inherited protection candidate only".
     It is the same part, in the same role, on a board that has taken cranking
     transients in this vehicle. That is not a logger qualification — different
     board, layout and load — but it is in-vehicle evidence, not inheritance,
     and R02 should be reframed as *qualify the delta* rather than *choose a
     protection scheme*.
  2. **Keyless protects its signal lines and the logger does not.** Seven
     **P6KE30A** sit on the keyless harness lines; the logger has none, and the
     owner reports four P6KE30A on hand. A direct template for the logger input
     protection, and an input to R02.
  3. **The permanent-12 V question is already answered in the family.** Keyless
     runs exactly the architecture the owner is considering for the logger.
  4. **Check the inductor against keyless before trusting the logger BOM note.**
     The logger row warns its RLB0912 saturation is below the LM2678 fault
     limit. Keyless runs a physically larger 2 A part at the same 22 µH in the
     same role; the comparison is worth making rather than re-deriving.
  5. Keyless carries **both** connector families in service — a Molex Mini-Fit
     Jr 16P body harness and the JAE IL-AG5 22P experiment — so both are
     already proven in this car.
- **D-ENVELOPE-01 — owner decision, October 29:** the Rev A board is a
  **generic rectangle, 80 × 120 mm**, with **no enclosure** and no mounting
  method chosen. Mounting behind the gauge cluster was considered and set
  aside. It carries the Pico module, the SD module and the remaining
  circuitry. The SD module occupies **16 × 16 mm** plus
  `PinHeader_1x06_P2.54mm_Vertical`.
  **This closes U-11 for layout purposes.** The owner first offered the present
  bench footprint as a size reference — an 82 × 55 mm half-size breadboard plus
  a 46 × 36 mm mini — and that was too small, because those breadboards carry
  only the as-built. Rev A adds the whole onboard power block, twenty test
  points and eight placeholders. Nominal package areas over the 81 captured
  parts with footprints give **5,031 mm²** raw, so a 1.6–2.0× routing allowance
  wants 8,000–10,000 mm². **80 × 120 is 9,600 mm², a 1.9× allowance**, which
  clears the floor with margin for a through-hole two-layer board. Ten parts
  — J1, J2 and the eight placeholders — are still unassigned and will eat into
  that, so the margin is real but not generous.
  **Consequences:** connector positions become LRA-08's choice rather than an
  owner input, and LRA-08 should place generic corner mounting holes that
  commit to no particular mounting method. **Residual and non-blocking:**
  mounting method and harness lengths.
- **D-OFFSTATE-01 — owner measurement, October 29:** key out and parked, to
  chassis ground: **B2 (VSS) = 4.140 V, B1 (tach) = 0 V, C11 (fuel) = 0 V**.
  This closes U-10 and changes the biggest Rev A design item. **B2 is the only
  one of the five vehicle branches that is energized while the car is parked**;
  C14 and B11 were already recorded dead with the key out. Through B2's fitted
  22k/33k divider, 4.140 V is **75.3 µA** — on its own, nine times the 8/20 µA
  allocated to all five branches and three quarters of the entire 100 µA
  whole-system parked budget. So isolation is still required, but **D4 narrows
  from five branches to one**, and that one is a digital pulse input rather than
  an analog channel. If the analog reviewer agrees C11 and B11 need no switch,
  the ≤25 Ω fuel and ≤100 Ω supply top-leg limits disappear along with the
  card-header calibration problem in REV_A_INTERFACES §8.2. **Open:** whether
  4.140 V was read loaded or open-circuit is **answered the same day**: the owner
  lifted the VSS wire and read **4.669 V** open-circuit against 4.140 V loaded.
  So injection is real rather than an upper bound, and B2 is held up by an
  always-on pull-up to about 4.67 V through **3,757 Ω**.
  **All readings share one configuration**, which the owner confirmed: dividers,
  clamps, Pico module and SD module all seated, the Pico unpowered with the USB
  lead off. Four readings now close the branch with nothing assumed — 4.669 V
  open-circuit, 4.140 V at the tap loaded, **1.042 V at the 22k/33k junction**
  and 0.883 V on the clamp cathodes:

  - B2 draws **140.8 µA**, of which **109.2 µA is back-fed through a
    forward-biased clamp into the Pico's own 3V3 rail** and only 31.6 µA
    reaches ground through the 33k. **The board is partially energized while
    parked.**
  - That one branch is **141 % of the entire 100 µA whole-system parked
    budget** and **17.6×** the 8 µA allocated to all five together.
  - The clamp drop is **159 mV at 109 µA** — a Schottky value, which
    corroborates the 1N5819 the record claims and gives **U-07** its first
    measured point. It does not close U-07, and because V<sub>F</sub> keeps
    falling below 109 µA, **D11's clamp margin is smaller than estimated**.
  - REV_A_INTERFACES §6 says nothing in its off-state matrix is established.
    The B2 row now is, and it fails.

  **Three earlier figures are superseded and must not be requoted:** 75.3 µA
  (assumed the divider was the only load), 7.03 kΩ (assumed the clamp was off),
  and the 134–141 µA / 3.8–3.9 kΩ ranges (assumed a clamp drop now measured).
  Do not re-ask any of the four readings.
- **D-KEYLESS-485-01 — owner statement, October 29:** the keyless board **has a
  MAX3485 fitted, in an IC socket**, and the **RS-485 link was tested
  extensively** from the Pi 4 using a host CLI — `./hp out lock pulse`,
  `./hp io`, `./hp status`. This is operational bus evidence, not a designed
  precedent. Do not re-ask whether the part is present or whether the bus ran.
`keyless/firmware/accord-keyless/accord-keyless.ino` said "no MAX3485 fitted"
  and "once U5 is soldered"; **corrected October 29 on owner instruction**, with
  the manifest hash, adjustment record and a clean rebuild. The `cm5sim`
  docstring at the bench still carries the same stale line and is outside this
  repository. `D14` still owns the equivalent logger sketch comment.
  **Migration gap:** the host tooling never came across. `hp` and `cm5sim` live
  at `/srv/agent_share/pcb/benchlink/`, and the migrated firmware references
  `cm5sim` four times as the counterpart a reader should run, so the public
  repository documented a tool it does not contain. **Fixed October 29**: the
  sketch header now says once what `cm5sim` is and that it lives outside this
  repository. Importing the tooling blocks nothing. Task `KEY-02`.
  Socketing is a Rev A input — vibration and contact resistance
  for the electrical reviewer, and a real but unguaranteed disconnection
  measure for the off-state question.
- **D-INVENTORY-01 — owner clarification, October 29:** the original reference is
  `/srv/agent_share/inventory/inventory_list.md`; the historical logger-power
  copy is not the primary inventory. The original is mostly accurate but
  incomplete, and some listed parts may have been consumed. Owner additionally
  reports **four P6KE30A diodes**, absent from that list. Reconcile exact available
  project stock later during parts discussions; an inventory audit is not a
  prerequisite for current documentation/design work. Stock does not establish
  electrical suitability or authorize a BOM substitution. Keep the full inventory
  private unless a selected export is separately reviewed for publication.
- **D-RA-01 — owner direction:** prioritize integrated-power Rev A; fuel curve,
  dashboard and future-network completion do not gate it.
- **D-RA-02 — planning distinction:** prototype fabrication recommendation,
  assembled-board bring-up, and unattended vehicle approval are separate gates.
  Exact numeric acceptance/test envelope must be agreed, not inferred here.
  Old universal pre-PCB vehicle-duty wording is historical; this is not permission
  to fabricate an electrically unresolved design.
- **D-RA-03 — reviewed candidate 01:** use the shared qualified-IGN/deadline
  contract and FIRMWARE_REVIEW for isolated implementation; runtime/electrical
  acceptance remains open. Never mix
  the old raw-GP5/100 ms rules with the newer analog-qualified proposal.
- **D-ASBUILT-01 — owner reminder, October 28:** the logger already has a physical
  as-built circuit documented outside KiCad. LRA-03 consolidates those corrected
  records first; LRA-06 captures the reviewed baseline and explicit Rev A changes.
  Keep fitted logger wiring, keyless examples and the automatic-power candidate
  distinct. Exact source sections and current connections are in the LRA-03 packet.
- **D-REUSE-01 — owner direction, October 28:** consult the existing `hondaPico`
  keyless circuit and working examples before designing equivalent logger blocks.
  References: `keyless/hardware/hondaPico.kicad_sch`, matching PCB and firmware,
  and `keyless/validation/kicad-20261027/README.md`. Reuse applicable knowledge;
  record actual fitted evidence and logger-specific differences. Keep the two
  modules' pin maps, power lifecycle and artifact ownership separate.
  **Sharpened October 29 by owner direction:** use the keyless project as a
  template for *conventions and naming* — project-relative `${KIPRJMOD}`
  library tables, one project-local `Custom` symbol library, a project
  `.pretty`, the test-point/reset-header pattern and the `kicad-cli` validation
  method — while the logger is a **separate, distinct board project** at
  `logger/hardware/kicad/accord-logger.*`. Copy the scaffolding and the
  `LM2678T-5.0` symbol, which the Rev A regulator reuses; copy no circuit. The
  keyless project keeps the filename `hondaPico.kicad_pro` per `AGENTS.md`; the
  new board taking a clean name is not a conflict with that and licenses no
  renaming on the keyless side. See `handoffs/LRA-06_SCHEMATIC_CAPTURE.md`.
- **D-POWER-02 — owner direction, October 28:** continue the existing `9527a14`
  power circuit. Reuse its design, BOMs and checks; limit new investigation to
  identified gaps. Replacement requires a documented defect or unmet requirement.
- **D-RA-04 — pending 04:** minimal communications provisioning; daughterboard
  is a valid alternative to evaluate, not a selected implementation.
- **D-REPO-01 — owner direction:** `accord` is authoritative for new active work;
  selectively recover historical material, preserve provenance; private deployment
  data remains private. No duplicate active tracker or parallel manager.
- **D-DATA-01 — established:** SD raw evidence → canonical converter/trip engine;
  public service stops at trip JSON. Guarded private DB intake remains separate.
- **D-POWER-01 — existing interim arrangement:** manual buck power and time sync
  before departure; no RTC, replacement RS-485 part or power-latch completion
  required to continue present logging. Automatic cutoff remains a Rev A goal.

For prototype recommendation require coherent schematic/BOM, compatible rails/
protection, no known destructive path within the declared envelope, critical
bench evidence or explicit unpopulated/isolation provisions, layout/rule review
and actionable bring-up. Remaining risks need safe restrictions and named tests.
Prototype label does not justify an incompatible clamp or unbounded backfeeding.
Long-duration vehicle qualification and complete future bus software can follow.

## Evidence and history

[Hardware/current uncertainties](../logger/hardware/REV_A_CONTEXT.md),
[migration/provenance map](MIGRATION_MAP.md), [task packets](HANDOFF_INDEX.md),
[public server validation](../logger/server/VALIDATION.md), logger/keyless
`SOURCE_MANIFEST.json` and keyless KiCad validation. Historical M1–M6 checkpoints
remain in old `coordination/PROJECT_MILESTONES.md` at `1e99449`; do not copy their
stale counts/assignments forward. Update this snapshot on material outcomes,
not every automated intake tick. Record accepted task commit/evidence here.

October 28 return triage by the current pcb-manager: read the electrical
[LRA01_HANDOFF](https://github.com/jgazeley/accord/blob/a85f185c4dfc593b0a5b7284170e904cbf8a54c1/logger/hardware/power/LRA01_HANDOFF.md)
and contract follow-up gates. Engineer reports 33 checks passing; manager has
not independently rerun or accepted this delivery. Branch remains unmerged.

October 28 integration review by the current pcb-manager supersedes the return
triage above: both original commits are preserved; [manager review](reviews/LRA01_LRA02_REVIEW_2026-10-28.md)
and [firmware disposition](../logger/hardware/power/FIRMWARE_REVIEW.md) are delivered.
The 44 model/arithmetic/integrity checks and eight existing native firmware
suites pass independently. This closes the missing written R01 review, not
implementation or bench acceptance. No new specialist is marked active.

October 29 review by the current pcb-manager: [LRA05_HANDOFF](../logger/coordination/LRA05_HANDOFF.md)
received at `0745d5be562f9b340fa467b8242f33fef25d2f76`; original commit preserved
on integration. [Review and evidence](reviews/LRA05_REVIEW_2026-10-29.md) supersede
prior statements that 05 is unimplemented/unclaimed. The acknowledged claim
covers this delivery, not an automatically continuing assignment.

October 29 LRA-03 review by the current pcb-manager: local first return
`a9c828bef0b5da1ab7192622f95575e8f2d33f52` received with the specialist's own
attribution. All 65 arithmetic checks and 17 pinned source hash/blob/size checks
pass, but model errors, contradictory fitted-status statements and unsupported
closure claims require revision. [Detailed findings and return instructions](reviews/LRA03_REVIEW_2026-10-29.md).
Original branch is preserved; no LRA-03 integration, new hardware action or
repeat owner inventory/part-count questioning is authorized by this review.

October 29 LRA-03 integration by Claude `pcb-manager`,
`630dea87-5e4d-4bad-a1ff-d41b3a5f509b`: merged `f23e51c` into `main` as
`dc07292`, preserving the engineer's authorship on both task commits and the
reviewed first return as `archive/reviews/LRA03-a9c828b`. The merge adds an
integration reconciliation drafted by the predecessor manager session and
repaired here; it changes prose, table wording and cross-references only, and no
asserted number moved. Re-verified on the merge result: 70 arithmetic checks, 44
power checks, 9 native suites, 12 converter cases, and the three deliverable
hashes recomputed in `SOURCE_MANIFEST.json`. Integration makes the consolidation
the documented baseline; it accepts no hardware, freezes nothing, and authorizes
no purchase, bench work or repeat owner questioning.

October 29 LRA-04 triage by Claude `pcb-manager`,
`630dea87-5e4d-4bad-a1ff-d41b3a5f509b`: an owner-supplied browser return against
the `eb33d17` packet is preserved verbatim at `logger/coordination/LRA04_GROK.md`
and reviewed in [reviews/LRA04_REVIEW_2026-10-29.md](reviews/LRA04_REVIEW_2026-10-29.md).
The survey is usable and its RS-485-primary direction is not rejected, but the
proposal both ties DE//RE and costs an unreachable shutdown mode, and it
recommends RS-485 as the best fit to the 2/5 µA allocation after recording a
powered-off bus current three orders of magnitude above it. Keyless RS-485 is a
designed and so-far unpopulated precedent, not operational evidence. The
corrected pass needs no bench access, purchase or new owner question. No bus is
selected and `D-RA-04` is unchanged.

October 29 LRA-04 correction by Claude `pcb-manager`,
`630dea87-5e4d-4bad-a1ff-d41b3a5f509b`: finding R04-REV-3 is **withdrawn**. The
return's "proven on keyless" was accurate; the review's two attempts to qualify
it were not. Both came from reading stale firmware comments as current fact,
which is the exact error the LRA-04 packet warns against and which the review
quoted while committing. The owner's October 29 statement and the surviving
`hp`/`cm5sim` tooling establish an exercised 115200 bus with a real
request/response protocol and a worked half-duplex DE implementation at
`keyless/firmware/accord-keyless/link.h:221`. The keyless precedent is
operational evidence and the strongest argument for the RS-485 recommendation.
Firmware comments in this project date from when they were written; the owner
is the authority on what is physically built and run.
