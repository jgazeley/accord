# LRA-12 — finish the logger electrical design for owner layout

Prepared October 29, 2026 by Codex `pcb-manager`, session
`01a18447-07c2-7bb3-8318-9b276cfdb3b8`.
Resume: `codex resume 01a18447-07c2-7bb3-8318-9b276cfdb3b8`.
Identity verified from matching `CODEX_SESSION_ID` and `CODEX_THREAD_ID`.

**Parent:** M5. **Responsible:** one remote electrical/KiCad engineer; current
assignment/claim is recorded in `coordination/PROJECT_MILESTONES.md`.
**Reviewer/integration owner:** current pcb-manager. The owner will do layout.
The owner explicitly requested this single assignment. No bench is available
to the remote engineer and none is required to begin it.

## Starting point — working hondaPico base plus logger additions

**Owner clarification, October 29:** this board largely reuses the working
accord-keyless/hondaPico circuitry, with the logger's IGN-sense, power-hold and
automatic-shutoff addition. Treat this as integration of existing circuits.
The logger's fitted input cells and SD wiring are also existing work; preserve
those documented connections rather than substituting the keyless pin map.

Inspect `keyless/hardware/hondaPico.kicad_sch` and the matching PCB directly for
applicable supply, protection, connector and layout details. Carry reusable
blocks forward by default, recording their source and the logger-specific net,
load or lifecycle differences. The logger remains its own board/project and
keyless files remain read-only. The earlier LRA-06 “copy no circuit” wording
is superseded: separate projects do not prohibit circuit reuse.

**Bound the engineering to the additions and their interactions.** Every proposed
change to a working inherited block must identify a concrete incompatibility,
changed operating condition or documented defect. Do not make blanket redesign
or requalification of inherited circuitry a prerequisite to layout. In
particular, the new A5 supply's compatibility and paths that could feed a
powered-off Pico need resolution because the shutdown addition changes those
conditions. The work order below is a completion checklist for that integration.

## Objective and completion boundary

Return a **complete, footprint-assigned logger schematic and consolidated BOM**
that the owner can import into PCB Editor and place/route on the agreed
80 × 120 mm board. Resolve the remaining electrical choices and capture them.
This is the completion of existing work, not a new power-design survey and
not another paper-only proposal. Leave placement/routing to the owner.

It is not a requirement to prove lifetime vehicle qualification before layout.
Separate layout blockers from explicit fabrication/bring-up tests. Do not hide
known incompatibilities behind “prototype,” an unconnected symbol, or a test
that cannot reasonably be performed on the resulting board.

## Repository, base and owned paths

Repository: `https://github.com/jgazeley/accord`. Fetch public `main` containing
this packet and record its full SHA in your handoff. Branch:
`task/LRA-12-<your-short-session-id>`. Use an isolated checkout/worktree.

One claimed edit scope:

- `logger/hardware/kicad/`: schematic, local libraries, BOM, checks and exports.
- `logger/hardware/isolation/`: corrected implementation and enable analysis.
- `logger/hardware/communications/`: minimal expansion/service disposition.
- New `logger/hardware/power/LAYOUT_CLOSURE.md` and any new bounded verification
  script; update the active `INTERFACE_CONTRACT.md` only where a decision needs
  it, with an attributed change record.
- `logger/hardware/LRA12_HANDOFF.md`: final evidence and residual gates.

Root/coordination stays with the manager. Read firmware to check pin/timing
feasibility, but do not edit or flash it in this assignment. Do not modify
keyless, other agents' worktrees, the fitted as-built record, or files pinned
as historical exports by a `SOURCE_MANIFEST.json`. Put corrections to those
sources in `LAYOUT_CLOSURE.md` and the new capture; preserve their provenance.
Claim with your own verified tool/session identity in your first handoff update
and report it to the manager; only the manager records the tracker claim.

## Minimum entry reads

1. [Layout-readiness review](../reviews/LAYOUT_READINESS_2026-10-29.md): current
   dispositions and the precise errors to avoid. This supersedes earlier
   “LRA-11 is the only blocker” and “no source for X6/X8” statements.
2. `logger/hardware/power/INTERFACE_CONTRACT.md` §§1–3, 6–9: existing architecture,
   source precedence and limits. Its references lead to the already-designed
   clock, latch, reset and qualifier. **Do not read only DESIGN.md/BOM.csv.**
3. `logger/hardware/kicad/CAPTURE_NOTES.md` §§2, 5–7 and the actual schematic/BOM:
   what is present and which placeholders/questions remain.
4. `logger/hardware/as-built/REV_A_INTERFACES.md` §§1–6, read against current
   tracker decisions `D-OFFSTATE-01`, `D-ENVELOPE-01`, `D-KEYLESS-485-01` and
   `D-POWER-03`. Later owner measurements override the older inferred states.

Targeted source files for each work item are below. Everything required is in
public `main`; the historical private repository, transcripts and full inventory
are not prerequisites.

## Work order — one engineer completes these together

### 1. Replace the missing power blocks with the existing circuit

Capture X6 and X8 using `CUTOFF_MARGIN_REVIEW.md` §§1–3,
`MAX_ON_CUTOFF.md` connection table and HOLD-path switch section, then the
LRA-01 contract and LRA-02 `COMPONENT_MARGIN_CLOSURE.md` / `BOM_DELTA.csv`.
Retain QP before LM2678, direct QI startup, independent A5 clock/counters/latch,
qualified IGN on GP5 and HOLD on GP6. Implement QMON before JH, QS between
SINK and QH collector, and QREPORT with its switched-3V3 pull-up. Do not use
the obsolete raw-GP5/100 ms contract or resurrect the superseded bare crystal.

Consolidate the BOM rather than telling the layout owner to merge three CSVs.
Resolve supporting passives, unused gates, bypasses, test points and real
packages, including the LRA-02 capacitor/UOE and paired QP/DZ decisions.
PCB-mounted SMD parts need footprints, not breadboard adapter placeholders.
Keep the maintenance HOLD link and an accelerated-cutoff test provision clearly
distinguished from the production timeout selection.

### 2. Close the genuine power-input compatibility gap

Reuse the operational keyless LM2678/1.5KE30A evidence and the existing logger
switching topology. **The new always-on A5 supply is a real difference.**
Resolve X7 so the selected protection, A5 regulator, QP/DZ, QI/QH, caps and IGN
input share a stated, compatible voltage envelope. The existing contract calls
for protected P12 ≤28 V; a 41.4 V TVS clamp alone does not satisfy it.

Select a bounded correction with primary-source limits and calculations;
explain any necessary deviation from the retained candidate. Include fuse
coordination, clamp tolerances/current conditions, gate stress, dissipation,
and the regulator/inductor/output-cap choices that affect footprints. Do not
claim a keyless in-car success proves every new logger rail safe. Conversely,
do not restart the buck architecture without a demonstrated unmet requirement.

Carry the whole-system current ledger with explicit conditional values and
remaining measurements. Do not silently change the 100/500 µA targets or count
typical values as maxima. Distinguish an unproven assembled budget from a
known component bound that cannot fit it; resolve the latter or report a precise
tradeoff for review.

### 3. Implement isolation and dispose every remaining input placeholder

Use `isolation/B2_ISOLATION.md`, its script and the manager's follow-up.
**ASSR-601JV's leakage-temperature scope is settled.** Do not spend another
pass asking Broadcom to restate its explicit table header. Complete the actual
driver: GPIO enable plus hardware PGOOD permission, or an electrically justified
equivalent. Preserve fail-open-on-BAD; do not assume BAD drops B5 with QI on.
Name the driver parts, pin numbers, LED-current bounds, startup/reset defaults,
power-domain crossings and shutdown sequence. Account for absent Pico 3V3 with
B5 still present, USB-only power, normal shutdown and unexpected rail collapse.

GP7 is available and is the preferred ISO_EN reservation if the current source
audit confirms it remains free. Publish the pin/sequence contract and required
firmware follow-up in the handoff. Hardware must stay safe before that firmware
exists; describe how bring-up tests it. Check that settle/isolate delays fit the
existing shutdown budget; the 5/20 ms proposal is not a guaranteed timing proof.

Create and verify the actual local ASSR footprint/symbol from the manufacturer
drawing, including absent leads and externally unconnected pin 3. Use the
specified test conditions correctly for leakage, LED drive, R_ON and timing.

For X2–X5 (tach/brake/fuel/supply), produce a reachable-state table and **make
a decision for each**: justified bypass or selected protection/isolation. They
measure dead while parked, so no blanket five-relay requirement follows. That
does not answer energized-input/dead-rail faults. Preserve the fitted divider
ratios and loading unless a concrete defect requires change. Resolve D11's
tach clamp margin with limits, not an invented source measurement. If series
resistance affects ADC calibration, publish the metadata consequence rather
than silently changing the effective ratio.

### 4. Resolve grounding and connector questions in the drawing

Close R06-REV-2/Q2: the opto LED power return and B16 ADC reference cannot
remain an unexplained conflict. Start with the power design's PGND LED return;
check reverse clamp placement and input voltage/CTR margins for the measured
2.2k resistor. Keep B16 as a sense/reference connection, not a supply return.
Account explicitly for ground connections already inside the Pico module;
separate net labels alone do not isolate those conductors.

Select J1/J2 connector parts, footprints, pin numbering and mating housings.
Molex Mini-Fit Jr is a documented in-service family; JAE IL-AG5 is another
precedent. Make a reasonable project choice without another inventory survey.
Connector placement is the layout owner's choice. Clarify tap-end fuses versus
any secondary onboard FIGN; an onboard fuse cannot protect upstream harness.
Resolve J4: either a useful isolated/DNP UART0 provision or a defined RUN/GND
reset header, not a contradictory “service UART” with NC pins.

### 5. Bound communications so it cannot hold the PCB hostage

Use the existing LRA-04 return/review; do not redo the general bus comparison.
The keyless MAX3485 and protocol were physically exercised. Resolve the two
actual contradictions: tied DE//RE does not reach shutdown, and supply current
does not prove powered-off bus leakage. A **DNP daughterboard/expansion header
is an allowed Rev A solution** if onboard bus circuitry would keep this task
open. Select one provision, exact GPIOs/pinout/footprint and population policy.
No connected external powered bus or service pull-up may bypass the off-state
contract. With a DNP fallback, document the disconnected interfaces and limits;
do not claim bus interoperability. Full CAN hardware/software is not required.

### 6. Deliver a design the owner can actually lay out

Retain `accord-logger.kicad_pro`, project-local libraries and designator/source
mapping. Update or explicitly retire generators so they cannot overwrite the
finished schematic with the old placeholders. Export fresh netlist, ERC and
SVG/PDF; visually inspect the schematic. Assign every populated part a checked
footprint, including pad-number/polarity mapping for semiconductors and modules.

Check physical feasibility on **80 × 120 mm** after adding the missing power
logic. The earlier area estimate omitted those components. Include Pico antenna
keepout, USB/SD access, SD module overhang, power/analog separation and generic
corner mounting-hole clearances. Supply an annotated floorplanning guide or
courtyard study; leave final placement and routing to the owner. Do not silently
enlarge the board. If it demonstrably cannot fit, return dimensions and a concrete
package/envelope trade rather than another unspecified mechanical blocker.

## Acceptance and evidence

| Check | Expected result / artifact |
|---|---|
| Schematic completeness | No X1–X8 electrical placeholder remains. Each has a real circuit or an explicitly justified removal/bypass. Required autonomous power is present |
| Interface coherence | One GPIO/domain/enable/state table, preserved current contract or explicit reviewed delta; no 5 V GPIO pullups or unexplained alternate power paths |
| BOM/footprints | One population BOM with exact MPN/package or a precise interchangeable passive specification; selected connectors and verified pad mappings; no hidden mandatory TBD |
| ERC and net audit | Fresh ERC JSON with zero unresolved errors, disposition every warning, exported netlist checks for physical connectivity/polarity and cutoff paths |
| Checks | Rerun applicable existing power, capture and isolation scripts. Update capture assertions for the new intended circuit. Add meaningful state/corner checks, not merely assertions mirroring a parts table |
| Layout handoff | Fit/keepout guidance, high-current loops, return strategy, trace/rule requirements, test points and assembly constraints sufficient for owner placement/routing |
| Residual risks | Each is classified as layout blocker, fabrication gate or bring-up/vehicle test; concrete test/provision and limit. No blanket “needs bench” deferral of a design decision |
| Publication | Review exact staged contents for public-safe material; stage only owned paths; own attribution; pushed task branch and full commit IDs |

`logger/hardware/LRA12_HANDOFF.md` must list decisions, changed artifacts,
commands/results, tests not run, remaining risks, firmware follow-up, and the
exact KiCad entry point. State whether the electrical layout handoff is ready.
A candidate is not an accepted board. If a real blocker remains, name its exact
net/part/requirement and the smallest decision needed; preserve all completed
work on the task branch instead of expanding into another broad investigation.

No purchase, fabrication, physical wiring, bench operation, firmware flash,
deployment or database change is authorized. The original inventory is partial
and may contain consumed stock; the owner also has four P6KE30A. Neither exact
inventory nor ordering parts is a prerequisite for this design assignment.

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
