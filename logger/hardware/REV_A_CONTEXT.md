# Logger Rev A — current hardware and design entry point

Prepared October 28, 2026 by Codex `pcb-manager`, session
`01a17045-1855-7af2-b76a-32c2b778cd64`.
Historical bookmark: `codex resume 01a17045-1855-7af2-b76a-32c2b778cd64`.
Earlier updates: Codex `pcb-manager` `01a18447-07c2-7bb3-8318-9b276cfdb3b8`
and Claude `pcb-manager` `630dea87-5e4d-4bad-a1ff-d41b3a5f509b`.

Current summary audited October 29, 2026 by Codex `pcb-manager`, session
`01a18447-07c2-7bb3-8318-9b276cfdb3b8`.
Resume: `codex resume 01a18447-07c2-7bb3-8318-9b276cfdb3b8`.
This replaces the stale pre-LRA-03 summary; earlier wording remains in Git.

## Start here

The logger largely reuses the working accord-keyless/hondaPico circuitry,
combined with its documented logger inputs/SD and the existing IGN-controlled
hold/shutoff design. Reuse applicable blocks by default. Investigate concrete
logger-specific changes in loads, nets and powered-off behavior; do not restart
working circuit design. Separate project files and pin maps remain necessary.

- **Current task state and ownership:** [project tracker](../../coordination/PROJECT_MILESTONES.md).
- **Manager continuity:** [current handoff](../../coordination/handoffs/PCB_MANAGER_LAYOUT_HANDOFF_2026-10-29.md).
- **Existing KiCad project:** [accord-logger.kicad_pro](kicad/accord-logger.kicad_pro),
  [schematic](kicad/accord-logger.kicad_sch) and [capture notes](kicad/CAPTURE_NOTES.md).
- **Electrical completion:** [LRA-12 packet](../../coordination/handoffs/LRA-12_LAYOUT_ELECTRICAL_CLOSURE.md)
  and [readiness review](../../coordination/reviews/LAYOUT_READINESS_2026-10-29.md).

The schematic is an integrated capture candidate, not a complete electrical
freeze. Continue it; do not create a replacement project. The owner will place
and route after the electrical handoff. No fabrication-ready board exists yet.

## Fitted logger baseline

The detailed physical authority is [AS_BUILT.md](as-built/AS_BUILT.md), especially
its dated owner corrections and measurement register. Proposed changes belong
in [REV_A_INTERFACES.md](as-built/REV_A_INTERFACES.md) and the power contract;
a proposed Rev A connection is not an assertion about fitted wiring.

| Block | Current recorded fitted state |
|---|---|
| VSS | B2 → 22k/33k → GP2; upper 1N5819 clamp to Pico 3V3 |
| Tach / brake | B1 / C14 → 22k/6.8k → GP3 / GP4; upper 1N5819 clamps |
| Fuel | C11 → 7.5k/4.7k → GP26; 1k series, 1 µF and two 1N5819 clamps |
| Supply sensing | B11 → 22k/4.7k → GP27; same fitted ADC protection/filter arrangement |
| IGN | B11 feed with inline fuse, 1N5819 and measured 2.2k into opto LED; LED return B16. Collector → GP5 with internal pull-up, emitter → Pico GND, 100 nF across output |
| ADC reference | B16 to common divider-return node and Pico AGND; power-ground interaction needs explicit Rev A disposition |
| SD | SPI0 GP16/17/18/19; Pico switched 3V3. No SD bulk capacitor fitted; addition captured for Rev A |
| Power | Manual external buck arrangement; no installed/accepted automatic-cutoff circuit established |

Tap-end fuses on C11/B11 and the IGN inline fuse are recorded present. Exact
ratings and component identity/tolerances remain distinct from fitted topology.
Preserve the logger's own pin map; keyless circuitry is a reuse source, not a
reason to substitute keyless firmware assignments.

The owner's parked measurements are settled: B2 open **4.669 V**, loaded
**4.140 V**, divider junction **1.042 V**, unpowered 3V3 rail **0.883 V**.
The resulting model gives **140.8 µA** total B2 draw and **109.2 µA** clamp
backfeed. The old 75.3 µA divider-only figure is superseded. B1/C11 read zero
parked; C14/B11 were already recorded dead. These measurements narrow the
parked isolation problem to B2; other branches still need fault-state review.
Do not re-ask these readings. See tracker decision `D-OFFSTATE-01`.

## Existing design and remaining integration

The working hondaPico LM2678 supply, protection and connector examples are in
`keyless/hardware/hondaPico.kicad_sch` and its matching PCB. Its MAX3485 is
fitted and the RS-485 link was extensively exercised, owner-confirmed. Those
are working precedents, not hypothetical examples.

The existing logger power candidate is exported in [power/](power/README.md)
with original provenance. Read [INTERFACE_CONTRACT.md](power/INTERFACE_CONTRACT.md)
for precedence, then the margin review, cutoff connections and LRA-02 component
proposals. GP5 reports hardware-qualified ignition; **GP6 is HOLD**, not an open
pin choice. The older raw-GP5/100 ms/GP7-alternate proposal is superseded.
Software hold is 1800 s, independent cutoff nominally 2048 s; physical timing
and fault acceptance remain open.

The existing capture omits the detailed qualifier and cutoff even though their
connection tables already exist. LRA-12 implements them in this project and
resolves protection compatibility, input isolation/grounding and actual
parts/footprints/connectors. The added always-on A5 regulator is a specific
compatibility difference from keyless; the old TVS alone does not meet its
protected-rail requirement. This warrants a bounded correction, not a new
buck-design investigation.

[LRA-11's ASSR-601JV study](isolation/B2_ISOLATION.md) is integrated as a
conditional reference. Its temperature-specification question is closed;
enable, timing and footprint implementation remain subject to the linked review.
The complete 100/500 µA parked-current targets are not established by the
arithmetic scripts. Conditional component limits and assembled tests must remain
clearly distinguished.

The board envelope is **80 × 120 mm**, no enclosure selected; SD module
**16 × 16 mm** plus its 1×6, 2.54 mm header. Connector placement belongs to
layout. The newly captured power logic must be included in the fit check.
The inventory is partial, and the owner reports four P6KE30A not listed in it;
exact stock reconciliation can wait for parts discussions.

## Firmware and communications boundaries

Public source is the **0.8.1-lra05-dev** candidate, with
`LOGGER_POWER_QUALIFIED=0` (manual) by default. Qualified shutdown is implemented
as opt-in; it is not physically accepted or evidence of a new flash. See
[configuration notes](../NEXT_AGENT.md) and the
[LRA-05 review](../../coordination/reviews/LRA05_REVIEW_2026-10-29.md).
The masked-interrupt/watchdog release limitation remains an acceptance issue,
not a reason to treat the firmware as unimplemented.

LRA-04 supplied a comparison with outstanding corrections. LRA-12 selects a
minimal power-off-safe provision; a defined DNP expansion/daughterboard header
is permitted. Full CAN/RS-485 software, fuel calibration and dashboards do not
gate owner layout. No current bus allocation should be inferred from an offer
of spare GPIOs in an older table.

## Deeper history when needed

Source manifests, linked reviews and Git retain the original imports and later
changes. Session bookmarks identify contributors and can recover a specific
unresolved detail. They are not prerequisites for understanding current scope.
The tracker is the single task authority; this page is a hardware summary.
