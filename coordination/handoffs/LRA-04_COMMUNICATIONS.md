# LRA-04 — choose bounded Rev A communications provisioning

October 29, 2026 update by Codex `pcb-manager`, session `01a18447-07c2-7bb3-8318-9b276cfdb3b8`.
Current manager bookmark: `codex resume 01a18447-07c2-7bb3-8318-9b276cfdb3b8`.
Identity verified from matching `CODEX_SESSION_ID` and `CODEX_THREAD_ID`.

**Parent:** M5. **Responsible:** communications reviewer, unclaimed; hardware and
firmware reviewers, unclaimed. Current pcb-manager integrates; tracker owns state.

## Objective and scope

Compare onboard RS-485, CAN controller plus transceiver, and a host-side
daughterboard interface with neither bus populated. Return one recommendation,
a fallback and the unresolved constraints needed for schematic freeze.
Work in `jgazeley/accord` from current public main containing reviewed LRA-01/02
and LRA-05 candidate `0745d5b`; record the exact starting revision. Branch
`task/LRA-04-<own-session-short>` when Git tools are available.
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

**Ready to assign now.** The reviewed LRA-01/02 papers provide a provisional
power interface; completion of every electrical/bench gate is not a prerequisite
for this comparison and interface proposal. Work alongside LRA-03; coordinate
final pin/connector reservations before schematic freeze. Do not declare a
completed vehicle interface while protection/isolation requirements remain open.

Read these current documents after the historical/context summaries above:

- [LRA-01 interface](../../logger/hardware/power/INTERFACE_CONTRACT.md), especially
  sections 2, 6–8: GP5 qualified IGN, GP6 HOLD, power and off-state boundaries.
- [LRA-02 margins](../../logger/hardware/power/COMPONENT_MARGIN_CLOSURE.md), especially
  sections 4–5: unresolved current guarantees and interface allocations.
- [LRA-05 review](../reviews/LRA05_REVIEW_2026-10-29.md) and
  [implementation handoff](../../logger/coordination/LRA05_HANDOFF.md): actual
  firmware resources and the remaining timing fault limitation.

Apply these constraints to every option:

| Constraint | Required treatment |
|---|---|
| Existing logger resources | Preserve GP2/3 capture, GP4 brake, GP5 IGN, GP26/27 ADC and SD SPI0 GP16–19. Reserve GP6 for candidate HOLD; GP7 is not an alternate HOLD assignment. GP8/9 are suggestions only until this review/LRA-03 agree. |
| Firmware resources | Core 0 owns SD/Wi-Fi; core 1 capture and the power supervisor. Qualified mode dynamically claims a hardware alarm and uses the watchdog. Account for bus IRQ/peripheral/PIO/DMA and any masking/blocking interaction; no automatic spare-alarm assumption. |
| Power domains | Identify the switched rail and logic levels for each device. Do not assign a continuously powered bus load to A5 or assume undocumented regulator/current headroom. Separate active demand, shutdown demand and externally supplied current while the logger is off. |
| Off-state allocation | Whole-system targets remain 100 uA at 20–30 C / 500 uA at 85 C. All independently energized interfaces together have 10/25 uA allocation; LRA-02 tentatively reserves 2/5 uA of that total for future bus/service and 8/20 uA for five vehicle inputs. These are unproved allocations, not measured capacity. Show a compliant path or explicitly request a tradeoff; do not silently enlarge them. |
| Isolation/protection | Demonstrate specified powered-off bus and GPIO behavior, including external power/debug and connector paths. Unpopulated/disconnected fallback is permissible. R02 vehicle protection and R05 isolation remain open and require later electrical review. |

An unresolved component limit should produce a conditional recommendation and
a precise follow-up, not a blanket refusal to perform LRA-04. Inventory is
incomplete and exact reconciliation is deferred; do not block on stock access.

## Existing RS-485 implementation to consult first

Owner reminder, October 28, recorded by the current pcb-manager: the existing
`hondaPico` keyless circuit provides working examples and must inform this review.
Read `keyless/hardware/hondaPico.kicad_sch` U5 and its RS-485 notes together with
`keyless/firmware/accord-keyless/accord-keyless.ino` and `link.h`.
The schematic specifies MAX3485 on 3V3, tied DE and /RE with a 10k default-listen
pulldown, selectable 120-ohm termination and a dedicated bus ground return.
Keyless firmware assigns GP8 TX, GP9 RX, GP10 direction and 115200 baud.
Those are keyless allocations; propose logger allocations separately.

Treat these as existing design/source evidence. Reconcile R14/R15 bias values
against the PCB and fitted board before adopting them: the migration validation
report flags a schematic/PCB mismatch. Confirm populated hardware and operational
bus evidence separately from stale firmware comments. This reference and the
owner-tested 5 V module/divider option should precede new component research;
new analysis should address actual logger power-off/resource/interface gaps.

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

For a browser LLM without repository write tools, return the proposed contents
of `REV_A_OPTIONS.md` and `INTERFACE_PROPOSAL.md` with source links and the
repository revision inspected. Manager performs local verification, publication
review and integration; inability to push is not a blocker. If a required source
cannot be accessed, name that exact file and continue independent comparisons.
Use the available tool/model/role identity and explicitly state unavailable
session identifiers; never invent an ID or claim executed tests/commits.

> **Required agent attribution:** Follow `logger/coordination/AGENT_ATTRIBUTION.md` relative to this repository root. Use your own tool, role and verified current session ID for Git author and committer (`<Tool> <role> [<short-id>]`), using per-command settings. End commits with `Agent-Session: <role>` and your full tool-specific session-ID trailer (`Codex-Session-ID`, `Claude-Session-ID` or `Antigravity-Session-ID`). This includes documentation-only work. Identify yourself and your resume command in coordination documents and dated updates. Preserve predecessor identity and original attribution when transporting commits. If an ID is unavailable, state that explicitly; never invent or borrow one. Include this requirement in subsequent seeds and handoffs.
