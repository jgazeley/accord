# LRA-04 — choose bounded Rev A communications provisioning

October 28, 2026 update by Codex `pcb-manager`, session `01a18447-07c2-7bb3-8318-9b276cfdb3b8`.
Current manager bookmark: `codex resume 01a18447-07c2-7bb3-8318-9b276cfdb3b8`.
Identity verified from matching `CODEX_SESSION_ID` and `CODEX_THREAD_ID`.

**Parent:** M5. **Responsible:** communications reviewer, unclaimed; hardware and
firmware reviewers, unclaimed. Current pcb-manager integrates; tracker owns state.

## Objective and scope

Compare onboard RS-485, CAN controller plus transceiver, and a host-side
daughterboard interface with neither bus populated. Return one recommendation,
a fallback and the unresolved constraints needed for schematic freeze.
Work in `jgazeley/accord` from transition base `303092a74526c1107ab705457064b6062dfc0906`
and the latest pushed packet revision; branch `task/LRA-04-<own-session-short>`.
Own only `logger/hardware/communications/`; deliver `REV_A_OPTIONS.md` and
`INTERFACE_PROPOSAL.md`. Firmware and other hardware artifacts are read-only.
Environment: remote documentation/source review; no bench presumed.

## Minimum inputs and dependencies

Read `logger/hardware/REV_A_CONTEXT.md`, `logger/hardware/README.md`,
`coordination/handoffs/LRA-01_POWER_INTERFACE.md` and
`coordination/handoffs/LRA-03_AS_BUILT.md`; inspect actual logger/keyless source as
needed. Keyless already uses RS-485; no factory CAN connection is established.
The tested 5 V RS-485 module/dividers remain an interim option. Do not reopen
that completed feasibility question or promise CAN interoperability with keyless.

Analysis may begin alongside LRA-03. Obtain LRA-01/02 rail/current/off-state
constraints and agree pin reservations with LRA-03 before recommending a freeze.
GP6/GP7 HOLD and GP8/GP9 bus suggestions are not accepted allocations.

## Deliverables and acceptance

- Compare controller versus transceiver requirements, exact GPIO/peripheral use,
  UART/SPI/PIO/DMA/interrupt needs and current Arduino-Pico support. Use current
  primary datasheets/documentation with version/date and links for factual claims.
- Cross-check SD SPI0, capture, ADC, Wi-Fi and proposed HOLD resources; list pin
  conflicts and concrete resolutions. A header option needs signal/voltage/power
  pinout, connector orientation, mechanical allowance and return-current plan.
- Specify active/off current assumptions, reset/enable defaults, termination,
  bias, protection and energized-bus/board-off behavior for each viable option.
  Separate calculated, specified and unmeasured behavior. Reserve RTC/test
  resources only where justified by a concrete requirement.
- Give a bounded recommendation and fallback, BOM/space implications and named
  tests. Hardware and firmware reviewers record compatibility dispositions;
  local review is required for browser-derived conclusions. Manager integrates.

Authorized: scoped research/documentation and synthetic feasibility checks.
No complete CAN stack, firmware feature implementation, vehicle connection,
service/DB changes, purchases, fabrication or flashing belongs to this packet.

## Return and next action

Acknowledge claimant/scope to manager first. Return comparison and explicit pin/
power proposal, sources, pushed branch/commit, checks and their limits, reviewer
status and blockers. No selected bus, delivery or acceptance is claimed here.
Name remaining uncommitted artifacts and the next bounded action in the return.

> **Required agent attribution:** Follow `logger/coordination/AGENT_ATTRIBUTION.md` relative to this repository root. Use your own tool, role and verified current session ID for Git author and committer (`<Tool> <role> [<short-id>]`), using per-command settings. End commits with `Agent-Session: <role>` and your full tool-specific session-ID trailer (`Codex-Session-ID`, `Claude-Session-ID` or `Antigravity-Session-ID`). This includes documentation-only work. Identify yourself and your resume command in coordination documents and dated updates. Preserve predecessor identity and original attribution when transporting commits. If an ID is unavailable, state that explicitly; never invent or borrow one. Include this requirement in subsequent seeds and handoffs.
