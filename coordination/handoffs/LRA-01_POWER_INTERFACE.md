# LRA-01 — agree the logger power/shutdown interface

Prepared October 28, 2026 by Codex `pcb-manager`, session `01a17045-1855-7af2-b76a-32c2b778cd64`. Historical bookmark: `codex resume 01a17045-1855-7af2-b76a-32c2b778cd64`. Successors use their own identities.

October 28, 2026 update by Codex `pcb-manager`, session `01a18447-07c2-7bb3-8318-9b276cfdb3b8`.
Current manager bookmark: `codex resume 01a18447-07c2-7bb3-8318-9b276cfdb3b8`.
Identity verified from matching `CODEX_SESSION_ID` and `CODEX_THREAD_ID`.

**State:** owner reports electrical work begun on a remote machine October 28;
electrical session/branch pending receipt. Logger-firmware reviewer unclaimed.
**Parent:** M2; feeds M5. **Responsibility:** electrical lead, with logger-firmware
review; current `pcb-manager` integrates the decision. The manager has prepared
this assignment, not claimed electrical approval.
Use your own session identity. No old agent is presumed currently available.

## Objective and context

Produce one compatible IGN/HOLD/deadline/reset/USB contract plus concrete
current/protection decisions so electrical capture and firmware can proceed.
No hardware implementation or fabrication is part of this assignment.

Start in `jgazeley/accord`; transition base is
`303092a74526c1107ab705457064b6062dfc0906`, code baseline `8261314`.
Use the latest pushed manager packet revision (see
`git log -1 -- coordination/handoffs/LRA-01_POWER_INTERFACE.md`). Suggested branch `task/LRA-01-<own-session-short>`; own
`logger/hardware/power/` design documents only. Propose cross-owner changes
rather than edit firmware or global task state concurrently with its owner.

Read [current task authority](../PROJECT_MILESTONES.md),
[Rev A context](../../logger/hardware/REV_A_CONTEXT.md),
[migration map](../MIGRATION_MAP.md), and current logger startup/IGN/SD APIs.
The selected circuit tables, BOMs, handoffs and checks from `9527a14` are now
exported in [logger/hardware/power](../../logger/hardware/power/README.md).
Start with that directory README for revision precedence and current commands.
The source manifest records exact hashes and original attribution; private
repository access and predecessor conversations are not prerequisites.

## Owner direction — continue the existing circuit, October 28

Recorded by the current pcb-manager identified above: the owner explicitly wants
to avoid repeating power-circuit research where a potential circuit already exists.
**Use `9527a14153c7b06f3d59b641a2e681b28dcd1735` as the continuation baseline.**
LRA-01/02 close and integrate that candidate; they are not a fresh topology search.
Retain completed circuit choices/calculations unless a specific unresolved
requirement or verified defect warrants changing them. Any alternative must name
that defect, explain the bounded change and preserve useful existing work.

Manager recovery check on October 28 located the original `logger-power/` in the
historical checkout. The following ten files are byte-identical to `9527a14`:

- `NEXT_SESSION.md`: use its final **Current handoff after the margin review**
  section; earlier remaining-work lists describe superseded checkpoints.
- `DESIGN.md`, `BOM.csv`: base onboard supply, switching connections and BOM.
- `MAX_ON_CUTOFF.md`, `MAX_ON_BOM.csv`: independent cutoff circuit and additions.
- `CUTOFF_MARGIN_REVIEW.md`: later clock/reset/supply/current revisions; read
  alongside the base design to avoid restoring superseded choices.
- `INTERFACE_HANDOFF.md`, `PROTOTYPE_TEST_PLAN.md`: proposed interfaces and tests.
- `check_max_on_logic.py`, `check_cutoff_margins.py`: existing verification.

The historical checkout's later committed power-folder change only adds a
manager seed; it does not revise these engineering files. Original commit author
is `Jayson Gazeley (Remote Codex)`; the engineer session identified by the owner
and historical manager review is `01a17407-4357-7031-b3ac-a51c97864fbe`.
Preserve that attribution when exporting; this manager is the verifier/transporter.

Fresh verification: ran both scripts from exact Git blobs in a temporary directory
with Python 3 `-B`: **11 logic + 8 margin checks passed**. No historical working
files were changed. These remain conditional checks, not physical acceptance.

Continue with the known open work: current/leakage allocations, compatible input
protection, exact capacitor/hot-device/clock limits, off-state signal isolation,
current-firmware agreement, then coherent schematic/BOM and measured validation.
Export completed October 28: the ten listed files plus the supporting
`REVIEW_2026-10-25.md` are preserved byte-for-byte in `logger/hardware/power/`.
[Public-content/provenance review](../reviews/POWER_EXPORT_9527A14_2026-10-28.md)
records the source, exclusions and destination checks. Continue this circuit;
no reconstruction of earlier work is required.

## Existing keyless power/input reference

Owner reminder, October 28, recorded by the current pcb-manager: consult the
already-migrated `keyless/hardware/hondaPico.kicad_sch` and PCB for applicable
working examples. Its U13 PC817 ignition cell and U3 LM2678 supply are concrete
references; LRA-03 records additional blocks. Historical notes explicitly derive
the earlier IGN wake cell from U13. Use this prior work alongside `9527a14`.
The keyless input cell does not itself establish the proposed shared-qualified
IGN timing, logger cutoff or off-state behavior. In particular, the keyless
protection arrangement must not be copied over the unresolved regulator/clamp
compatibility requirement. Preserve useful circuits and review the specific
logger differences; no fresh general topology search is implied.

## Manager source triage — review input, not firmware acceptance

Inspected public firmware at `303092a` (unchanged code baseline `8261314`):

- `accord-logger.ino`: `setup()` calls SD then network setup; no HOLD output is
  initialized. `setup1()` configures active-low GP5 with a pull-up and can wait
  up to 3000 ms for USB serial before `loop1()` begins. Startup HOLD cannot rely
  on that loop meeting the old 100 ms proposal.
- `loop1()` samples GP5 for `networkSetIgn()` every 20 ms, with a nonblocking
  mailbox that can reject a contended update. This does not establish the later
  proposed <=10 ms observation bound. The reviewer must specify the observation
  owner, edge timestamp and worst-case delay, including startup and contention.
- `logger_sd.h` exposes setup/loop/status/upload APIs, no shutdown handshake.
  Core 1 produces lines; core 0 owns SdFat/SPI. `sdLoop()` drains and periodically
  syncs at 10000 ms or 4096 bytes; this is not a bounded finalization operation.
  Decide producer quiescence, drain/close acknowledgment, timeout and IGN return
  during each phase before implementing LRA-05.
- `wifi_schedule.h` has 5000 ms settling and a 900000 ms maximum radio window.
  Those govern radio policy only. Its initial known-OFF state can open a window;
  it must not be reused to grant a fresh power HOLD after IGN-absent reset/USB boot.
  Proposed 1800 s HOLD / nominal 2048 s hardware cutoff still need tolerances,
  finalization reserve and a single qualified-IGN rearm definition.

This is static source inspection; no timing, circuit or firmware acceptance test
was performed. Electrical and firmware reviewer acknowledgments remain required.
The selected historical power tables are now exported. This supplies review
inputs; electrical and firmware acceptance remain pending.

## Assignment and return protocol

Before editing, acknowledge electrical lead or firmware reviewer with your own
verified identity to the manager. Electrical scope is
`logger/hardware/power/`; firmware review belongs in
`logger/hardware/power/FIRMWARE_REVIEW.md`, reserved to the acknowledged reviewer.
The electrical lead owns the other design documents in that directory. If one
person performs both analyses, record that and retain a separate review gate.
Firmware source is read-only for this task. Manager alone updates the tracker.

Return the contract candidate, review findings and explicit unresolved decisions,
source provenance, checks and pushed branch/commit. Manager integration is blocked
until the electrical and firmware dispositions are recorded; missing measurements
must remain named bench requirements, not inferred passes. Use remote/no-bench
analysis initially. The first deliverable may be a candidate with blockers.

## Required decisions/deliverables

1. A state/timing/polarity table resolving old raw-GP5/100 ms assumptions versus
   the later shared-qualified IGN. Include startup HOLD, IGN-return during SD
   close, deadline/rearm, brownout/reset/USB-only boot and no-network/SD-fault cases.
2. Explicit GPIO reservation and interface semantics against current v0.8.1.
   No collision with capture/SD or speculative future bus assumptions.
3. Disposition of current-budget gap and incompatible clamp/regulator boundary:
   defend allocations under existing targets or present an explicit alternative
   for review. Do not silently relax targets or equate powered 5 V current with
   battery-side off-state leakage.
4. Named failure exclusions, independent cutoff coverage, proposed numerical
   limits versus calculations versus measurements still needed.
5. Current contract and bounded electrical/firmware/bench follow-ups in
   `logger/hardware/power/INTERFACE_CONTRACT.md`, plus source manifest for any
   imported engineering artifacts. This becomes the active contract; old versions
   remain historical. No second live power plan in the old repository.

## Acceptance and boundaries

Electrical and firmware review must agree or record exact unresolved conflicts.
No mutually incompatible startup/rearm rules; every fault has an expected outcome
and proposed test. If historical 11 logic/8 margin scripts are selected, run them
and report their conditional scope; green tests do not establish circuit safety.
A candidate with review pending is not an accepted contract.

Remote design work needs no bench. Do not flash, change live firmware/services,
write DB records, wire a vehicle, purchase parts or authorize fabrication. Do not
implement CAN or the complete shutdown feature here. Publish only owned, reviewed
source/docs on the task branch with attribution; manager integrates task status.
Return commit/branch, tests, review disposition, blockers and next action.

Optional bookmarks: remote power predecessor `01a17407-4357-7031-b3ac-a51c97864fbe`;
earlier power `01a173c4-d2fd-7f71-a396-8996d502387b`; logger delivery
`01a17526-034c-78f1-9d09-24c3b88c3dc7`; manager predecessor in author block above.
These bookmarks are not prerequisites or current staffing claims.

> **Required agent attribution:** Follow `logger/coordination/AGENT_ATTRIBUTION.md` relative to this repository root. Use your own tool, role and verified current session ID for Git author and committer (`<Tool> <role> [<short-id>]`), using per-command settings. End commits with `Agent-Session: <role>` and your full tool-specific session-ID trailer (`Codex-Session-ID`, `Claude-Session-ID` or `Antigravity-Session-ID`). This includes documentation-only work. Identify yourself and your resume command in coordination documents and dated updates. Preserve predecessor identity and original attribution when transporting commits. If an ID is unavailable, state that explicitly; never invent or borrow one. Include this requirement in subsequent seeds and handoffs.
