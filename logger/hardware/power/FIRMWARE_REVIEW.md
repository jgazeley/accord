# LRA-01/02 firmware compatibility review

October 28, 2026 — Codex `pcb-manager`, acting firmware interface reviewer.
Session: `01a18447-07c2-7bb3-8318-9b276cfdb3b8`, verified from matching session
and thread environment. Resume: `codex resume 01a18447-07c2-7bb3-8318-9b276cfdb3b8`.
The owner reports no current firmware agent; this manager performs R01 rather
than attributing approval to an absent specialist. Review scope is this file
and coordination; no firmware implementation or hardware changes.

## Disposition

**R01 written source-level disposition delivered: conditionally accept the
interface as the basis for isolated LRA-05 implementation.** GP5 qualified IGN,
GP6 HOLD and the proposed shutdown policy have a feasible software integration
path. Existing firmware does not implement them. Integration of the paper
candidate is approved; runtime timing, component limits and physical reset
behavior remain unproved. R02–R05 and all B01–B07 remain open. No firmware
implementation claimant or deployed automatic-power acceptance is implied.

Reviewed electrical commits `a85f185c4dfc593b0a5b7284170e904cbf8a54c1`
and `c946f6f53af39ff7270122caacb674261d8bd23d`, by Codex logger-power,
session `01a18463-5ed7-7041-ad90-ec3a7480c4e6`. Firmware/server source is
unchanged from the `25cebe8` export baseline. Review includes the sketch,
SD/network/upload modules, card header and format, converter comment handling,
and the installed Arduino-Pico 6.1.0 core/SDK sources. It is independent of
the electrical author, but manager integration and firmware review are by
the same reviewer, not two independent approvals.

## Required implementation findings

| ID | Source evidence and consequence | Required LRA-05 disposition |
|---|---|---|
| F01 | `accord-logger.ino::setup1` waits up to 3000 ms for USB, then prints; `loop1` samples network IGN every 20 ms, has a 200 ms level command, serial bursts and ADC work. `networkSetIgn` can drop updates. None provides a 10 ms power bound. | Establish the sole power owner before blocking sketch initialization. Use an explicitly core-1-owned bounded timer/IRQ or a demonstrated equivalent; do not use the network mailbox as authority. |
| F02 | `OutTee::write` assembles complete lines, then calls potentially blocking USB `Serial.write`. Help, commands and status are also producers; a sample can be part-written while ADC work runs. | Quiesce every producer at a complete-line boundary; publish generation and a stable ring watermark. Do not acknowledge quiescence merely because sampling stopped. No Serial, SdFat, network or contended mutex work in the power IRQ. |
| F03 | Core 0 owns SdFat. `sdLoop` can retry failed media, rename and open files; upload uses card-generation handles. There is no shutdown gate or final close handshake. | Gate uploads, opens, retries and renames; drain/settle/sync/close on core 0. Invalidate upload handles and distinguish card generation from shutdown generation. Serialize any already-running close before a new file, even after IGN return. Stale completion must never close the new file. |
| F04 | No application watchdog policy exists. A timer can continue running while the main loop is blocked. Current USB startup delay already exceeds the proposed 2 s progress age. | Define bounded startup and runtime health separately. Feed only with actual recent progress from both cores and valid power state. Do not count IRQ liveness as foreground health or allow indefinite startup grace. |
| F05 | Existing `ign`/`ms_since_ign` use GP5; changing its physical source changes edge timing. The header declares polarity but not qualification. | Preserve columns, units and polarity; explicitly identify hardware-qualified versus legacy/manual input in per-file metadata. Keep manual-power builds usable and do not label them as qualified hardware. |

These are implementation gates, not claims that the electrical author supplied
broken firmware: that return intentionally contains no firmware changes.

## Requested contract decisions

- **Pins/drive:** accept GP6 reservation and explicit 4 mA drive for the candidate.
  Preload LOW before output-enable; boot with OFF/unknown must not assert HOLD.
  The installed core's `wiring_digital.cpp::__pinMode` supports 4 mA. This setting
  does not prove loaded HIGH >=2.6 V at all rail/temperature corners; the narrow
  transistor-drive margin stays in R03. No GP7 alternative is introduced.
- **Startup/supervision:** accept <=10 ms observation/release supervision and
  measured retention <=900 ms after raw IGN rise as targets. Core `main.cpp`
  launches core 1 before user core-0 `setup`, so an early `setup1` hook is feasible;
  SDK/USB initialization still precedes it and <=750 ms boot is not established.
  SDK `pico_time/time.c` associates an alarm pool with its creating core. Explicitly
  create/verify the core-1 alarm context; do not assume the default pool belongs
  to core 1. Audit interrupt masking, IRQ priority, USB and flash operations.
- **Clock/deadlines:** accept 64-bit monotonic timing, 1770 s finalization,
  1800 s release and <=1801 s release limit with the stated <=1% clock envelope.
  The conditional latest physical release is 1819.202 s after Q OFF, leaving
  227.847 s to the conditional earliest backup cutoff. No wall-clock adjustment
  may renew it. Cross-core 64-bit state needs a race-safe transfer on RP2040;
  `volatile` alone is not a synchronization protocol.
- **Races/reset/USB:** accept generation-tagged requests and acknowledgments,
  genuine qualified ON invalidating prior shutdown, and forced release without
  an SD acknowledgment. A single execution context must arbitrate HOLD; foreground
  and ISR writers must not race. Uncertain OFF edge history cannot create a later
  deadline. Reset during OFF grants no new window, and USB power grants no HOLD.
  USB/residual power after release must not restart recording or reopen a file
  until a valid new RUN generation under the contract.
- **Data loss:** accept possible tail loss under forced cutoff, stalled storage,
  brownout or watchdog reset. Healthy finalization must drain all acknowledged
  complete lines and close normally. If an operation cannot be aborted, HOLD
  release remains independent and bounded; do not promise cancellation of an
  arbitrary blocking SdFat call.
- **Watchdog:** accept the proposed 4 s timeout and <=2 s progress freshness for
  candidate development, subject to F04. Installed SDK `hardware_watchdog/watchdog.c`
  configures broad reset coverage; `watchdog_enable(4000, false)` is a candidate
  API choice that does not pause on debug. Verify initialization, both-core reset,
  GPIO release and actual fault-to-reset timing physically. A ~6 s health/reset
  bound is not a 4 s bound from the first failure and is not graceful finalization.
- **Recording compatibility:** use an additive per-file header such as
  `# log.power interface=lra01-v1 ign_source=hardware-qualified hold=GP6` for the
  qualified build. Final spelling belongs in the implementation and format docs.
  Missing metadata must not be interpreted as proof of qualified hardware;
  retain legacy interpretation. The existing `ign=1:on` polarity and units remain.
  `CARD_FORMAT.md` permits unknown tags; public `cardconv.py` retains comment
  notes. No format-token bump is needed for an additive source descriptor.
  Test old and new synthetic files, header capacity, reinsertion and boot-before-
  clock rename. Do not infer raw edge times from filtered samples or rewrite
  historical records. Public conversion review does not certify the private DB.

## Evidence and limits

Independently run at `c946f6f` in a detached review worktree:

| Command | Result |
|---|---|
| `python3 -B logger/hardware/power/check_max_on_logic.py` | 11 pass |
| `python3 -B logger/hardware/power/check_cutoff_margins.py` | 8 pass |
| `python3 -B logger/hardware/power/check_interface_contract.py` | 14 pass |
| `python3 -B logger/hardware/power/check_component_margins.py` | 11 pass; includes eleven unchanged imported hashes |
| `python3 -B logger/tools/test_native.py` | All eight existing firmware suites pass |
| `git diff --check origin/main...c946f6f` | Pass |

The 44 power checks exercise models, arithmetic and artifact integrity. Existing
native tests establish a regression baseline; neither executes a new power
implementation. No configured build, flashing, physical timing, hot leakage,
reset trace, filesystem fault injection or vehicle test was performed.
LRA-05 must test the actual shared policy/handshake code, not duplicate only
the Python model. Preserve electrical authorship and the original design files.
