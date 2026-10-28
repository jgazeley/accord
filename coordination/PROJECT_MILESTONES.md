# Accord — current status and task authority

Prepared October 28, 2026 by Codex `pcb-manager`, session `01a17045-1855-7af2-b76a-32c2b778cd64`. Historical bookmark: `codex resume 01a17045-1855-7af2-b76a-32c2b778cd64`. Successors use their own identities.

October 28, 2026 update by Codex `pcb-manager`, session `01a18447-07c2-7bb3-8318-9b276cfdb3b8`.
Current manager bookmark: `codex resume 01a18447-07c2-7bb3-8318-9b276cfdb3b8`.
Identity verified from matching `CODEX_SESSION_ID` and `CODEX_THREAD_ID`.

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
  all 19 conditional checks successfully; see the LRA-01 packet. Selected export
  is still required before remote detailed review.
- **First blocker to resolve:** one qualified-IGN/HOLD/shutdown contract and
  the cutoff candidate's power-budget/protection gaps.
- **Next action:** electrical lead claims [LRA-01](handoffs/LRA-01_POWER_INTERFACE.md);
  logger-firmware reviewer separately acknowledges review. Manager source triage
  is available in the packet. LRA-03/04 packets are prepared for parallel claims.
- **Authority:** Codex `pcb-manager`, session `01a18447-07c2-7bb3-8318-9b276cfdb3b8`,
  claims root/coordination on October 28, 2026. Predecessor remains historical.
  No electrical, firmware, hardware-integrator or communications specialist has
  acknowledged a current claim; preparation is not dispatch or acceptance.

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
No LRA task has an acknowledged specialist claimant at this manager takeover. Every row requires a task packet
before dispatch; record the claim and evidence here, not in a second tracker.

| ID | Responsible role | State / dependencies | Outcome and acceptance |
|---|---|---|---|
| [LRA-01](handoffs/LRA-01_POWER_INTERFACE.md) | Electrical lead; firmware reviewer; manager integrates | Ready; both specialist roles unclaimed; manager source triage recorded | One agreed qualified-IGN/HOLD/startup/shutdown/reset/USB contract; numerical assumptions and faults explicit; current/protection decisions and reviewer disposition |
| LRA-02 | Power engineer | Ready for gap closure on existing `9527a14` candidate; final depends on 01 | Coherent power schematic/BOM, compatible protection, effective capacitance and current/leakage allocations; off-state paths and bench checklist |
| [LRA-03](handoffs/LRA-03_AS_BUILT.md) | Hardware integrator; analog reviewer | Ready, unclaimed; packet prepared; finalize power domains with 01/02 | Current as-built consolidated with unknowns, frozen Rev A pins/connectors/input loading/protection/grounds/mechanics/test points; no full fuel model |
| [LRA-04](handoffs/LRA-04_COMMUNICATIONS.md) | Bounded communications reviewer; hardware/firmware accept | Ready, unclaimed; packet prepared; coordinate 03 | RS-485/CAN/daughterboard comparison with usable GPIO/peripheral/current/voltage/power-off contract; recommendation and fallback |
| LRA-05 | Logger firmware | Blocked on 01 contract | Isolated shutdown candidate: early HOLD, bounded SD finalization, IGN-return/reset/watchdog behavior; build/fault/replay tests and rollback; no implicit flash |
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
| DOC-01 | Codex pcb-manager, `01a18447-07c2-7bb3-8318-9b276cfdb3b8` | Active, claimed October 28: authority recorded; 01 refreshed and 03/04 prepared. Existing power candidate located and 19 checks rerun. Next: export selected engineering artifacts before remote detailed review; no specialist dispatched yet |

## Decisions and gates

- **D-RA-01 — owner direction:** prioritize integrated-power Rev A; fuel curve,
  dashboard and future-network completion do not gate it.
- **D-RA-02 — planning distinction:** prototype fabrication recommendation,
  assembled-board bring-up, and unattended vehicle approval are separate gates.
  Exact numeric acceptance/test envelope must be agreed, not inferred here.
  Old universal pre-PCB vehicle-duty wording is historical; this is not permission
  to fabricate an electrically unresolved design.
- **D-RA-03 — pending 01:** one shared qualified-IGN/deadline contract. Never mix
  the old raw-GP5/100 ms rules with the newer analog-qualified proposal.
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
