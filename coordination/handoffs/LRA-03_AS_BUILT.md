# LRA-03 — consolidate the logger as-built and Rev A interfaces

October 28, 2026 update by Codex `pcb-manager`, session `01a18447-07c2-7bb3-8318-9b276cfdb3b8`.
Current manager bookmark: `codex resume 01a18447-07c2-7bb3-8318-9b276cfdb3b8`.
Identity verified from matching `CODEX_SESSION_ID` and `CODEX_THREAD_ID`.

**Parent:** M5. **Responsible:** hardware integrator, unclaimed; analog reviewer,
unclaimed. Current pcb-manager integrates; task state is in the single tracker.

## Objective and scope

Produce one traceable description of the fitted logger and a proposed Rev A
interface freeze, preserving the distinction between fitted, specified and unknown.
Work in `jgazeley/accord` from transition base `303092a74526c1107ab705457064b6062dfc0906`
and the latest pushed revision of this packet. Suggested branch
`task/LRA-03-<own-session-short>`.

Claim only `logger/hardware/as-built/`. Deliver `AS_BUILT.md`,
`REV_A_INTERFACES.md` and a `SOURCE_MANIFEST.json` for any recovered artifacts.
Power documents, firmware, KiCad and root/coordination remain with their owners.
Environment: source/document analysis without bench access initially.

## Minimum inputs and dependencies

Read `logger/hardware/REV_A_CONTEXT.md`, `logger/hardware/README.md`,
`coordination/MIGRATION_MAP.md` and `coordination/handoffs/LRA-01_POWER_INTERFACE.md`.
Cross-check actual public firmware pin declarations and SD assignments. Manager
provides selected, public-reviewed historical circuit/ADC excerpts if required.
Detailed fitted opto and ADC component values are unresolved inputs, not license
to copy specified values into an as-built BOM. Collect precise owner/bench questions.

Start signal consolidation now; power domains finalize after LRA-01/02. Exchange
proposed GPIO/connector reservations with LRA-04 before either freezes them.

## Deliverables and acceptance

- Circuit table: signal, vehicle tap, polarity, fitted component/value/source,
  proposed change, GPIO, rail and confidence. Verify 1N5819 correction; distinguish
  opto input isolation from the installation's shared grounds.
- Interface proposal: input loading/protection, grounds/returns, connectors,
  mounting/enclosure constraints, SD/USB access and test points. Dimensions not
  actually measured remain explicitly unknown.
- Off-state path matrix: every energized vehicle input, USB and expansion path
  against disabled rails; expected path and analysis/test required. Refer to
  the power owner's contract rather than invent a second power design.
- Evidence check: each fitted assertion has a dated source or physical record;
  each conflict/unknown has a proposed resolution and responsible role. Analog
  reviewer records loading/protection disposition; electrical lead agrees power
  boundaries; firmware reviewer agrees pin mapping. Manager records acceptance.

Authorized: scoped public-safe documentation and analysis. Hardware operation,
vehicle wiring, flashing, purchasing/fabrication and private runtime/DB changes
require separate owner authorization. No fuel calibration model is needed here.

## Return and next action

First acknowledge claimant and exact scope to manager, then deliver the circuit
matrix with unknowns. Return pushed branch/commit, provenance, verification,
review disposition, remaining questions and next bounded action. No delivery,
bench test or acceptance is claimed by this packet. Preserve any uncommitted work
and identify it in the return; do not silently overwrite other owners' artifacts.

> **Required agent attribution:** Follow `logger/coordination/AGENT_ATTRIBUTION.md` relative to this repository root. Use your own tool, role and verified current session ID for Git author and committer (`<Tool> <role> [<short-id>]`), using per-command settings. End commits with `Agent-Session: <role>` and your full tool-specific session-ID trailer (`Codex-Session-ID`, `Claude-Session-ID` or `Antigravity-Session-ID`). This includes documentation-only work. Identify yourself and your resume command in coordination documents and dated updates. Preserve predecessor identity and original attribution when transporting commits. If an ID is unavailable, state that explicitly; never invent or borrow one. Include this requirement in subsequent seeds and handoffs.
