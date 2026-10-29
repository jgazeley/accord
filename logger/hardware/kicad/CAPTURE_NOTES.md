# LRA-06 — Rev A schematic capture notes

October 29, 2026 by Claude Code `logger-schematic`, session
`73d7d954-f82a-4038-8ff3-546a23fc5fa9`.
Resume: `claude --resume 73d7d954-f82a-4038-8ff3-546a23fc5fa9`.
Session ID read from this session's harness-assigned working paths; no
tool-provided session/thread pair exists here to cross-check it against.

Branch `task/LRA-06-73d7d954`, rebased onto public `main` at
`21dfd163d904af002b55b248f84d855f412bb714`.

**Disposition: capture for review. Nothing here is frozen, accepted, ordered or
built.** Four blocks carry no selected part. The schematic reproduces the fitted
circuit and the already-decided Rev A deltas; it selects no part, changes no
divider ratio, moves no pin and makes no mechanical claim.

## 1. What was captured, and from what

Inputs were the four documents the packet names, and nothing else:

| Source | Section | Used for |
|---|---|---|
| [`REV_A_INTERFACES.md`](../as-built/REV_A_INTERFACES.md) | §1 | the pin map captured on U1, Rev A column |
| | §3.1, §3.4 | the D4 placeholder requirement text |
| | §4 | grounds and returns, delta D5 |
| | §5.1, §5.3 | connectors J1–J4 and the test-point table |
| | §7 | the delta work order D1–D15 |
| [`AS_BUILT.md`](../as-built/AS_BUILT.md) | §2 | the five fitted input cells |
| | §3.4, §3.4a | the ignition opto cell and its measured 2.2k |
| | §3.5 | SD wiring and the D6 justification |
| [`power/DESIGN.md`](../power/DESIGN.md) | §3 | the component-level power connection list |
| [`power/BOM.csv`](../power/BOM.csv) | — | power part numbers and the three TBD rows |
| [keyless validation README](../../../keyless/validation/kicad-20261027/README.md) | — | the validation method repeated here |

Deltas captured as already-decided candidates: **D1, D2, D5, D7, D13**.
Deltas owned and implemented by this task: **D6** (SD bulk) and **D8** (test
points and the reset header). Deltas deliberately untouched: **D4** (placeholder
only), **D10, D11, D14, D15**. D3, D9 and D12 are closed in the source and
needed nothing.

## 2. Placeholders — four blocks, no part selected

A placeholder is a dashed symbol carrying a `?` and a state label, so it cannot
be read as a real part in the SVG, and it appears in `BOM.csv` with a
`REQUIRED_BEFORE_*` status and `(none assigned)` for its footprint.

| Block | Instances | Refs | State in the SVG |
|---|---|---|---|
| **D4** input isolation | 5, one per branch | X1–X5 | X1 (B2) `REQUIRED, NOT SELECTED`; X2–X5 `UNDER REVIEW, NOT SELECTED` |
| **J3** bus / expansion | 1 header, all pins unconnected | J3 | unpopulated; GP8–GP10 also left unconnected on U1 |
| **MAX_ON** | 1 | X8 | `NOT SELECTED (MAX_ON)` |
| **VEHICLE_PROTECTION** | 1 | X7 | `NOT SELECTED (R02)` |
| **QREPORT stage** (see Q1) | 1 | X6 | `NOT SELECTED (QREPORT)` |

The fifth is a block the packet did not enumerate; §6 explains why it exists
rather than being silently omitted.

**D4 after `D-OFFSTATE-01`.** The owner's October 29 key-out measurement closed
U-10: B2 reads 4.140 V while B1 and C11 read 0 V, and C14 and B11 were already
recorded dead with the key out. All five positions are kept, as the amended
packet directs. X1 carries the measured requirement — 75.3 µA through B2's
fitted 55 kΩ, on its own about nine times the 8/20 µA allocated to all five
branches. X2–X5 keep their positions with the parked-drain justification
withdrawn; whether a fault or transient reason keeps them is the analog
reviewer's call, not this task's. Neither outcome needs a redraw.

`TVS` and `X7` are deliberately separate parts. `TVS` is the named inherited
candidate 1.5KE30A-E3/54 from `DESIGN.md` §3; `X7` is the unselected
`VEHICLE_PROTECTION` BOM row. Neither is vehicle-approved.

## 3. ERC dispositions

`validation/erc.json`, KiCad 9.0.2: **0 violations at `--severity-all`**, so
there are no errors and no warnings to disposition. Specifically:

- **The keyless run's two cached-symbol warnings did not recur.** They came from
  Pico W and MAX3485 symbols embedded in that schematic differing from the
  installed library definitions. Every symbol here is taken from the installed
  libraries, and `RaspberryPi_Pico_W`, which the libraries store as a derived
  symbol, is flattened the way KiCad resolves inheritance — a schematic's
  `lib_symbols` cannot carry `extends`. No library was edited to silence
  anything.
- **No "library not configured" warning**, because the run used a temporary
  configuration holding the installed global `sym-lib-table` and `fp-lib-table`.
- **Deliberately unconnected pins carry explicit no-connect flags** rather than
  being left dangling: GP0/GP1, GP7, GP8–GP10, GP28, ADC_VREF, 3V3_EN and VBUS
  on U1; all six J3 pins; J4 pins 3–4; the two J2 spare contacts; and UREG pin 7
  `ON/OFF`, which `DESIGN.md` §3 specifies as open. In the exported netlist these
  appear as single-node `unconnected-(…)` nets, which is what an intentional
  non-connection looks like.
- **Two `PWR_FLAG`s** (`#FLG1` on VIN_SW, `#FLG2` on VSYS) declare those nets
  driven. Both reach a power-input pin — UREG VIN and the Pico's VSYS — through
  passive parts only, so without them ERC would report an undriven power input.
  PGND needs none: the Pico's GND pin is a power output.

`/usr/share/kicad/3dmodels` is absent on this host, so 3D model resolution and
appearance **cannot be verified**. That is a stated limitation of this check,
not a failure.

Rule-check results above are read from the JSON report. `kicad-cli` does not
signal violations through its exit code unless `--exit-code-violations` is
passed, so a zero exit is not evidence of a clean design.

## 4. Footprints

79 of the 89 real parts carry an installed footprint. The ten exceptions, and
why:

| Ref | Reason |
|---|---|
| J1, J2 | connector family not selected; envelope, mounting and harness entry are unknown (U-11, `REV_A_INTERFACES` §5.2). Assigning a footprint here would be an invented mechanical decision |
| X1–X8 | placeholders: no part is selected, so no package exists to assign |

`accord-logger.pretty/` is therefore empty of footprints: every captured part
either resolves in an installed library or has no part yet. The directory and
its library-table entry exist so LRA-08 has the project-local place to put a
footprint the standard libraries do not cover.

Footprints for the parts that are bench-only or unselected (QI/QH as 2N3904,
F1/F2 as 5×20 mm clip holders, CIN/COUT as generic radials) are **package
placeholders for layout planning, not part selections**; the BOM status column
carries the real state.

## 5. Annotation and designators

KiCad requires `<prefix><number>` references, so the descriptive names used
while capturing are recorded in each symbol's `Source_designator` field and in
the `source_designator` column of `BOM.csv`. A reviewer diffing against
`DESIGN.md` §3 should read that column: `U3` is `UREG`, `Q1` is `QP`, `D101` is
`DREV`, and so on.

**Diodes are numbered from D101.** The delta list in `REV_A_INTERFACES` §7 uses
IDs D1–D15, and conventional diode designators D1–D15 on the same board would be
unreadable next to it. No schematic designator here can be mistaken for a delta
ID.

## 6. Questions this capture could not resolve

Q1 is the one that matters; the rest are smaller.

**Q1 — the GP5 report path has no component-level source.**
`REV_A_INTERFACES` §1 gives GP5 as `QUAL_N_REPORT`, "QREPORT drain, 10k to
switched 3V3", and `AS_BUILT` §3.4a says that in Rev A the optocoupler drives
`IGN_A`/`IGN_RC` in the A5 qualification network rather than a GP5 pull-up.
`DESIGN.md` §3 — the only component-level power schematic in this task's input —
instead wires the opto collector straight to GP5 as `IGN_N` with `RIGN` 10k to
3V3. That is the older raw-GP5 arrangement, and `D-RA-03` forbids mixing it with
the qualified proposal. Capturing either one literally would be wrong, so the
capture does what the sources jointly require: the opto collector goes to
`IGN_N`, X6 is a marked placeholder for the A5-domain stage, and GP5 is
`QUAL_N_REPORT` pulled up by `RIGN` to switched 3V3. **A reviewer should confirm
that reading, or point to the document that specifies the stage.** The three test
points it implies — TP_A5, TP_VCLK, TP_QUALN — are captured either way.

**Q2 — the fitted ignition LED returns 4.7–5.8 mA through B16, which §4 says
carries no current.** `AS_BUILT` §3.4 is explicit that the opto LED cathode goes
to cluster B16 "with nothing in series", and §4 is equally explicit that B16 is
reference-only and "must never become a power return". `DESIGN.md` §3 returns the
same LED to PGND instead. This capture follows the fitted cell, per the packet,
so U2 pin 2 is on B16. Two consequences for the reviewer: the B16 conductor
carries the LED current in normal operation, and with the board off a 16 V B11
still drives that LED, which is a criterion-B path that returns off-board rather
than into the board's rails. **Which return is intended for Rev A is an
electrical decision, not a capture decision.**

**Q3 — J3's contact count is a guess.** LRA-04 selected no bus, so nothing fixes
the pin count. A 6-way header is placed with every pin unconnected. The count is
provisional and LRA-04's to set; changing it costs one symbol.

**Q4 — FIGN's location contradicts §5.1.** `DESIGN.md` §3 puts the ignition-sense
fuse on the board; `REV_A_INTERFACES` §5.1 says per-branch fuses belong at the
tap end, "which is where the specification puts them and where a chafed wire is
actually backed by vehicle current". It is captured on the board, following the
power block's own connection list, and flagged rather than silently dropped.

**Q5 — J4's UART0 pins cannot be both present and unconnected usefully.** §5.1
defines J4 as "UART0 on GP0/GP1 and a RUN-to-GND reset pair", while §1 and this
task's acceptance both require GP0/GP1 to stay unconnected. J4 is captured with
the RUN-to-GND pair live and pins 3–4 present but unconnected. If the service
UART is wanted, §1's "keep free" needs rewording; if not, J4 can shrink to two
contacts.

**Q6 — MAX_ON's inhibit is not inserted into the HOLD path.** The BOM calls
MAX_ON a "latched HOLD-path inhibit", but the reviewed HOLD path in `DESIGN.md`
§3 runs GP6 → JH → RH → QH base with no such element, and MAX_ON is "not
implemented in revision A". `HOLD_N` is therefore brought only to X8 and its test
point. **Where the inhibit acts is the electrical lead's decision**; the capture
records the interface without silently changing the reviewed latch.

**Q7 — the ADC clamp and filter returns, and the third ground loop.** The fitted
ADC protection is "1 µF to GND, 1N5819 to 3V3 and to GND" (§2 rows 4a/5a), and
§3.3 says the rail carrying B16 and both divider bottoms is the one the Pico's
AGND pin sits on. The capture puts those returns on AGND, which keeps the ADC
reference consistent but means a clamp conducting during a fault puts current in
B16 — the same concern as Q2. Relatedly, §5.3 asks for three ground loops
"buck, Pico, harness"; TP_GND_BUCK and TP_GND_PICO are on PGND and
TP_GND_HARNESS is on the B16 sense node, which is the reading that makes the
third loop useful. Both choices are cheap to change and should be confirmed.

## 7. How to reproduce the checks

```sh
export HOME=$(mktemp -d)                 # temporary KiCad configuration
mkdir -p "$HOME/.config/kicad/9.0"
cp /usr/share/kicad/template/sym-lib-table \
   /usr/share/kicad/template/fp-lib-table "$HOME/.config/kicad/9.0/"
cd logger/hardware/kicad
kicad-cli sch erc --format json --severity-all -o validation/erc.json accord-logger.kicad_sch
kicad-cli sch export netlist --format kicadsexpr -o validation/netlist.net accord-logger.kicad_sch
kicad-cli sch export svg --no-background-color --exclude-drawing-sheet -o validation accord-logger.kicad_sch
python3 check_capture.py
```

The schematic and `BOM.csv` are both generated from one parts table by
`tools/gen_logger_sch.py`, and `Custom.kicad_sym` by `tools/gen_custom_sym.py`,
so the drawing and the BOM cannot drift apart. The generators are included for
reproducibility; the `.kicad_sch` is the deliverable and can be edited directly
in KiCad from here on, after which the generators become historical.

`check_capture.py` reads the exported netlist and the BOM and asserts the §1 pin
map, the deliberately unconnected pins, the §2 cell values and clamp
orientations, the ignition cell, the HOLD path, D6, D7, D13, the J3/J4 state, the
placeholder inventory and its D4 split, the footprint exceptions, that every
library URI is `${KIPRJMOD}`-relative, and that all 53 declared nets still exist
as separate nets with no unexpected extras. **201 checks pass.** It proves the
capture agrees with the written sources; it proves nothing about circuit
behaviour.

The last of those matters because of how the drawing is built: every connection
is a net label on a short stub at the pin, rather than a drawn wire between two
pins. That makes the netlist unambiguous, but a stub landing on a neighbouring
pin would silently merge two nets, and ERC would not complain. The net-identity
check is the guard against it.

Exact commands used, with the KiCad version, are in `validation/COMMANDS.txt`.

## 8. Legibility of the SVG — checked, but not with human eyes

The acceptance criterion is that a placeholder be visually unmistakable in the
SVG. **No SVG rasterizer is installed on this host** (no `rsvg-convert`,
`inkscape`, ImageMagick or headless browser), so the export could not be
rendered and looked at. Legibility was instead checked geometrically, from the
schematic source and from the stroked glyph paths in the SVG:

- Reference and Value fields were initially placed by a fixed offset and
  overlapped each other on the larger symbols. They are now placed from each
  symbol's actual bounding box — beside a narrow two-pin part, above and below
  anything with a body — and the worst previous cases were verified in the file
  as 3.56 mm apart at 1.69 mm text height.
- The ten long annotation blocks were initially drawn over the circuit. They are
  now in their own column on the right of an A0 sheet, with the circuit itself
  unchanged.
- Labels were initially placed directly on the pins, touching KiCad's pin
  numbers. Each now sits at the end of a 2.54 mm stub.

What remains unverified is the overall visual impression: whether blocks read in
a sensible order, whether any note column line wraps awkwardly, and whether the
dashed placeholder bodies are as prominent on screen as intended. **A reviewer
should open `validation/schematic.svg` or the project in the KiCad GUI once.**
That is the one acceptance item this session could not close itself.

## 9. What this does not do

No PCB layout (LRA-08, which additionally needs U-11). No part selection for D4,
MAX_ON, VEHICLE_PROTECTION or the QREPORT stage. No divider ratio, pin
assignment or clamp changed. No interface freeze: that still waits on a selected
D4 part and a corrected LRA-04 bus recommendation. No fabrication, purchase,
flashing or vehicle work is authorised by this capture, and the power stage as
captured is explicitly bench-only — QI and QH are 2N3904s rated for a 12–16 V
bench, and F1 assumes a current-limited supply.

> **Required agent attribution:** Follow `logger/coordination/AGENT_ATTRIBUTION.md`
> relative to this repository root. Use your own tool, role and verified current
> session ID for Git author and committer identity (`<Tool> <role> [<short-id>]`),
> with per-command settings. End each new commit message with
> `Agent-Session: <role>` and your full tool-specific session-ID trailer
> (`Codex-Session-ID`, `Claude-Session-ID` or `Antigravity-Session-ID`). This
> includes documentation-only commits. Identify yourself and your resume command
> in new coordination documents and dated updates. Preserve predecessor bookmarks
> and original attribution when transporting existing commits. If your ID is
> unavailable, say so rather than inventing one. Include this requirement in any
> seeds or handoffs you create.
