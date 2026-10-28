# LRA-01 — agree the logger power/shutdown interface

Prepared October 28, 2026 by Codex `pcb-manager`, session `01a17045-1855-7af2-b76a-32c2b778cd64`. Historical bookmark: `codex resume 01a17045-1855-7af2-b76a-32c2b778cd64`. Successors use their own identities.

**State:** ready, unclaimed. **Parent:** M2; feeds M5. **Responsibility:** electrical
lead, with logger-firmware review; successor manager integrates the decision.
Use your own session identity. No old agent is presumed currently available.

## Objective and context

Produce one compatible IGN/HOLD/deadline/reset/USB contract plus concrete
current/protection decisions so electrical capture and firmware can proceed.
No hardware implementation or fabrication is part of this assignment.

Start in `jgazeley/accord`, based on the coordination-transition commit (find
with `git log -1 -- coordination/PROJECT_MILESTONES.md`); code baseline is
`8261314`. Suggested branch `task/LRA-01-<own-session-short>`; own
`logger/hardware/power/` design documents only. Propose cross-owner changes
rather than edit firmware or global task state concurrently with its owner.

Read [current task authority](../PROJECT_MILESTONES.md),
[Rev A context](../../logger/hardware/REV_A_CONTEXT.md),
[migration map](../MIGRATION_MAP.md), and current logger startup/IGN/SD APIs.
The historical exact circuit tables are at private `logger-power/` candidate
`9527a14`. Retrieve only needed documents/scripts with provenance and public
review. If private access is unavailable, request the selected export from the
manager; do not require predecessor conversations or invent component values.

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
