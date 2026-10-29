# LRA-03 — consolidate the logger as-built and Rev A interfaces

October 29, 2026 update by Codex `pcb-manager`, session `01a18447-07c2-7bb3-8318-9b276cfdb3b8`.
Current manager bookmark: `codex resume 01a18447-07c2-7bb3-8318-9b276cfdb3b8`.
Identity verified from matching `CODEX_SESSION_ID` and `CODEX_THREAD_ID`.

**Parent:** M5. **Responsible:** hardware integrator, unclaimed; analog reviewer,
unclaimed. Current pcb-manager integrates; task state is in the single tracker.

## Objective and scope

Produce one traceable description of the fitted logger and a proposed Rev A
interface freeze, preserving the distinction between fitted, specified and unknown.
Work in `jgazeley/accord` from current public main, including reviewed LRA-01/02
and LRA-05 candidate `0745d5b`; record the exact starting commit. Suggested branch
`task/LRA-03-<own-session-short>`.

Claim only `logger/hardware/as-built/`. Deliver `AS_BUILT.md`,
`REV_A_INTERFACES.md` and a `SOURCE_MANIFEST.json` for any recovered artifacts.
Power documents, firmware, KiCad and root/coordination remain with their owners.
Environment: source/document analysis without bench access initially.

## Minimum inputs and dependencies

Read `logger/hardware/REV_A_CONTEXT.md`, `logger/hardware/README.md`,
`coordination/MIGRATION_MAP.md` and `coordination/handoffs/LRA-01_POWER_INTERFACE.md`.
Cross-check actual public firmware pin declarations and SD assignments. Manager
provides selected, public-reviewed historical circuit/ADC excerpts if required.
Detailed fitted opto and ADC component values are unresolved inputs, not license
to copy specified values into an as-built BOM. Collect precise owner/bench questions.

Read `logger/hardware/power/INTERFACE_CONTRACT.md`,
`logger/hardware/power/COMPONENT_MARGIN_CLOSURE.md`
and `coordination/reviews/LRA05_REVIEW_2026-10-29.md` for the current candidate
interfaces and unresolved protection/leakage/isolation/timing gates. GP6 is the
qualified HOLD reservation; the existing as-built remains manually powered.

Start signal consolidation now; final power domains depend on LRA-01/02 closure. Exchange
proposed GPIO/connector reservations with LRA-04 before either freezes them.

## Existing logger as-built — owner reminder, October 28

Current pcb-manager verified the historical as-built records following the owner's
reminder that the logger circuit already exists but is not yet captured in KiCad.
**Start by consolidating that physical build; schematic absence is not design
absence.** Keep the recorded as-built and proposed Rev A changes separately labeled.
Keyless circuits are references; `9527a14` is the proposed automatic-power addition.
Neither is a substitute for the fitted logger signal chain.

Baseline source: historical `accord-logger` at
`1e994494f933da99636942d6ec135e857f2b3f6b`, `circuits.md` dated corrections and
`fuel/READINGS.md` installation/ground entries; `fuel/ADC_INTERFACE_SPEC.md`
provides specifications, not blanket proof of fitted parts. The current public
summary is `logger/hardware/REV_A_CONTEXT.md`. Read newest owner corrections first:

| Block | Existing recorded build / qualification |
|---|---|
| VSS / tach / brake | B2 -> GP2, 22k/33k; B1 -> GP3 and C14 -> GP4, 22k/6.8k. October 24 owner correction confirms one upper 1N5819 clamp per cell, replacing erroneous BAT54 labels. |
| Fuel / supply | C11 -> GP26 and B11 -> GP27. Fuel divider installed October 24; B11/B16 subsequently confirmed connected. Specified dividers are 7.5k/4.7k and 22k/4.7k; exact fitted protection/filter parts still need reconciliation. |
| Ground | October 24 owner clarification: B16 lands on a breadboard ground rail jumpered to Pico AGND; both ADC dividers use that rail. Buck power return and opto output return must be represented explicitly. |
| IGN | October 26 supersedes the older clock/Pi feed: B11 -> series diode/resistor -> opto LED, return B16; collector -> GP5, emitter -> Pico GND, capacitor across collector/emitter. Latest report leaves resistor/capacitor values and diode type unspecified. |
| SD | Existing SPI0 GP16/17/18/19 for MISO/CS/SCK/MOSI, module 3V3 fed from Pico 3V3(OUT); current `logger_sd.cpp` preserves the as-built assignment. |
| Supply | Auxiliary-battery buck provides 5 V with manual power; automatic HOLD/cutoff remains a candidate addition. |

Older notes saying brake/fuel are merely tapped, B11/B16 are disconnected or all
three digital dividers are identical must not overwrite later installation
records. Preserve unknowns rather than importing keyless values or proposed power
values into the as-built. Capture each planned change as a delta with its reason.
Selected historical excerpts need provenance/public review; personal readings and
road data do not need importing to preserve this circuit record.

## Existing keyless examples — owner reminder, October 28

Current pcb-manager reviewed `keyless/hardware/hondaPico.kicad_sch`, matching
firmware input definitions and the existing KiCad validation report. Consult this
already-migrated design before inventing equivalent logger blocks:

- U10–U13 PC817 input cells: ground-active switch inputs and +12 V-active IGN.
  U13/R12/D4 is the schematic's PC817 / 2.2k / 1N5819 ignition example; firmware
  reads GP14 active-low. It is not the logger's GP5 pin assignment or proof of
  the logger's latest fitted resistor/capacitor values.
- U3 LM2678T-5.0 supply, battery divider, ULN2803A output stages, ceiling-light
  MOSFET, harness connectors, rail/ground test points and RUN reset header are
  existing implementation references. Select only blocks relevant to logger.
- Existing validation records J2 absent from the PCB and R14/R15 value differences.
  Read `keyless/validation/kicad-20261027/README.md` before extracting values.

The owner identifies working examples in this circuit. Preserve the associated
operational evidence, but distinguish schematic intent, fitted hardware and any
logger-specific validation still required. Historical `circuits.md` explicitly
records the earlier IGN wake cell as a copy of keyless U13; do not rediscover that
basic topology. Shared-qualified IGN and logger power-off behavior remain the
LRA-01/02 continuation work. No keyless design changes are assigned here.

## Deliverables and acceptance

- Circuit table: signal, vehicle tap, polarity, fitted component/value/source,
  proposed change, GPIO, rail and confidence. Verify 1N5819 correction; distinguish
  opto input isolation from the installation's shared grounds.
- Interface proposal: input loading/protection, grounds/returns, connectors,
  mounting/enclosure constraints, SD/USB access and test points. Dimensions not
  actually measured remain explicitly unknown.
- Off-state path matrix: every energized vehicle input, USB and expansion path
  against disabled rails; expected path and analysis/test required. Refer to
  the power owner's contract rather than invent a second power design.
- Evidence check: each fitted assertion has a dated source or physical record;
  each conflict/unknown has a proposed resolution and responsible role. Analog
  reviewer records loading/protection disposition; electrical lead agrees power
  boundaries; firmware reviewer agrees pin mapping. Manager records acceptance.

Authorized: scoped public-safe documentation and analysis. Hardware operation,
vehicle wiring, flashing, purchasing/fabrication and private runtime/DB changes
require separate owner authorization. No fuel calibration model is needed here.

## Return and next action

First acknowledge claimant and exact scope to manager, then deliver the circuit
matrix with unknowns. Return pushed branch/commit, provenance, verification,
review disposition, remaining questions and next bounded action. No delivery,
bench test or acceptance is claimed by this packet. Preserve any uncommitted work
and identify it in the return; do not silently overwrite other owners' artifacts.

> **Required agent attribution:** Follow `logger/coordination/AGENT_ATTRIBUTION.md` relative to this repository root. Use your own tool, role and verified current session ID for Git author and committer (`<Tool> <role> [<short-id>]`), using per-command settings. End commits with `Agent-Session: <role>` and your full tool-specific session-ID trailer (`Codex-Session-ID`, `Claude-Session-ID` or `Antigravity-Session-ID`). This includes documentation-only work. Identify yourself and your resume command in coordination documents and dated updates. Preserve predecessor identity and original attribution when transporting commits. If an ID is unavailable, state that explicitly; never invent or borrow one. Include this requirement in subsequent seeds and handoffs.
