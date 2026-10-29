# LRA-06 — Rev A schematic capture, as a new KiCad project

> **Current continuation:** [LRA-12](LRA-12_LAYOUT_ELECTRICAL_CLOSURE.md)
> consolidates the remaining electrical/capture work for owner layout. Read its
> [readiness review](../reviews/LAYOUT_READINESS_2026-10-29.md) for source and
> gate corrections before redispatching this historical packet.
> October 29 update by Codex `pcb-manager`, session
> `01a18447-07c2-7bb3-8318-9b276cfdb3b8`
> (`codex resume 01a18447-07c2-7bb3-8318-9b276cfdb3b8`).

Prepared October 29, 2026 by Claude `pcb-manager`, session
`630dea87-5e4d-4bad-a1ff-d41b3a5f509b`.
Identity verified from the harness-reported session ID.

**Parent:** M5. **Responsible:** KiCad schematic owner, unclaimed. Current
pcb-manager integrates; `coordination/PROJECT_MILESTONES.md` owns state.

## Read this first: you are not blocked

The tracker row for LRA-06 has long said "blocked for freeze on 01–04." That is
true of the *freeze*, not of the capture. Most of this board is specified well
enough to draw today, and two items are deliberately placeholders. **Do not go
looking for what blocks you.** The three incomplete areas are named in
"Placeholders" below, with the exact instruction for each. Nothing else in the
repository needs to be consulted to settle whether work can begin.

Budget your reading. The documents listed under "Minimum context" are the whole
input. The rest of `logger/hardware/`, the review folder, the LRA-01–05 packets
and the historical `accord-logger` repository are **not** required, and the
owner has explicitly identified context sprawl as this project's main problem.
If something seems missing, raise it as a bounded question in your return rather
than excavating for it.

## Objective and completion boundary

Produce a new KiCad 9 schematic for the Rev A logger board, capturing the fitted
circuit plus the agreed Rev A deltas, with unselected items placed as clearly
marked placeholders. Deliver the project, a BOM, an SVG export and an ERC
disposition.

**Done** when the schematic loads and exports under `kicad-cli` 9.0.2, every ERC
violation is either resolved or dispositioned in writing, and every symbol has a
footprint assigned or an explicit reason it does not yet. **Not** in scope:
PCB layout (LRA-08), part selection for the placeholders, any change to a
divider ratio or pin assignment, and any claim that the design is frozen.

## Repository, branch, owned paths

Work in `jgazeley/accord` from current public `main`; record the exact starting
revision in your return. Branch `task/LRA-06-<your-session-short>`.

Own `logger/hardware/kicad/` only. Everything else in the tree is read-only,
including `keyless/hardware/`, which you copy *from* and must not modify.

Project files: `logger/hardware/kicad/accord-logger.kicad_pro` and siblings,
matching the firmware directory name `logger/firmware/accord-logger/`.

## Minimum context

Four reads. In this order.

1. [`REV_A_INTERFACES.md`](../../logger/hardware/as-built/REV_A_INTERFACES.md)
   **§1** (GPIO allocation — the pin map you capture), **§5** (connectors and
   test points), **§7** (the delta list D1–D15 — this is your work order).
   Skim §3.4 only for the D4 placeholder's requirements.
2. [`AS_BUILT.md`](../../logger/hardware/as-built/AS_BUILT.md) **§2** (circuit
   matrix — the five input cells as fitted) and **§3.4** (ignition cell).
   §3's per-channel discussion is background; you need the matrix.
3. [`DESIGN.md`](../../logger/hardware/power/DESIGN.md) **§3**, the
   component-level connection schematic for the power block, with
   [`BOM.csv`](../../logger/hardware/power/BOM.csv) beside it for part numbers.
4. [`keyless/validation/kicad-20261027/README.md`](../../keyless/validation/kicad-20261027/README.md)
   — the validation method you repeat, and the warnings already known.

## Convention template — related board, separate project

**Owner direction, October 29, 2026:** use the keyless KiCad project as a
template for conventions and naming, and build the logger as a **distinct board
project**. Copy the scaffolding; copy no circuit.

Take from `keyless/hardware/`:

| Item | What to reuse |
|---|---|
| `sym-lib-table` | The pattern: one project-local `Custom` library at `${KIPRJMOD}/Custom.kicad_sym`. Project-relative URIs are what made the keyless copy portable; do not write absolute paths or register anything globally |
| `fp-lib-table` | Same pattern, one project footprint library at `${KIPRJMOD}/accord-logger.pretty` |
| `Custom.kicad_sym` | Holds `IL-AG5-22P` and **`LM2678T-5.0`**. The LM2678 is the Rev A regulator (`UREG`, BOM row 6), so copy that symbol across rather than redrawing it. Leave the connector symbol behind unless you need it |
| `hondaPico.pretty` | The pattern only — project footprints for parts with no library equivalent. The keyless `.kicad_mod` files are enclosure posts and a JAE connector; none applies here |
| `LICENSE`, `NOTICE` | Place at `logger/hardware/kicad/`. Hardware is CERN-OHL-P-2.0 per `LICENSING.md` |
| Test-point and reset-header style | TP loops per rail, three separate ground loops, a shorting jumper for RUN-to-GND. REV_A_INTERFACES §5.3 lists the logger's own set |

Naming: the keyless project keeps the filename `hondaPico.kicad_pro` and
`AGENTS.md` requires that it not be modernised. Your new project is a new board
and takes the clean name; this is not a conflict with that rule, and it does not
license renaming anything on the keyless side.

Symbols you should *not* need to draw: `MCU_Module:RaspberryPi_Pico_W`,
`Isolator:PC817`, `Diode:1N5819`, `Device:R/C/L/LED`, `Connector:TestPoint`,
`Jumper:Jumper_2_Open` all come from the installed standard libraries. Use the
installed versions directly rather than importing the copies cached inside
`hondaPico.kicad_sch` — see "ERC dispositions" for why.

## What to capture

| Block | Source | Note |
|---|---|---|
| Pico W and pin map | REV_A_INTERFACES §1 | Capture the Rev A column. GP0/GP1, GP7 and GP28 stay free and must not be connected |
| Five input cells | AS_BUILT §2, §3 | Fitted ratios and clamps carried forward unchanged. Both ADC channels already have 1 kΩ + 1 µF + two 1N5819; this is not a new addition |
| Ignition / opto cell | AS_BUILT §3.4, delta D1 | 1N5819 series, 2.2k, 100 nF output, no input cap. GP5 is the QREPORT node with 10k to **switched** 3V3 |
| Onboard power | DESIGN.md §3, BOM.csv | QP / LM2678 / independent latch, counters, clock; D7 and D13 |
| HOLD | Delta D2 | GP6, 47k pulldown, JH removable link |
| SD | AS_BUILT §3.5, delta D6 | SPI0 GP16–19 on switched 3V3, plus the new 10–100 µF bulk at the SD supply |
| Connectors J1–J4 | REV_A_INTERFACES §5.1 | J1 power 2-way, J2 cluster 8-way, J3 bus (see placeholders), J4 service |
| Test points | REV_A_INTERFACES §5.3 | The full table, including the A5-domain points that carry **no** GPIO connection |
| Grounds | REV_A_INTERFACES §4, delta D5 | One B16 conductor to one common node to AGND. B16 is never a power return — capture it so layout cannot lose it |

Deltas owned by LRA-06: **D6** and **D8**. Deltas you capture as already-decided
candidates: D1, D2, D5, D7, D13. Deltas that are **not yours**: D4, D10, D11,
D14, D15 — do not attempt to resolve them.

## Placeholders — three items, three instructions

1. **D4, input isolation.** Normally-open, power-off-safe isolation upstream of
   the divider top. **No part is selected and selecting one is not your task.**
   Place a single-pin-pair placeholder symbol, reference-designated
   consistently, with its requirements in a schematic text note
   (REV_A_INTERFACES §3.4). The BOM already carries this as the
   `SIGNAL_ISOLATION` row.

   **Amended October 29, after the owner's U-10 measurement** (`D-OFFSTATE-01`).
   Key out and parked, B2 reads **4.140 V** while B1 and C11 read **0 V**; C14
   and B11 were already recorded dead with the key out. So **B2 is the only
   branch with a measured parked-drain case**, and D4's justification no longer
   covers the other four. Keep **all five placeholder positions** — they are
   placeholders and cost nothing — but annotate them differently: B2's as
   **required, measured 75.3 µA at 4.140 V through the fitted 55 kΩ**, and the
   other four as **under analog review, parked-drain justification withdrawn**.
   Do not delete the four and do not promote them to real parts. If the reviewer
   drops them, four symbols come out; if a fault or transient reason keeps them,
   nothing has to be redrawn.
2. **J3, bus and expansion.** LRA-04 returned with revisions required and no bus
   selected. GP8, GP9 and GP10 are **offers, not reservations**. Place J3 as an
   unpopulated header with its pins unconnected, and leave those three GPIOs
   unconnected. Do not capture a transceiver.
3. **`MAX_ON` and `VEHICLE_PROTECTION`**, the other two TBD BOM rows. Same
   treatment: marked placeholder, requirement in a text note, no part chosen.

A placeholder must be visually unmistakable in the SVG export and must appear in
the BOM as unselected. A silently omitted block is a defect; a clearly marked
empty one is the deliverable.

## ERC dispositions, pre-seeded

The keyless validation run already found these; do not rediscover them.

- Its two remaining ERC warnings were **cached symbols differing from installed
  library definitions** (Pico W, MAX3485), an artefact of symbols embedded in
  that schematic. Draw from the installed libraries and you should not inherit
  them. If you do see this class of warning, disposition it rather than editing
  a library to silence it.
- Run `kicad-cli` 9.0.2 against a **temporary KiCad configuration**; change no
  global user configuration.
- Read the **JSON reports**. `kicad-cli` rule checks do not signal violations
  through the process exit code unless `--exit-code-violations` is passed, and a
  zero exit is not a clean design.
- `/usr/share/kicad/3dmodels` is absent on this host, so 3D model resolution
  cannot be verified. State that as a limitation; do not treat it as a failure.

## Deliverables

Into `logger/hardware/kicad/`:

- `accord-logger.kicad_pro`, `.kicad_sch`, `Custom.kicad_sym`, `sym-lib-table`,
  `fp-lib-table`, `accord-logger.pretty/`, `LICENSE`, `NOTICE`
- `BOM.csv` — every captured part, placeholders included and marked
- `validation/` — ERC JSON, the `kicad-cli` commands used, and `schematic.svg`
- `CAPTURE_NOTES.md` — ERC dispositions, footprint assignments and the reason
  for any symbol left unassigned, placeholder inventory, and every question you
  could not resolve from the four documents above

No `.kicad_pcb`. Layout is LRA-08.

## Acceptance

| Check | Expected | Evidence |
|---|---|---|
| Project loads and exports | `kicad-cli sch export svg` succeeds | `validation/schematic.svg` |
| ERC | Zero errors; every warning dispositioned in writing | ERC JSON + `CAPTURE_NOTES.md` |
| Pin map | Matches REV_A_INTERFACES §1 Rev A column exactly; GP0/1, GP7, GP8–10, GP28 unconnected | Reviewer diff against §1 |
| Input cells | Ratios and clamps match AS_BUILT §2 with no value changed | Reviewer diff against §2 |
| Placeholders | Five D4 positions with B2's marked required and the other four marked under review; J3 unpopulated; `MAX_ON` and `VEHICLE_PROTECTION` present and marked | SVG + BOM |
| Libraries | All URIs `${KIPRJMOD}`-relative; no global library registration | `sym-lib-table`, `fp-lib-table` |
| Footprints | Assigned, or listed with a reason | `CAPTURE_NOTES.md` |

## Authorized and unauthorized

**Authorized:** create the new KiCad project; copy scaffolding and the
`LM2678T-5.0` symbol from `keyless/hardware/`; run `kicad-cli` with a temporary
configuration; commit to your task branch.

**Unauthorized:** modifying anything outside `logger/hardware/kicad/`; selecting
parts for D4, `MAX_ON` or `VEHICLE_PROTECTION`; changing any divider ratio, pin
assignment or clamp; declaring the interface frozen or the design ready to
order; PCB layout; force-adding `keyless/hardware/3d/039301160.stp`; changing
global Git or KiCad configuration. This packet authorizes no fabrication,
purchase, flashing or vehicle work.

## Dependencies, blocker and next action

No blocker on starting. The schematic cannot be *frozen* until D4 has a selected
part and LRA-04 returns a corrected bus recommendation; both are tracked
elsewhere and neither gates capture. LRA-08 additionally needs the owner's U-11
physical envelope, which is independent of this task.

Next action: claim the row in `coordination/PROJECT_MILESTONES.md` with your
tool, role and session, then read the four documents above.

> **Required agent attribution:** Follow `logger/coordination/AGENT_ATTRIBUTION.md`
> relative to this repository root. Use your own tool, role and verified current
> session ID for Git author and committer (`<Tool> <role> [<short-id>]`), using
> per-command settings. End commits with `Agent-Session: <role>` and your full
> tool-specific session-ID trailer (`Codex-Session-ID`, `Claude-Session-ID` or
> `Antigravity-Session-ID`). This includes documentation-only work. Identify
> yourself and your resume command in coordination documents and dated updates.
> Preserve predecessor identity and original attribution when transporting
> commits. If an ID is unavailable, state that explicitly; never invent or borrow
> one. Include this requirement in subsequent seeds and handoffs.
