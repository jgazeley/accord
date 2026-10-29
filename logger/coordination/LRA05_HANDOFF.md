# LRA-05 — qualified IGN/HOLD firmware candidate

October 29, 2026 — Codex `logger-power`.
Session: `01a18463-5ed7-7041-ad90-ec3a7480c4e6`, verified from matching
`CODEX_SESSION_ID` and `CODEX_THREAD_ID`.
Resume: `codex resume 01a18463-5ed7-7041-ad90-ec3a7480c4e6`.

Task branch: `task/LRA-05-01a18463`.
Base: `2c52afd7b5609444641d02cd420bc252a1f494c7` (fetched reviewed public main).
Implementation commit: the attributed commit containing this handoff; its exact
hash accompanies the branch return. Manager owns tracker claim and integration.
The owner explicitly authorized this packet with “begin task.” Scope is the
packet's firmware/tests/format/next-agent/handoff paths only. Electrical design,
manager coordination, server implementation and live equipment are unchanged.
The original checkout's preexisting server README edit was left untouched.

## Return and engineering decisions

`0.8.1-lra05-dev` implements an opt-in LRA-01 GP5/GP6 candidate; default
`LOGGER_POWER_QUALIFIED=0` retains manual power. `1` selects GP5 active-LOW
hardware-qualified IGN, GP6 active-HIGH HOLD, LOW preload before output enable,
and explicit 4 mA drive. Neither compilation nor this label certifies wiring.

At the first line of core-1 `setup1`, the qualified build installs its sole
runtime HOLD owner: an exclusively claimed RP2040 hardware alarm IRQ on core 1,
highest priority, rearmed 5 ms after each callback. The default SDK alarm pool
and SDK alarm callback dispatcher are deliberately avoided: both involve
shared spinlock paths. There is no heap allocation in this supervisor. Resource
failure leaves HOLD LOW and the enabled watchdog resets; no fallback grant.

The ISR uses `time_us_64()/1000`, retains HOLD after a valid ON, starts finalization
at OFF + 1770 s and releases at OFF + 1800 s whether storage acknowledged or not.
OFF/unknown boot grants nothing. An unknown observation starts the conservative
OFF window; later OFF does not move it. If supervision misses more than 10 ms,
a newly observed OFF is charged back to the prior observation, not the late
callback. A backwards monotonic input fails closed. Actual qualified ON at a
deadline wins, increments the generation, and cancels the old power deadline.
The generation counter fails closed at exhaustion. USB/residual power does not
rearm recording; valid new ON is required. No permission persists across reset.

Finalization stops every Out producer at a complete-line boundary. Even a row
whose prefix was printed before ADC must finish before acknowledgment. A prefix
suppressed while stopped cannot become a suffix row if the new file opens
mid-report. Qualified lines up to 512 bytes enter the 8192-byte SPSC queue
whole; overflow/full-queue drops whole records. The stable producer watermark
bounds the old file's drain. A failed card discards the abandoned queue after
quiescence, trading possible old data loss for no half-row in the new file.
A qualified header must persist before producers are enabled.

An observed OFF-to-ON return creates a fresh recording generation and file even
if it precedes 1770 s. This conservative choice makes ownership explicit; pulses
and the existing 1 Hz IGN latch are not reset. Core 0 completes any old drain,
settle, sync and close before reopening. A blocking library call already entered
cannot be cancelled, but a fresh snapshot is required before granting producers
a new file. Upload handles have separate card-generation invalidation. A stale
close result is diagnostic only, and cannot control HOLD or close a later file.

Startup health grace is a fixed **8 s from supervisor installation**, allowing
the existing 3 s USB wait; each core loses that exemption when it completes
setup. Runtime feeds require both foreground progress stamps no older than
**2 s**. The ISR does not refresh them. Health failure latches until reset;
late foreground recovery cannot resume feeds. `watchdog_enable(4000, false)`
gives a nominal roughly 6 s runtime fault-to-reset bound, or up to roughly 12 s
from supervisor installation for incomplete startup. These are not measured
reset bounds and not substitutes for the startup retention target. A watchdog
reset while OFF releases and cannot renew the 30-minute window.

## F01–F05 dispositions and ownership

| Review | Candidate disposition | Evidence / remaining qualification |
|---|---|---|
| F01 | Direct core-1 alarm IRQ exclusively owns runtime GP6; 5 ms rearm precedes USB/setup waits. Policy is independent of network mailbox and core-0 SD progress. | Native policy deadlines and compiled IRQ inspection pass. Actual boot/IRQ latency and masked-interrupt faults remain open below. |
| F02 | All Out writers use shared `Producer`; even stop tokens ACK only at a line boundary. Queue publishes whole records with acquire/release atomic 32-bit indices. Qualified USB mirror uses available TX capacity and may drop mirror bytes. | Native partial ADC row, suppressed-prefix/resume, full/overlong records, wrap, and combined producer/queue/tail/session test pass. USB library calls can still block on their SDK mutex; ISR plus watchdog remain independent subject to IRQ masking. |
| F03 | Shared `Session<PowerStorage>` serializes stop/ACK/watermark/drain/settle/sync/close/reopen; gates retries, rename, open and uploads. Open completion is revalidated. Failed media is not carried into a new file. | IGN return at every finalization stage, stale ACKs, blocked producer/drain, each IO failure, failed open/backoff and late open tests pass. SdFat physical fault injection still required. |
| F04 | Fixed startup grace, explicit per-core setup completion and foreground heartbeats, latched health failure, 4 s watchdog. RX work is capped at 128 bytes per loop in qualified mode. A completed bounded command can report foreground progress. | Native startup boundary, either-core stalls, late recovery, a concurrently published slightly future heartbeat, and 32-bit health timestamp rollover pass. Reset coverage, GP6 release and observed timing require bench. |
| F05 | Additive per-file `log.power` distinguishes manual/qualified; no CSV reordering or meaning changes; missing tag remains historical/unspecified. | Existing golden/header/upload identity tests plus qualified capacity, all 12 public converter fixtures pass. No private DB certification. |

`power_policy.h` owns the portable production Policy, Health, Producer and
Session algorithms. `logger_power.cpp` supplies the actual RP2040 GPIO/timer/
watchdog adapter. The ISR alone owns policy and 64-bit OFF/start times. It
publishes only 32-bit fields through a seqlock; bounded readers fail closed if
interrupted by publication. No cross-core 64-bit volatile timestamp is used.

Core 1 owns producer state, queue head and heartbeat 1. Core 0 owns Session,
SdFat, queue tail, stop/run commands, card handles and heartbeat 0. Even command
tokens request stop; exact token ACK plus release ordering makes the queue head
stable. Odd tokens permit production only for the current file/power generation.
The counter does not reuse tokens on exhaustion. Final results appear as optional
`# POWER closed_generation=... clean=...` diagnostics through the existing status
snapshot; they are not authority. Network/SD/Serial work is never called in ISR.

32-bit queue index subtraction deliberately wraps at 2^32 and is tested across
that wrap with less than capacity outstanding. Health's signed modular 32-bit low-ms differences
accept a heartbeat published just after the ISR captured its time; they
are checked every IRQ and latch failure; they are not long-duration deadlines.
Power deadlines remain 64-bit; a lifetime wrap is outside the hardware contract.
The seqlock cannot make a full sequence wrap during a normal bounded read;
a system stalled that long will have reset on the watchdog.

## Installed SDK audit and limits

Audit target is the actually compiled Arduino-Pico 6.1.0 installation under
`~/.arduino15/packages/rp2040/hardware/rp2040/6.1.0/`, not an assumed SDK version.

- `cores/rp2040/main.cpp`: SDK/USB initialization precedes launch; core 1 launches
  before core-0 user `setup`. Therefore the first `setup1` hook does not prove
  power-on-to-HOLD <=750 ms or one-second raw IGN pulse retention <=900 ms.
- `pico-sdk/src/common/pico_time/time.c`: pool affinity is set from the creating
  core; pool IRQ uses a striped spinlock. `hardware_alarm` SDK dispatch is also
  avoided. Our `hardware_alarm_claim_unused(false)` is startup-only; per-core
  `irq_set_exclusive_handler` / enable is on core 1, with direct alarm register
  clear/rearm in ISR. The 32-bit compare wraps naturally; measure that path too.
- Qualified ELF disassembly of `tick()` calls only `time_us_64`, the installed
  64-bit divide/memcpy wrappers, atomic-read helper and `watchdog_update`.
  GPIO, alarm register writes and policy/health are inlined. No mutex, SDK alarm
  dispatcher, Serial, storage, network or allocation calls appear. This is a
  source/compiled-code audit, not a worst-case execution-time measurement.
- Sketch interrupt masking covers only pulse counter copies/reset. SPI helper
  masking occurs on core 0 and its registered-GPIO IRQ paths, not our alarm.
  Application has no flash programming or `idleOtherCore` call. Adding either
  needs a renewed timing review; ISR instructions still execute from XIP flash.
- `CoreMutex.cpp`, `SerialUSB.cpp`, `wiring_analog.cpp`, and SDK `mutex.c` show
  USB/ADC/status/mailbox foreground paths still take SDK mutex/spinlock sections.
  `Serial.availableForWrite()` is **not** a promise of lock-free USB output.
  Normally the interrupt-disabled portions are short, but a core stopped while
  owning a shared SDK spinlock can leave core 1 spinning with interrupts masked.
  The dedicated alarm removes its own shared lock dependency, not this broader
  SDK failure mode. Hardware watchdog reset, rather than the 5 ms ISR, is the
  fallback then. **An arbitrary masked-IRQ/core lockup is not proven to satisfy
  the <=10 ms or <=1801 s release targets.** This is an explicit remaining
  firmware qualification issue, not closed by passing native tests. Test and
  review the fault envelope before automatic-power acceptance.

## Validation and reproducibility

All commands below run from repository root. No configured secrets, flashing,
bench/vehicle operations, receiver requests or DB writes were performed.

```sh
python3 logger/tools/test_native.py
python3 logger/tests/check_power_converter.py
python3 logger/hardware/power/check_max_on_logic.py
python3 logger/hardware/power/check_cutoff_margins.py
python3 logger/hardware/power/check_interface_contract.py
python3 logger/hardware/power/check_component_margins.py
python3 logger/tests/build_power_candidates.py --output /tmp/lra05-candidates-final2
git diff --check
```

- All **nine native suites pass** (eight existing plus `power_policy_test.cpp`).
  Tests compile the production shared algorithms, not an independent policy
  model. Integrated producer/queue/tail/session test drains split chunks to an
  exact expected file and excludes stale-generation bytes. IO mocks inject
  deterministic call completion/failure; they do not emulate the SdFat driver
  or electrical GPIO timing. Clock adjustments cannot enter Policy: its only
  time input in production is monotonic, separate from existing SNTP/host time.
- The power native suite also passes GCC AddressSanitizer and UndefinedBehaviorSanitizer
  (`-fsanitize=address,undefined -fno-omit-frame-pointer`), with no findings.
- **12 converter cases pass** with the unchanged public `cardconv.py`, temporary
  synthetic input/output only. No permanent fixture was added to server scope.
- **44 electrical checks pass** (11 + 8 + 14 + 11), including the eleven unchanged
  imported artifact hashes. These are the prior model/margin checks, not new
  firmware runtime qualification.
- Both builds use the unchanged `logger/tools/build_candidate.py` through a
  test wrapper that stages source copies. Only the qualified copy changes the
  config default from `0` to `1`. All twenty manual source hashes were checked
  against the checkout; every other qualified source hash is identical.
  Arduino CLI **1.4.1**, commit `e39419312`; Arduino-Pico **6.1.0**;
  bundled SdFat **2.3.1**; ARM compiler **GCC 16.1.0**, tool package
  `pqt-gcc/5.0.0-9576866`; FQBN **rp2040:rp2040:rpipicow**.
  Profile **DUMMY-CREDENTIALS-DO-NOT-FLASH**. No build blockers; zero warnings.

| Mode | Flash bytes | Global RAM bytes | UF2 SHA-256 (local compile artifact only) |
|---|---:|---:|---|
| Manual (0) | 394256 | 103392 | `f6baa4924bfbc6d7297eb9d0bee00dc4aa7f01dd2cdb2297a2bc519ac9416d97` |
| Qualified (1) | 396628 | 103872 | `c35fbfb7edc707d2d0b2dccd4193aff41610e5689cfc11ce0ed8ad72e4fd54b9` |

The build helper records full manifests/build logs beside each local artifact.
Binaries and generated build directories are excluded from this return. Paths
and build timestamps can change UF2 bytes on another machine; effective source
hashes below establish the candidate, rather than demanding identical binaries.

### Effective firmware source SHA-256

| Source | SHA-256 (manual/default; qualified identical except config) |
|---|---|
| `accord-logger.ino` | `2e4ccb22c5f1f7e9686bd3d9610ef6279e43cc3b63871fd719038443f938d3a8` |
| `adc_median.h` | `ee4d9251f87e7c3914e58d0291d42c58178b072e7c3c6cbc314708a10284a627` |
| `card_header.h` | `34b482065e1ce26000334811db730887de5054d66a4b5d3153f867794f9db27b` |
| `card_tail.h` | `78be99e307f86245bfd8336e0d4e00855e4501bf41e6d23ecc55c05172e7817b` |
| `host_time_frame.h` | `bc6a8471f22f3972bc991fde5560790d40fca5168954846d8aef69450068f200` |
| `logger_network.cpp` | `42f2a3f60bad335979eb4358576625e4caed6a5f4a8ca1f382593ce250757001` |
| `logger_network.h` | `3346c5d891eedd17ffdb6e89e601a227a75097f6214ca9684dd8ba6776ab021c` |
| `logger_power.cpp` | `d3486b9dda637e166587fa656905174a2b36ced0bdab3f416956f432dea9fbbd` |
| `logger_power.h` | `12d80c304c99d0a3eacbaca81ef2b161d1359a18c601f06a85e30a519a6a4f77` |
| `logger_sd.cpp` | `d5012192b9f202c2084463f3468a7cbc739f897e2265b964d52fa1c7a4beccef` |
| `logger_sd.h` | `68c8ac680aa3c6e5f07f0365551c9bb96a62fdc2606a154d18eca104beef3d9f` |
| `logger_upload.cpp` | `c3de849abc3db26c866a33e73c91a2ce051ff55de4a476bc1cbea3a3670cc376` |
| `logger_upload.h` | `e5591b48bf754ac6723ff6ea50f1c5daf0430b47c94f567a558ff168a1d6c6b0` |
| `power_config.h` | `aedd491ce3ac77157676443f111e0d7985dcf2711cde0dc40a4252c2edbf7d19` |
| `power_policy.h` | `de26bfcf946e713fa788c7195e5d994dd772937063be9ea12d14ae4d569db489` |
| `power_queue.h` | `cae78279b6cb99b40ce04bb406ca8d63999d464fb7bd575ea32ea3bcf2456827` |
| `sntp_packet.h` | `819ac923d7131d7e41ab490cbccc0d6150524e5ea8f60b371f2664fc8babbd72` |
| `upload_identity.h` | `70bcf13d643a2aad938c9ab1d7d4f78134da77cc3db5619d78a82fcbbf8bbae4` |
| `upload_protocol.h` | `758e66053281cd2468a9af7f3fc8e1cbc281a78c74bffd7ecc0242a7997f03e2` |
| `wifi_schedule.h` | `131a97fdaf2eddd8704fd1bd756afe2dbc34fa220845507350e5d9c762a0c2f7` |

Qualified `power_config.h`: `1df750536150e49c0d47908142f299eede6f846f40587f3792aa804647f493ef` (only default `1`).

## Remaining gates, requested reviews and rollback

No missing input blocks publishing this bounded candidate. It is **not a
qualified automatic-power release**. Manager/firmware review should decide:

1. Accept the direct hardware alarm allocation/priority, failure behavior and
   XIP/SDK masked-interrupt fault envelope. Quantify or remove that dependency
   before claiming the strict release bound under arbitrary core lockups.
2. Review the 8 s startup grace, 2 s two-core freshness and 4 s watchdog choice
   against actual boot, ADC, USB and worst-case SD latency. A slow card can cause
   watchdog reset and tail loss by design. Repeated bounded command completions
   count as foreground progress; a long command burst can still delay a 1 Hz
   report, even though power supervision and quiescence continue independently.
3. Review new-file-per-observed-ON, exact stop-token ACK/queue publication,
   upload invalidation and post-open revalidation. Review deliberate dropping of
   queued old-file data after media failure. The manual framing/retry policy
   remains historical; only qualified mode adopts this abandonment policy.
4. Review additive `log.power`, conditional USB byte loss and close diagnostics
   with firmware/bridge consumers. Public converter synthetic tests pass, but
   the USB mirror must no longer be assumed to be a complete card copy in
   qualified mode. No server implementation change is proposed here.

Physical work remains mandatory: power-on/one-second IGN capture through HOLD,
loaded GP6 HIGH >=2.6 V at the declared drive, measured IRQ observation/release
latency under pulse/ADC/USB/radio/SD load, watchdog both-core reset and pad release,
OFF reset/brownout/USB residual isolation, and media-removal/stall/cutoff integrity
with IGN return during real close/open operations. Repeat around the timer
compare rollover. The <=1% clock envelope and regulator/clamp, hot leakage,
parked-current, off-state isolation and BOM margins remain the electrical
review's R02–R05/B01–B07 gates; this firmware does not close them or change the
power topology. Inventory preferences and the P6KE30A stock remain inputs for
subsequent electrical work, not substitutions made by this packet.

Rollback: keep `LOGGER_POWER_QUALIFIED=0` in `power_config.h`, or compile the
reviewed base `2c52afd7b5609444641d02cd420bc252a1f494c7` in an isolated checkout for
exact pre-task firmware. The default candidate touches no GP6, installs no power
alarm, enables no application watchdog, and retains manual SD/USB behavior.
Default still includes the version/metadata update and atomic SPSC queue
implementation. Source rollback/building is separate from authorized flashing
or wiring work. Do not merge into main from this specialist branch.

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
