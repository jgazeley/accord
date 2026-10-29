# LRA-11 — stop B2 energizing the board while it is parked

Prepared October 29, 2026 by Claude `pcb-manager`, session
`630dea87-5e4d-4bad-a1ff-d41b3a5f509b`.
Identity read from this session's harness-assigned working paths.

**Parent:** M5. **Responsible:** analog/electrical reviewer, unclaimed.
Current pcb-manager integrates; `coordination/PROJECT_MILESTONES.md` owns state.

This is the resolution of **D4**, carved out of LRA-02 because it is the single
item on the critical path: it blocks LRA-08, and LRA-08 blocks everything after.

## Read this first: this is much smaller than the documents say

`REV_A_INTERFACES` §3 describes D4 as isolation on **all five** vehicle
branches and calls it "the largest Rev A design item." **That was written before
the owner measured the car on October 29.** Three things changed:

1. **Four of the five branches are dead when parked.** B1 and C11 measure 0 V
   key-out; C14 and B11 were already on record as dead. **Only B2 is live.**
   Those four are now "under analog review" with the parked-drain argument
   withdrawn — deciding their fate is *not* this task.
2. **The leakage budget relaxed five-fold.** The 8 µA / 20 µA allocation was for
   five branches together. One branch needing isolation gets **all of it**.
3. **B2 is a digital pulse input.** The ≤25 Ω fuel and ≤100 Ω supply top-leg
   limits in §3.4 item 4 **do not apply to this task** — those were C11 and B11.

So the documents will read harder than the job is. Where §3 and this packet
disagree about scope, **this packet is current**.

## What was measured, and why it matters

Everything seated, Pico unpowered, key out, car parked. Four readings, no
assumptions left:

| | |
|---|---|
| B2 open-circuit | **4.669 V** |
| B2 loaded at the tap | **4.140 V** |
| 22k/33k junction | **1.042 V** |
| 3V3 rail (clamp cathodes) | **0.883 V** |

Which gives: parked source **3,757 Ω**, total draw **140.8 µA**, of which only
31.6 µA reaches ground through the 33k and **109.2 µA is back-fed through a
forward-biased clamp into the Pico's own 3V3 rail.**

**The problem is not mainly a current budget.** One branch is 141 % of the whole
100 µA system parked allowance, which is bad enough. But the board is also
**partially energized while it is meant to be off** — the clamp is powering a
dead rail to 0.883 V. `REV_A_INTERFACES` §6 says nothing in its off-state
matrix is established; this row now is, and it fails.

## Objective

**Stop B2 injecting into the unpowered board, within budget, without breaking
the VSS signal.** Return a selected part or topology with a datasheet-backed
case, plus a fallback.

Note the objective is an *outcome*, not "pick a switch." A series switch is the
obvious shape, but **the solution space is open** and two non-switch directions
are legitimate and unexplored:

- **Raise the divider impedance.** The ratio sets the logic level and must hold,
  but §2's "do not reduce the 55 kΩ" is a floor, not a ceiling. Less available
  current means less clamp conduction. Likely insufficient alone — ~10× gets to
  roughly 14 µA, inside the hot budget but not the cold one — and high impedance
  costs noise immunity and edge speed on a pulse input. Possibly viable combined
  with something else.
- **Change the clamp topology.** The back-feed path *is* the clamp into a dead
  rail. A clamp that does not reference the switched 3V3 rail removes the
  mechanism rather than starving it.

Say which you chose and why the others lose. A reasoned rejection is a result.

## The specification

1. **Normally open with no power applied, by construction** — not by a pulldown.
2. **Off-state leakage specified as a maximum**, not a typical, at 4.67 V, at
   20–30 °C and at 85 °C. Budget: **≤8 µA cold, ≤20 µA hot.** A datasheet giving
   only a typical does not satisfy this, whatever the number.
3. **Withstand 16 V with its own supply at 0 V** — the charging-fault case.
4. **Pass the VSS signal undistorted.** Pulses 0 V to about 5 V or more, ~91 Hz
   at 80 mph, nothing below ~2 km/h. No edge artefact within **100 µs**, the
   firmware's `GLITCH_US` rejection window. The upper pulse amplitude is **U-06
   and unmeasured**; 16 V withstand covers it, so this does not block you.
5. **Switch reliably at low level.** The branch carries **140.8 µA at the tap
   and 1.042 V at the divider junction** — measured, so no longer an estimate.
   Mechanical contacts need a **dry-circuit** rating; this is well below the
   wetting current of ordinary contacts.
6. **Enable only from a rail that exists** in the Rev A domains, and **open
   before HOLD releases**, so shutdown is isolate-then-release.
7. **Fail open on supervisor BAD**, with no software step.

## Dead ends — do not re-screen these

- **Latching relay.** Rejected. It holds the input connected through an
  unplanned power loss, which is the exact entry condition this exists for.
- **ADG5412F-class analog switch.** Screened and **not** selected: 8 V minimum
  supply rules out running it from B5, and its power-off leakage is *typical*,
  not a maximum. A replacement must fix both.
- **The inventory list.** `/srv/agent_share/inventory/inventory_list.md` has no
  power-off-protected analog switch and no contacts specified for dry-circuit
  work. The owner says it is **incomplete and may list consumed stock**, so
  absence from it proves nothing. **Stock is not a suitability argument, in
  either direction.** Do not let a parts hunt become this task.

**One class got cheaper and deserves a fresh look.** A *non-latching* signal
relay with gold-clad contacts was never rejected — its cost was coil current
while energized, budgeted against five of them. **At one branch that cost falls
five-fold.** §3.3's objection was written for the five-branch case and no longer
applies at the same weight.

## Minimum context

Three reads. Nothing else is needed and the rest of the tree will mislead you,
because most of it predates the measurements.

1. `coordination/PROJECT_MILESTONES.md`, decision **`D-OFFSTATE-01`** — the
   measurements and what they changed. Start here.
2. `logger/hardware/as-built/REV_A_INTERFACES.md` **§3.3 and §3.4** — candidate
   classes and the seven requirements, **read against the scope correction
   above**; and **§2**, the B2 row only, for signal and loading.
3. `logger/hardware/as-built/AS_BUILT.md` **U-07, U-08, U-10, U-14** in §6 —
   the measured detail, including the clamp's 159 mV at 109 µA.

The captured schematic is at `logger/hardware/kicad/`; X1 is the placeholder
you are resolving. The board is a generic **80 × 120 mm** rectangle
(`D-ENVELOPE-01`), so a physically large part is a real cost but not fatal.

## Deliverables

Into `logger/hardware/isolation/` (yours; everything else is read-only):

- `B2_ISOLATION.md` — the recommendation, the rejected alternatives with
  reasons, the datasheet-backed leakage/withstand/timing case, the enable path
  and its rail, failure behaviour on supervisor BAD and on unplanned power
  loss, and the fallback.
- A footprint and package proposal concrete enough for LRA-08 to place X1.
- Any arithmetic as a checkable script, following `logger/hardware/power/`
  practice.

## Acceptance

| Check | Expected |
|---|---|
| Parked injection | Shown ≤8 µA cold / ≤20 µA hot from **specified maxima**, at 4.67 V |
| Back-feed | The 109.2 µA path into the unpowered 3V3 rail is eliminated, not merely reduced |
| Withstand | 16 V with the part's own supply at 0 V, cited |
| Signal | VSS passes; no artefact within 100 µs |
| Low-level switching | Dry-circuit rating cited if contacts are used |
| Enable | Named existing rail; opens before HOLD releases; fails open on BAD |
| Placeable | Package and footprint concrete enough for X1 |

## Authorized and unauthorized

**Authorized:** documentation and datasheet research; create
`logger/hardware/isolation/`; propose a part, a topology or a divider change
with its reasoning; commit to `task/LRA-11-<your-session-short>`.

**Unauthorized:** changing anything outside your directory, including the
schematic — X1 stays a placeholder until this is reviewed and integrated;
deciding the fate of X2–X5, which is a separate analog-review question;
touching R06-REV-2, the opto LED return; purchasing; any hardware, bench or
vehicle action. This packet authorizes no fabrication and no freeze.

## Dependencies and next action

**Nothing blocks starting.** U-06 is unmeasured but the 16 V withstand covers
it. U-08 is only partially closed, but the parked source is measured and that
is the case that matters here. R02–R05 remain open and do not gate this.

**This blocks LRA-08**, which is otherwise ready: the schematic is integrated
and the envelope is fixed.

Next action: claim the row in `coordination/PROJECT_MILESTONES.md` with your
tool, role and session, then read `D-OFFSTATE-01`.

> **Required agent attribution:** Follow `logger/coordination/AGENT_ATTRIBUTION.md`
> relative to this repository root. Use your own tool, role and verified current
> session ID for Git author and committer (`<Tool> <role> [<short-id>]`), using
> per-command settings. End commits with `Agent-Session: <role>` and your full
> tool-specific session-ID trailer. Identify yourself and your resume command in
> coordination documents and dated updates. If an ID is unavailable, state that
> explicitly; never invent or borrow one.
