# LRA-05 — isolated logger power firmware candidate

Prepared October 28, 2026 by Codex `pcb-manager`, session
`01a18447-07c2-7bb3-8318-9b276cfdb3b8`.
Resume: `codex resume 01a18447-07c2-7bb3-8318-9b276cfdb3b8`.
Claimant: unclaimed. Ready for remote implementation; no bench required to begin.
The manager has supplied the missing firmware interface review.

## Start and scope

Read root AGENTS.md, the current tracker, `logger/NEXT_AGENT.md`, and
`logger/hardware/power/{INTERFACE_CONTRACT,FIRMWARE_REVIEW}.md`.
Use current public main containing the reviewed `a85f185` and `c946f6f` returns.
Reuse the current logger firmware and existing hardware candidate. Claim with
your own verified identity and report branch/base to the manager; manager owns
the tracker. Work on `task/LRA-05-<your-short-id>`.

Allowed paths: `logger/firmware/accord-logger/`, `logger/tests/`,
`logger/protocols/CARD_FORMAT.md`, `logger/NEXT_AGENT.md`, and new
`logger/coordination/LRA05_HANDOFF.md`. Changes to `logger/tools/test_native.py`
are allowed to register relevant native tests. Do not edit electrical files,
keyless, server implementation, root or coordination tracker. If synthetic
converter verification needs a permanent server fixture, propose it in the
handoff for its owner; temporary fixtures outside Git are sufficient here.

## Deliver

1. Implement a testable power-state module and explicit board/build selection
   for legacy manual power versus LRA-01 qualified GP5/GP6. Existing manual
   behavior remains the default until hardware integration is authorized.
   Qualified mode preloads HOLD LOW, sets explicit 4 mA drive and starts the
   sole bounded power supervisor before blocking initialization.
2. Implement monotonic deadlines, no OFF-boot grant, qualified ON reacquisition,
   generation cancellation, forced release independent of core-0 progress, and
   race-safe state transfer. Address F01–F05 in the review individually. Audit
   actual core/SDK alarm affinity and masked-interrupt paths; measured timing
   remains a bench gate, not something a native test can prove.
3. Add complete-line producer quiescence, shutdown gates for upload/SD retry/
   rename/open, stable queue drain, tail settlement, sync/close result and
   serialized IGN-return reopen. Stale generations and card handles cannot
   affect a new file. Never call storage/network/Serial from the power ISR.
4. Implement bounded startup/runtime watchdog health from both cores. IRQ
   activity alone is not proof of foreground progress. Keep reset-OFF release
   and USB behavior explicit; no persistent permission across reset.
5. Add per-file qualification metadata without changing CSV order, units or
   polarity. Verify header capacity, manual/qualified labeling, reinsertion,
   boot-before-clock rename and public converter handling with synthetic files.

## Required evidence and return

Tests must exercise implementation code: OFF/unknown boot, true ON/OFF, deadline
boundaries, clock corrections/wrap assumptions, stalled core/producer/storage,
full ring, SD failure, serial activity, IGN return during each finalization
stage, stale acknowledgments, USB/residual-power release and watchdog health.
Use deterministic time and IO mocks; do not substitute another policy model
that production does not call. State which timing/fault paths still need hardware.

Run all existing native suites and the four power scripts. Compile both board
modes with dummy credentials using the documented build helper and installed
toolchain; do not collect private secrets or commit binaries. Record toolchain,
commands, results, firmware/config identity, source hashes and any build blocker.
Review the exact staged public content and push the task branch with attribution.

Return `LRA05_HANDOFF.md` with F01–F05 dispositions, API/state ownership,
tests, runtime/bench gaps and rollback to the unchanged manual build. A compiling
candidate does not close startup, IRQ-latency, pad-voltage, watchdog-reset or
storage-integrity measurements. No flash, vehicle/bench operations, live service
changes, database writes or fabrication are included. Manager reviews before
integration; source publication is separate from deployment.

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
