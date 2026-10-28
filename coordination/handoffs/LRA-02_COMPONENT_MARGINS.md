# LRA-02 — close component margins and parked-current allocations

Prepared October 28, 2026 by Codex `pcb-manager`, session
`01a18447-07c2-7bb3-8318-9b276cfdb3b8`.
Resume: `codex resume 01a18447-07c2-7bb3-8318-9b276cfdb3b8`.

## Assignment and completion boundary

Parent M2/M5. Next assignment for the returning Codex `logger-power` engineer,
session `01a18463-5ed7-7041-ad90-ec3a7480c4e6`
(`codex resume 01a18463-5ed7-7041-ad90-ec3a7480c4e6`). Continuation acknowledgment is
pending; the tracker owns current task status. No new engineering session is needed.
Environment: remote repository/datasheet/calculation work, no bench access.
Manager integrates; firmware reviewer remains separately required for LRA-01 R01.

Continue from your pushed electrical candidate
`a85f185c4dfc593b0a5b7284170e904cbf8a54c1` on `task/LRA-01-01a18463`.
Create `task/LRA-02-01a18463` from that commit and fetch the latest main for this
packet and coordination context. LRA-01 is a candidate awaiting firmware and
manager review, not a frozen contract. Its full technical review and test rerun
by the manager have not been performed. State assumptions explicitly and record
any change needed to its interface; do not assume publication means acceptance.

## Minimum context

- Your `logger/hardware/power/LRA01_HANDOFF.md`, especially R03/R04 and R02/R05.
- `logger/hardware/power/INTERFACE_CONTRACT.md`, sections 6–9.
- Existing `CUTOFF_MARGIN_REVIEW.md`, `BOM.csv` and `MAX_ON_BOM.csv`.
- Current `coordination/PROJECT_MILESTONES.md` and LRA-01 packet.

## First bounded deliverable

Close as much of **R03 component limits and R04 parked current** as primary
manufacturer evidence and calculation permit, preserving the existing topology.

1. Select exact CCLK/A5/CIN/COUT capacitor parts or justified combinations.
   Show effective capacitance at actual bias/temperature/tolerance, ESR/ripple,
   leakage, package and which requirement each selection satisfies. Separate
   guaranteed limits from typical curves and measurements still required.
2. Build a condition-specific current/drive ledger for A5, QP, QI/QS/QMON/QRESET,
   opto, protection, PCB and interface allocations. Examine the already-identified
   hot-leakage, loaded-logic, oscillator startup/load and low-load regulator gaps.
   Do not treat limits at different voltages/temperatures as an assembled guarantee.
3. Preserve whole-system 100/500 µA targets. Where a specified limit cannot close
   a row, identify the exact gap, compare bounded replacement options, and propose
   the smallest justified part/circuit change. Do not repeat a general power
   topology search. The new LRA-01 allocations remain proposed until reviewed.
4. Define the resulting bounded bench configuration under the existing 12–16 V
   controlled supply envelope, including current limit, disconnected inputs and
   pending tests. For R02 retain the <=28 V protected-input requirement and name
   unresolved vehicle exposure/fuse/energy inputs. Do not invent vehicle transient
   requirements or claim a TVS label closes protection.
5. For R05 reserve explicit leakage/loading requirements for LRA-03/04; avoid a
   competing as-built or bus design. DOR remains a candidate with its stated
   forward-drop/thermal/recovery checks. Stop at a clear engineering disposition:
   supported / conditional / unresolved, with reason and next evidence.

## Owned paths and return

Own only these new files under `logger/hardware/power/`:
`COMPONENT_MARGIN_CLOSURE.md`, `BOM_DELTA.csv`, `LRA02_HANDOFF.md`, and an optional
`check_component_margins.py` when it checks substantive calculations/invariants.
Keep the eleven imported files and their manifest unchanged. Reference proposed
contract corrections in the closure document; leave INTERFACE_CONTRACT and
reviewer-owned FIRMWARE_REVIEW to their current review process. Do not edit shared
coordination, firmware, as-built or communications artifacts.

Return exact part numbers, cited manufacturer revision/pages, calculations with
conditions, old/new BOM deltas, unresolved requirements and actionable bench tests.
Run the existing 11+8+14 checks on your branch and any new meaningful calculations;
verify original-file hashes and CSV structure. Passing models are not acceptance
of component limits or physical behavior. Public-review exact staged files and
publish only this task's scope with attribution. Return branch/commit, test results,
review disposition, uncommitted owned work and next bounded action.

Completion of this packet is a reviewable component/margin package, which may
retain explicitly evidenced blockers. It does not close all of LRA-02 or authorize
final schematic freeze, hardware operation, purchases, fabrication, deployment or
DB writes. Firmware agreement proceeds independently and does not block this
bounded paper-design work.

> **Required agent attribution:** Follow `logger/coordination/AGENT_ATTRIBUTION.md` relative to this repository root. Use your own tool, role and verified current session ID for Git author and committer (`<Tool> <role> [<short-id>]`), using per-command settings. End commits with `Agent-Session: <role>` and your full tool-specific session-ID trailer (`Codex-Session-ID`, `Claude-Session-ID` or `Antigravity-Session-ID`). This includes documentation-only work. Identify yourself and your resume command in coordination documents and dated updates. Preserve predecessor identity and original attribution when transporting commits. If an ID is unavailable, state that explicitly; never invent or borrow one. Include this requirement in subsequent seeds and handoffs.
