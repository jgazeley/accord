# Accord — current status and task authority

Prepared October 28, 2026 by Codex `pcb-manager`, session `01a17045-1855-7af2-b76a-32c2b778cd64`. Historical bookmark: `codex resume 01a17045-1855-7af2-b76a-32c2b778cd64`. Successors use their own identities.

October 29, 2026 update by Codex `pcb-manager`, session `01a18447-07c2-7bb3-8318-9b276cfdb3b8`
(`codex resume 01a18447-07c2-7bb3-8318-9b276cfdb3b8`). Identity verified from
matching `CODEX_SESSION_ID` and `CODEX_THREAD_ID`. That shift ended mid-integration.

October 29, 2026 handover: the current manager is Claude `pcb-manager`, session
`630dea87-5e4d-4bad-a1ff-d41b3a5f509b`
(`claude --resume 630dea87-5e4d-4bad-a1ff-d41b3a5f509b`). Identity read from this
session's harness-assigned working paths and confirmed against its transcript
file. The predecessor bookmarks above are historical attribution.

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
| [LRA-04](handoffs/LRA-04_COMMUNICATIONS.md) | Browser return, session identifiers unavailable; hardware/firmware accept | **Returned, revisions required.** Owner-supplied browser return preserved at `logger/coordination/LRA04_GROK.md`; [review](reviews/LRA04_REVIEW_2026-10-29.md) records six findings, two of them contradictions in the proposed topology. No bus selected, no pin reserved, nothing integrated | RS-485/CAN/daughterboard comparison with usable GPIO/peripheral/current/voltage/power-off contract; recommendation and fallback |
| [LRA-05](handoffs/LRA-05_FIRMWARE_POWER.md) | Returned by logger-power `01a18463-5ed7-7041-ad90-ec3a7480c4e6`; manager reviewed | Candidate `0745d5b` integrated October 29; manual default, opt-in qualified mode. Masked-IRQ release-bound analysis and physical qualification remain open; no active follow-up claimant | Isolated shutdown candidate: early HOLD, bounded SD finalization, IGN-return/reset/watchdog behavior; build/fault/replay tests and rollback; no implicit flash |
| LRA-06 | KiCad schematic owner | Blocked for freeze on 01–04; known-block capture may start | Consolidated schematic/export/BOM, pin/part/footprint checks and ERC dispositions; explicitly unpopulated options |
| LRA-07 | Local bench role; owner operates hardware | Blocked on testable 02/03 circuit and authorized bench setup; combined tests use 05 | Measured rails/startup/cutoff/reset/USB/energized-input-with-board-off results; conditions, limits, exceptions and artifacts |
| LRA-08 | PCB layout owner | Blocked on 06 baseline; resolve 07 material changes before release | Placement/routing, returns/current loops, antenna keepout, connectors, SD/USB access, mechanical review, DRC/parity dispositions |
| LRA-09 | Manager and independent reviewer | Blocked on 06/07/08; 05 interface feasibility/bring-up path | Frozen prototype-order review package, hashes, BOM, test restrictions and residual-risk matrix; owner approval still required |
| LRA-10 | Local bench/firmware | Blocked on 09 and owner order/assembly/testing authorization | Actual-board bring-up evidence, then separate unattended-vehicle acceptance |

Critical path: 01 → 02 and 05 → 07 → 09; in parallel 03 + 04 → 06 → 08 → 09.
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
| KEY-01 | Proximity/keyless | Owner participation required: threshold/repeatability and parked operation independent of Pi/logger; installed settings unknown |
| DIST-01 | Bridge/DB | Deferred: production-host cutover, packet checkpoints and independent server/VM comparison; not yet implemented |
| DOC-01 | Claude pcb-manager, `630dea87-5e4d-4bad-a1ff-d41b3a5f509b` | Active manager from October 29. LRA-01/02/05 reviewed and integrated as candidates by the predecessor session; LRA-03 revised return reviewed and integrated at `dc07292`. LRA-04 browser return triaged: revisions required, not integrated. Next: the corrected LRA-04 pass, electrical gap closure, bounded LRA-05 timing follow-up and the LRA-06 start condition. No automatic-power deployment accepted |

## Decisions and gates

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
