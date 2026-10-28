# Returning power engineer — remote continuation, October 25, 2026

Read this, then `REVIEW_2026-10-25.md` and `MAX_ON_CUTOFF.md`. The original
engineer bookmark in README refers to the predecessor, not this remote
continuation. This work was done on a different machine with repository and
transcript access, **no bench, car, instrument or deployed-machine access**.

**Latest continuation after 8937ccb:** read `CUTOFF_MARGIN_REVIEW.md` with
the revised `MAX_ON_CUTOFF.md` and BOM. It replaces the bare crystal,
diode-precharge filter and TPS7A16 proposal. It adds eight conditional margin
checks to the eleven logic checks. The historical scope below describes the
first checkpoint; the current remaining items are at the end of this file.

## Provenance and accountable scope

Base commit: `e7415c9` on master. Commit author configured by the owner:
`Jayson Gazeley (Remote Codex) <jayson.gazeley@gmail.com>`.
The owner explicitly requested committing reviewable progress. Use
`git log --oneline -- logger-power/` to locate this checkpoint and its diff;
its commit message is `logger-power: record remote review and cutoff candidate`.

The transferred rollout is
`rollout-2026-10-25T08-54-01-01a173c4-d2fd-7f71-a396-8996d502387b.jsonl`.
It remains outside the checkout; the remote review records where the original
session stopped. The five original deliverables matched that transcript's
successful patches before this continuation's changes. No original physical
results were discovered. The owner-supplied inventory is included unchanged
as a reference snapshot, not a fresh count or verification of unused stock.

Transferred rollout SHA-256:
`5ea45021efb348aa460c7afb8e89c25c9d3a69c1c97736cfe676cf1674f7e65c`.

This checkpoint contains:

- Source-review corrections to firmware startup/scheduling, shutdown races
  and watchdog timing, plus corrected handoff and test instructions.
- Owner decisions: onboard supply; auxiliary battery for testing; eventual
  starter-battery preference near the cluster; through-hole preferred with
  SMD acceptable.
- A proposed 2048 s independent cutoff, component connections, incremental
  candidate BOM, failure boundaries and conditional timing calculations.
- An executable Boolean specification with 11 passing checks, including
  reduced-count reachable-state coverage and brownout at every active count.
- Explicitly unresolved supply/reset/clock and interface questions. The
  candidate is not merged into revision A's authoritative wiring/BOM.

Only `logger-power/` artifacts are changed. No other owner's firmware or
hardware artifacts, shared coordination or `circuits.md` were edited. No
flash, deployment, purchase, physical assembly or measurement took place.
The commit establishes a reviewable engineering checkpoint, not circuit
approval, completed M2, or PCB fabrication readiness.

## Remaining remote work, in priority order

| Work | Concrete deliverable | What still requires local evidence |
|---|---|---|
| Close cutoff component choices and margins | Temperature-rated clock selection; worst-case reset/precharge and ignition thresholds; A5 input-collapse/reverse-current solution; complete leakage and gate-drive budget with 10k RGS | Clock startup/drive, ramp behavior, actual hot leakage and cutoff waveforms |
| Resolve firmware/hardware IGN qualification | One explicit timing/polarity contract and an owner-review patch if firmware documentation needs changes; account for pulses accepted by only one detector | Firmware-owner agreement and combined timing tests |
| Design automatic off-state signal isolation | Per-input circuit and parts for VSS/tach/brake, fuel/cluster ADCs, IGN, USB and future bus; input loading, analog error and unpowered leakage calculations | Installed signal levels, ground offsets and connected off-current |
| Finish the power/protection BOM | Exact capacitor series/ESR/ripple ratings, inductor/fault coordination, switch drive/inrush analysis and proposed starter-feed protection envelope | Actual load envelope, harness/fuse details, thermal and transient tests |
| Capture a coherent schematic | Power-owned KiCad capture with reviewable export and ERC findings; reconcile revision A, cutoff and incremental BOM | Physical prototype validation before layout/fabrication claims |
| Keep owner handoffs actionable | Bounded firmware/fuel/board interface requests as documents or patches within this folder | Their acceptance and physical implementation |

Bench access is not a prerequisite for those design tasks. Do not send
unresolved paper calculations to the owner as though they were measurements
only the owner could provide. Conversely, passing the Boolean checks does
not settle analog margins or transistor behavior.

First priority is the cutoff's known gaps, not new PCB layout. In particular:

1. The listed AB38T is a room-temperature experiment part, not an 85 C clock.
2. IGN_RC precharge during reset is unproven at worst-case electrical limits;
   an empty capacitor can otherwise falsely grant IGN at boot.
3. A5 reverse-current protection and supply-collapse behavior remain open.
4. Firmware's proposed 100 ms qualification and the RC detector are not yet
   equivalent. A mismatch can cause a hard cutoff before firmware expects it.
5. The candidate now uses 10k RGS and retains the 0.2 V off-gate criterion.
   Recompute all on-state gate/clamp currents and the complete leakage budget.

## Checks and handoff procedure

From the repository root run `python3 logger-power/check_max_on_logic.py`.
The 11 checks cover settled logic and arithmetic only; they do not test
propagation hazards, analog startup, transistor faults or power integrity.
CSV field counts and `git diff --check` were also checked. Every physical
test remains PENDING in `PROTOTYPE_TEST_PLAN.md` and `MAX_ON_CUTOFF.md`.

Follow root README ownership rules. Stage explicit paths. Pull/rebase and
inspect status around work; if there are local edits, preserve them before
integration. Cross-owner changes remain proposed patches. Reconcile this
checkpoint with any newer local work instead of overwriting either version.

## Current handoff after the margin review

The follow-up task was explicitly authorized to address clock, reset/IGN,
reverse-current supply behavior and leakage/gate calculations. Selected an
OV-7604-C7 TA oscillator, filtered VCLK with tolerant interfaces, a filter
whose empty capacitor means OFF, reset discharge, shared qualified GP5,
and TPS70950-Q1 with a defined protected-input boundary. Recomputed gate
drive and published a conditional current ledger. All 19 remote checks pass.

Not fully closed: exact effective-capacitance proof for clock/LDO capacitors;
actual clock startup/load bounds over temperature; hot opto and QI/QS limits;
guaranteed whole-logger parked current; vehicle protection meeting P_AON's
28 V design ceiling/30 V IC limit; and firmware-owner acceptance. The static
screening sum already exceeds the former 40 µA timer allocation. Do not
describe the entire cutoff design as complete or move to fabrication.

The next remote design decision is whether to reduce the safeguard's worst-
case current/part count or explicitly rebudget the rest of the logger while
retaining the whole-system target. That decision should precede final capture
of this candidate. Signal isolation and the full buck/protection BOM remain
the following work items. All physical acceptance remains local.
