# LRA-12R — entry-clamp rework of the LRA-12 return

Prepared October 29, 2026 by Claude `pcb-manager`, session
`42dd0e33-28b5-4936-847e-9c2e1d2488fa`.
Resume: `claude --resume 42dd0e33-28b5-4936-847e-9c2e1d2488fa`.

**Parent:** LRA-12. **Responsible:** one fresh electrical/KiCad session. The
original LRA-12 engineer (Claude `logger-electrical`,
`b690946d-3a88-4626-8e7b-b321126a3d16`) is not being resumed. Its work is the
baseline and its attribution stays on its commits.
**Reviewer/integration owner:** current pcb-manager. **The owner does layout.**

This is a bounded correction. Do not re-survey the design, re-open settled
LRA-12 decisions, or read transcripts or Git history for background.

## Base and scope

- Repository: `/srv/agent_share/accord` (public `github.com/jgazeley/accord`).
- Base: `task/LRA-12-b690946d` at
  `ad4f9188a9cbef25b0c1717418076c5e9b92cda1`. Create
  `task/LRA-12R-<your-short-session-id>` from it in a **new worktree of your
  own**. Do not use or modify `/srv/agent_share/accord-lra12`, and do not
  rewrite the original branch.
- Edit scope: `logger/hardware/kicad/`, `logger/hardware/power/LAYOUT_CLOSURE.md`,
  `logger/hardware/power/check_layout_closure.py`,
  `logger/hardware/power/INTERFACE_CONTRACT.md` (attributed change-record
  entries only), `logger/hardware/LRA12_HANDOFF.md` (append a dated
  revision section; do not rewrite the original's text).
- Not yours: root and `coordination/` (the manager's), `keyless/`, firmware,
  `logger/hardware/as-built/`, anything pinned by a `SOURCE_MANIFEST.json`.
- No purchase, bench work, wiring, flash, deployment or database change.

## Read only this

1. `coordination/reviews/LRA12_REVIEW_2026-10-29.md`: the findings.
2. `logger/hardware/power/LAYOUT_CLOSURE.md` §3 (all) and §7.
3. `logger/hardware/power/INTERFACE_CONTRACT.md` rows L04 and L07.
4. `logger/hardware/kicad/tools/gen_logger_sch.py`: the parts table and UUID
   generation. The schematic and `BOM.csv` are generated from it; edit the
   generator, never the `.kicad_sch` by hand.
5. `logger/hardware/power/check_layout_closure.py` §1 (envelope) and §4
   (ledger).
6. `logger/hardware/kicad/validation/COMMANDS.txt`: how to regenerate and
   validate.

Context you can rely on without re-deriving it: the keyless board runs the
same LM2678 + **1.5KE30A** pair in this car on a permanent 12 V feed through
cranking (tracker decision D-POWER-03), and the owner's direction is to reuse
working circuits unless there is a concrete reason (D-REUSE-02).

## Work

### R12-REV-1 — re-evaluate the clamp with a 60 V switch

§3.1 says the 1.5KE20A is forced because the only P-FET with a hot leakage
maximum is the 40 V IPD50P04P4L-11. That is false. Vishay **SQD50P06-15L**
(document 69098, Rev. E, https://www.vishay.com/docs/69098/sqd50p06.pdf):
−60 V V<sub>DS</sub>, ±20 V V<sub>GS</sub>, AEC-Q101, TO-252.
I<sub>DSS</sub> at V<sub>GS</sub> = 0 and V<sub>DS</sub> = −60 V: 1 µA max at
25 °C, 50 µA at 125 °C, 150 µA at 175 °C. Verify these from the datasheet
yourself.

Evaluate **keeping the 1.5KE30A** (41.4 V clamp at 36.2 A; compute the 85 °C
value) with SQD50P06-15L as QP, and then either adopt it or keep the
1.5KE20A with a stated reason other than "forced". If adopting:

- **QP:** check the gate drive and the DZ gate clamp against its V<sub>GS</sub>
  rating and threshold, and confirm the TO-252 pad mapping
  (1 G, 2/tab D, 3 S).
- **QI, QH, QMON, QRESET:** the 2N3904's 40 V V<sub>CEO</sub> is below the clamp.
  Select a ≥60 V V<sub>CEO</sub> small-signal BJT with a published collector
  cutoff (off-state leakage) figure, and recheck any base network or gain
  figure that the existing calculations rely on.
- **A5 second stage (R_AON, DZ_AON, C_AON):** at a ~43.5 V hot clamp the
  present 330 Ω / BZX55C22 dissipates about 1.4 W against 0.5 W. Redesign it
  so that worst-case P_AON is ≤28 V, then recheck the dropout floor at 6 V,
  the parts' dissipation and the startup time.
- **Everything else on P12 / VIN_SW:** recompute the §3.2 envelope table
  (LM2678 returns to its keyless in-service margin: 40 V operating, 45 V
  absolute; state that plainly), the B11 harness-entry TVS, the cold-margin
  line, and the new sustained-overvoltage ceiling.
- **Ledger (§7, L07):** update the QP row. The manager accepted the proposed
  re-allocation within the unchanged 100/500 µA totals; keep those totals.
- Update §3.4's option table so it reflects the decision.

### R12-REV-2 — name the exposure correctly

Restate L04 and the handoff's exclusion as **any sustained P12 above the
clamp standoff** (17.1 V with the 1.5KE20A, about 25.6 V with the 1.5KE30A),
explicitly including an alternator/regulator overcharge fault, and not as
"a 24 V jump start" alone. The owner has deferred this exposure as a named
vehicle-acceptance risk (tracker D-OVERVOLT-04).

### R12-REV-3 — deterministic UUIDs

`gen_logger_sch.py` currently gives every run fresh random UUIDs. Once the
owner creates the PCB, that breaks KiCad's schematic-to-footprint links on
every regeneration. Derive the UUIDs deterministically, for example `uuid5`
over a fixed namespace and the designator plus element role, so that
regenerating an unchanged parts table reproduces the `.kicad_sch` byte for
byte. Prove this by running the generator twice.

## Acceptance

- Regenerate, then rerun everything in `COMMANDS.txt`: ERC 0 at
  `--severity-all` (read from the JSON), capture checks all passing (update
  their assertions for any changed parts), `fp_area.py`, and
  `check_layout_closure.py`. Report the actual counts.
- Add closure checks for the new envelope numbers. They must assert physical
  quantities (voltages, dissipation, leakage), not copy the parts table.
- Two consecutive generator runs give a byte-identical schematic.
- Append a dated **"Revision LRA-12R"** section to `LRA12_HANDOFF.md`: the
  decision and why, changed parts, commands and results, and what remains
  open.
- Push `task/LRA-12R-<short-id>`. Report the branch and full commit IDs to the
  owner or manager. The manager records the claim in the tracker.

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

Pushing from this host requires the explicit key:
`git -c core.sshCommand='ssh -i ~/.ssh/id_ed25519_accord_public -o IdentitiesOnly=yes' push git@github.com:jgazeley/accord.git <branch>`.
KiCad CLI runs with `HOME` set to a temporary directory holding only the
installed global `sym-lib-table` and `fp-lib-table`; see `COMMANDS.txt`.

## Addendum, October 29 — R12-REV-4: put the keyless RS-485 circuit on the board

Added by Claude `pcb-manager`, session `42dd0e33-28b5-4936-847e-9c2e1d2488fa`
(`claude --resume 42dd0e33-28b5-4936-847e-9c2e1d2488fa`), after the LRA-12R
session had started. **Owner decision D-RS485-05:** Rev A carries the keyless
RS-485 circuit onboard, **same circuit and same footprints**, and it must stay
flexible for a bus topology that is not yet known. This replaces LRA-12's
"no transceiver, passive J3 header" provision
(`logger/hardware/communications/REV_A_PROVISION.md`). The keyless board is the
template for the buck, the car inputs and RS-485 alike (D-REUSE-02).

**Source circuit, read from `keyless/hardware/hondaPico.kicad_sch`** (read-only;
export its netlist to confirm):

| Keyless ref | Part / footprint | Connection |
|---|---|---|
| U5 | MAX3485, `Package_DIP:DIP-8_W7.62mm` (socketed in service) | 1 RO → GP9 (UART1 RX); 2 /RE and 3 DE tied → GP10; 4 DI ← GP8 (UART1 TX); 5 GND; 6 A; 7 B; 8 VCC +3V3 |
| C13 | 100 nF, `C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | U5 VCC decoupling |
| R13 | 10 k, axial DIN0207 vertical | DE//RE to GND: default listen |
| R14 | bias, axial | A to +3V3 |
| R15 | bias, axial | B to GND |
| R16 + JP1 | 120 Ω axial + `PinHeader_1x02_P2.54mm_Vertical` | A – R16 – RS485_TERM – JP1 – B: jumper-selectable termination |

On keyless, A and B leave on body harness J1 pins 14/15 (and the stock J2),
with a dedicated bus ground.

Implement it **unchanged** except where the logger forces a difference, and
state each difference:

1. **Pins:** GP8 TX, GP9 RX, GP10 DE//RE, as on keyless (these are the
   offered GP8/9/10 in `REV_A_INTERFACES.md` §1). Keep the tied DE//RE line;
   the shutdown-mode claim stays dropped (R04-REV-1). J3 must no longer
   carry UART1/GP10 to a header in parallel with U5. Keep or trim J3 for
   spare GP13 and power at your discretion, and say which.
2. **Bias values:** the keyless schematic says 270 Ω, its PCB 390 Ω (a
   recorded keyless parity warning). Use **390 Ω** unless the owner states
   otherwise; the manager has asked. Record the discrepancy and do not edit
   keyless.
3. **Flexibility for unknown topology:** termination already sits behind JP1.
   Also put the **bias pair behind its own jumper** (or fit-optional links),
   so the board can be either the biasing node or a plain mid-bus node.
   Default population: termination and bias **not linked**. The owner links
   them for the end-of-line or biasing node.
4. **Power-off paths, which keyless never had to meet:** the transceiver is on
   **switched** 3V3, so it draws nothing while parked. But with the logger
   off and another node biasing or driving the bus, (a) the MAX3485's bus
   input current with V<sub>CC</sub> = 0 (up to 1 mA at 12 V per the
   datasheet) and (b) R14 back-feeding a biased A line into the dead +3V3
   rail are real paths. Quantify both. The bias jumper removes (b) when
   unlinked; state what is left of (a). Carry the bus-side figure in the
   ledger as **a conditional exposure that only applies while an external
   node holds the bus active**, not inside the 2/5 µA allocation, and add it
   to the residual-risk table as a bench/vehicle gate.
5. **Connector:** bring A, B and a bus ground out on a connector the owner can
   wire. A spare position on the existing harness connector, or a dedicated
   3-position Mini-Fit Jr in the same family; your choice, stated.
6. **Protection:** keyless fits no TVS on A/B; do not add one unless you can
   name a concrete logger-specific reason.
7. Update `communications/REV_A_PROVISION.md` (or supersede it with a dated
   note), the BOM, the capture checks (assert U5's pin-to-net map, DE//RE
   tied and R13 to ground, and that the termination and bias are open with
   their jumpers out), the courtyard study, and the handoff.

LRA-04's bus comparison is no longer needed for Rev A; the tracker records
that. Do not redo it.
