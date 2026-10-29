# Layout readiness — close the electrical design, then hand over the board

October 29, 2026, Codex `pcb-manager`, session
`01a18447-07c2-7bb3-8318-9b276cfdb3b8`.
Resume: `codex resume 01a18447-07c2-7bb3-8318-9b276cfdb3b8`.
Identity re-verified from matching session/thread environment values.

The owner wants to begin placement/routing and requested **one remote-engineer
assignment** to remove the remaining electrical blockers. This review uses
current documents, the captured netlist/BOM, and the returned LRA-11 artifacts;
no transcript reconstruction. The assignment is
[LRA-12](../handoffs/LRA-12_LAYOUT_ELECTRICAL_CLOSURE.md). Current state and
claims remain solely in `PROJECT_MILESTONES.md`.

## What is already decided

The board is a separate logger project, 80 × 120 mm, with the Pico and the
16 × 16 mm SD module. No enclosure or inventory reconciliation is required to
start design. Preserve the owner-confirmed wiring, five divider ratios and
existing GPIO assignments. Keyless has a working LM2678 supply and exercised
RS-485 hardware; reuse that evidence without conflating the boards.

The existing power design is the starting circuit. The lack of its components
in the capture is **not evidence that it needs to be invented again**.

## Two capture questions have existing answers

| Captured question | Existing source | Disposition |
|---|---|---|
| Q1 / X6: no component-level qualified-IGN/QREPORT circuit | `power/CUTOFF_MARGIN_REVIEW.md` §2 and `INTERFACE_CONTRACT.md` §2 | The circuit exists: rewire the PC817 output into IGN_A/IGN_RC, the Schmitt/latch qualification, QRESET and QREPORT. Capture it, including the proper A5 supply and GP5 pull-up. Do not retain the old collector-to-GP5 wiring |
| Q6 / X8: where does MAX_ON interrupt HOLD? | `power/MAX_ON_CUTOFF.md`, connection table and “HOLD-path permission switch”; `CUTOFF_MARGIN_REVIEW.md` §§1–3; `INTERFACE_CONTRACT.md` §2 | QS goes between SINK and QH collector. QI stays directly on SINK. Include QMON before JH, clock, counters, latch and supervisor. The nominal cutoff remains 2048 s |

LRA-06's minimum input list used only `DESIGN.md` and `BOM.csv` for the power
block. Those describe the earlier circuit. Its eight placeholders are valid
markers of an incomplete capture, not eight fresh research assignments.
The “MAX_ON not implemented in Rev A” wording describes today's drawing;
it does not supersede the owner's integrated-power objective or the later
interface contract. Source precedence is explicitly given in that contract §1.

## LRA-11: temperature question closed; enable circuit still needed

Directly checked [Broadcom ASSR-601Jx-DS105, June 19, 2024,
pp.5–6](https://docs.broadcom.com/doc/ASSR-601Jx-DS). The DC table explicitly says
“Unless otherwise stated, all minimum/maximum specifications are over
recommended operating conditions.” The JV temperature range is −40 to +105 °C.
The leakage row specifies 1000 nA maximum at 1000 V, with no temperature
exception; footnote (a) requires LED voltage ≤0.4 V. The neighboring withstand
row explicitly limits its test to 25 °C. This is a stated table-wide condition,
not a typical-value extrapolation. **The previous demand for a separate vendor
confirmation of the temperature scope is withdrawn.**

Keep ASSR-601JV as the working candidate; no repeat component survey is needed
on that ground. The original `d8a67f7` return and its author are preserved by
merge. Its arithmetic script passes 24 checks independently. These checks
reproduce assumptions and numbers; they do not certify the proposed circuit.

The following qualifications control use of the return:

- **BAD does not necessarily remove B5.** The original design gates only QH;
  QI can maintain power with ignition present. Keep the literal hardware
  fail-open requirement. Complete the proposed PGOOD-controlled series driver,
  or an equivalent justified enable circuit, rather than silently weakening
  requirement 7. Select exact driver parts, defaults and pins. Also cover
  B5 alive while Pico 3V3 is absent or resetting, USB-only power, and rail decay.
- **The switch has finite leakage.** “No conductive path of any kind” and
  “eliminated” are overstatements. Bound residual current and dead-rail voltage,
  including PCB leakage. Applying the high-voltage leakage limit as a
  conservative low-voltage design screen is engineering reasoning, not a new
  manufacturer test at 4.669 V. The 1500 V withstand test is at 25 °C; use the
  recommended continuous-voltage rating for the operating-range argument.
- **The timing arithmetic is conditional.** The 4 ms turn-on maximum uses
  10 mA LED drive and a specified test load; the proposed 330 Ω circuit can
  supply less. The 190 pF coupling figure is typical, and an average-current
  calculation does not bound peak injected voltage. The script's extra 100 pF
  is assumed. Complete the drive/timing analysis and specify bench confirmation;
  do not promote 5/20 ms delays or the “no artefact” test name into guarantees.
- **Check the package drawing directly.** The return has no actual footprint.
  Verify pad geometry, numbering, omitted leads and height from p.3; a stock
  full-lead SOIC-16 is not sufficient. Pin 3 must remain externally unconnected.
- **Do not generalize a limited rejection into impossibility.** Removing the
  fitted external clamp alone does not solve the dead-rail problem. That does
  not prove every conceivable clamp/receiver topology impossible, nor dispose
  the other four branches' fault cases. Keep the useful result and the measured
  model; no broad replacement research is requested.

## Actual work before a complete board can be routed

| Item | Required result in LRA-12 |
|---|---|
| X1 and X2–X5 | Implement the B2 candidate with hardware gating and a firmware pin/sequencing contract. For each other branch, prove its reachable off/fault states and select a circuit or justified bypass. Parked 0 V alone is insufficient |
| X6 / X8 | Capture the existing qualified-IGN and full autonomous cutoff circuits using the source precedence above; close QMON/QS/report nets and footprints |
| X7 / R02 | Resolve the actual new A5/input-switch voltage compatibility. The working keyless buck/1.5KE30A precedent does not make a 41.4 V clamp compatible with TPS709's 30 V operating limit or the contract's ≤28 V protected rail |
| Ground returns / R06-REV-2 | Decide and draw the Rev A LED return and ADC reference topology, including Pico-internal ground continuity. Prefer the existing power design's PGND LED return if its input limits support it; preserve the as-built record separately |
| Parts / footprints | Consolidate existing BOM deltas; select exact population and packages for new power logic, caps, QP/DZ, isolation and connectors. Recheck 80 × 120 mm fit with the newly included components |
| Communications / service | Select a bounded, power-off-safe provision. A DNP expansion header is allowed. Do not require full CAN/RS-485 software or claim tied DE//RE reaches shutdown. Resolve J3/J4 pins and external-power paths |

The old “only LRA-11 stands between here and layout” sentence is withdrawn.
Known-block floorplanning can start, but a layout owner cannot finish a coherent
board from disconnected placeholder nets. LRA-12 must supply the actual
schematic and BOM, not merely another list of unresolved requirements.

Long-duration hot/cold qualification, actual stock counts, firmware deployment,
masked-interrupt watchdog acceptance, vehicle tests and ordering belong to
their later gates. They are not blanket prerequisites for placement. A known
electrical incompatibility or an unresolved footprint/net remains a layout
blocker; a documented, testable residual risk may remain an order/bring-up gate.
