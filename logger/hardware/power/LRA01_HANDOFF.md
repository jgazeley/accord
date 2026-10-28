# LRA-01 electrical return to pcb-manager

Prepared October 28, 2026 by Codex `logger-power`, electrical lead.
Session: `01a18463-5ed7-7041-ad90-ec3a7480c4e6`.
Resume: `codex resume 01a18463-5ed7-7041-ad90-ec3a7480c4e6`.
Verified from matching session/thread environment IDs. Owner explicitly assigned
this scope and requested publication on a task branch; no manager availability
is required to return the candidate. This document acknowledges that claim;
manager alone updates `coordination/PROJECT_MILESTONES.md`.

Branch: `task/LRA-01-01a18463`, based on public
`25cebe8afab20dc675ca70ef6f25fd396175ee6e`.
Identify the return commit with `git log -1 --format=fuller --
logger/hardware/power/INTERFACE_CONTRACT.md` on that branch; the final response
also supplies its exact hash. No merge into main is performed.

## Delivered and disposition

[INTERFACE_CONTRACT.md](INTERFACE_CONTRACT.md) is the electrical **candidate**
for LRA-01. Original `9527a14` design files and their manifest remain unchanged;
no new historical engineering artifacts were imported. Firmware source was
read only. The current firmware behavior was inspected independently, but
this session has not claimed the separate firmware-review gate.

Concrete decisions:

- Retain the existing switched-input buck, latch/counters, clock and A5 topology.
  Use hardware-qualified GP5 and select GP6 HOLD; remove the old competing
  raw-IGN/100 ms rules. Increase the HOLD current allocation to 4 mA because
  3 mA lacks a resistor-only worst-case bound. Use a 2.6 V HOLD HIGH
  qualification target with conditional transistor-drive calculations;
  RP2040's published 2.62 V VOH at 3.3 V does not support the old 3.0 V claim.
- Specify a <=900 ms measured retention target for a one-second raw IGN start,
  with explicit A5/supervisor/filter/Pico budgets. Define 1770/1800/1801 s
  finalization/release, monotonic-clock allowance, IGN-return generations,
  reset/USB rules and watchdog/fault exclusions.
- Retain TPS709 and require coordinated P12/P_AON <=28 V. Reject the 41.4 V
  TVS as sole protection. A lower-clamp part's nominal table is insufficient
  to approve automotive surge protection. Keep bounded 12–16 V bench scope.
- Preserve 100/500 µA whole-system targets. Propose explicit new allocations;
  identify the A5 subtotal and QP hot-leakage screen that prevent a guaranteed
  budget claim. Do not substitute measured 5 V running current.
- Require upstream isolation of the five signal branches. Select a limited
  DOR candidate change, 1N5819 to Vishay 1N4004-E3/54, for its lower specified
  reverse leakage; forward drop, thermal and recovery tests remain required.

## Validation

From the repository root:

```sh
python3 -B logger/hardware/power/check_max_on_logic.py
python3 -B logger/hardware/power/check_cutoff_margins.py
python3 -B logger/hardware/power/check_interface_contract.py
```

Results: **11 + 8 + 14 = 33 checks pass**. The new tests cover abstract
boot/reset/no-rearm, failed/missing close, stale-generation rejection, ON at
release, missed qualified return, long monotonic uptime, startup composition,
clock-drift reserve, current/diode screening and explicitly unresolved gaps.
They exercise a contract model and inherited settled hardware logic, **not
firmware implementation, electrical simulation or physical acceptance**.

All eleven imported files verified against `SOURCE_MANIFEST.json` SHA-256;
no changes to their original bytes. `git diff --check` passes. Exact staged
paths/content were inspected before commit/publication. No credentials,
configured binaries, private recordings, third-party PDFs or runtime data
are part of this change. No configured build or hardware test was performed.

## Remaining gates and required reviews

| Gate | Next owner/action |
|---|---|
| Firmware agreement (R01) | Acknowledged firmware reviewer writes `FIRMWARE_REVIEW.md`: GP6/drive, early core startup and <=10 ms supervision, clock envelope, shutdown generations/SD ownership, IGN semantics/metadata and watchdog |
| Protection (R02) | LRA-02 closes P12/IGN limiter/clamp/fuse/energy ratings; owner supplies eventual feed, transient and crank/jump-start requirements |
| Component limits (R03) | LRA-02 specifies capacitors and hot devices, loaded logic levels, oscillator startup/load and LDO all-load behavior; do not defer datasheet gaps as merely bench work |
| Parked budget (R04) | Manager/electrical review new allocations; LRA-02 closes condition-specific leakage or changes offending parts with justification; bench measures all sources |
| Isolation (R05) | LRA-02/03 review each actual input range/loading, upstream disconnect components, DOR tradeoff and ground paths; LRA-04 covers service/bus boundaries |
| Physical evidence (B01–B07) | LRA-07 after a reviewed circuit and LRA-05 candidate: startup/qualification/ramp corners, cutoff/stuck HOLD, reset/watchdog, SD-return races, leakage/thermal/decay |

Electrical disposition: **candidate, not accepted or fabrication-ready**.
Firmware disposition: **pending; not supplied by this electrical review**.
Manager should record this claimant and returned commit, dispatch firmware
review, and carry the numbered R/B gates into LRA-02/03/05/07. No need to
reconstruct or restart the power topology research. Source publication does
not authorize hardware deployment, fabrication, live firmware changes or DB
writes.

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
