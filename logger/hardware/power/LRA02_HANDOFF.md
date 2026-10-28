# LRA-02 first bounded return to pcb-manager

Prepared October 28, 2026 by Codex `logger-power`, electrical lead.
Session: `01a18463-5ed7-7041-ad90-ec3a7480c4e6`, verified against matching
CODEX_SESSION_ID / CODEX_THREAD_ID.
Resume: `codex resume 01a18463-5ed7-7041-ad90-ec3a7480c4e6`.

This acknowledges the returning-engineer assignment in
`coordination/handoffs/LRA-02_COMPONENT_MARGINS.md`, fetched from main after
owner notification of `1d9e07d`. Manager owns the tracker; no coordination file
was edited. Branch **`task/LRA-02-01a18463`**, parent
**`a85f185c4dfc593b0a5b7284170e904cbf8a54c1`**. The published task branch includes
that LRA-01 prerequisite. Integrate the parent first if it is absent; do not
mistake this incremental return for an independent replacement of LRA-01.
Return commit is supplied in the final handoff response and obtainable with
`git log -1 --format=fuller -- logger/hardware/power/LRA02_HANDOFF.md` on this
branch. No main merge, purchase, fabrication, live firmware or hardware action.

## Delivered

- [COMPONENT_MARGIN_CLOSURE.md](COMPONENT_MARGIN_CLOSURE.md): exact capacitor
  candidates, conditional effective-C/ripple/leakage calculations, semiconductor
  comparisons, loaded-drive and parked-current ledger, unresolved requirements
  and bounded fixture plan.
- [BOM_DELTA.csv](BOM_DELTA.csv): fourteen rows, explicit conditional/retained/
  paired-proposal dispositions. This is not a merged or accepted BOM.
- [check_component_margins.py](check_component_margins.py): eleven arithmetic,
  budget-gap, CSV and original-artifact checks. It intentionally verifies that
  the current screen **does not close** the proposed allocations.

Concrete choices: CCLK **T491D336K016AT**, 33 µF/16 V; A5 input one and output
two **GRM32ER71H475KA88L**; buck **EEUFR1H101 / EEUFR1C102**; conditional UOE
**74AHC1G17GV**; proposed paired QP **IPD50P04P4L11ATMA2** and DZ
**BZX55C10-TAP**. Retain counters, regulator, Schmitt clock gate and topology.
QP's asymmetric **+5/-16 V absolute gate rating** requires a new **-14..+1 V**
qualification envelope. It is not a drop-in under the old 18 V criterion.

CCLK's engineering stack is 24.057–43.923 µF; adding 100 µA load gives a
0.21871 V/ms falling-slew screen. A5 ceramic DC-bias/aging retention thresholds
are explicit, rather than invented guaranteed bias curves. Buck capacitor
catalog ratings do not establish loop compatibility. No unchanged inherited
file or manifest was edited; the LRA-01 contract/reviewer files remain untouched.

## Findings and remaining blockers

The selected clock capacitor exposes previously omitted leakage. With the UOE
room saving, the A5 subtotal is **46.175/302.85 µA**, before input leakage,
other capacitors and discretes. The three CD packages have unequal current
limits but still total 1.5/45 µA; their 5 V table is not a literal 5.11 V bound.
The connection audit excludes three hard-grounded inputs. The remaining
conservative pin-leakage screen plus other-cap reserve reaches
**59.875/344.85 µA**; a higher-voltage CD sensitivity screen reaches
61.375/389.85 µA. These mixed-condition sums neither guarantee passage nor
prove every physical unit fails. **100/500 µA whole-system acceptance remains
unchanged and unproved.** Proposed reallocation 65/375 A5, 5/75 QP, 20/25
entry/gates/PCB, 10/25 interfaces is only a feasibility envelope, not adopted.

| Next evidence | Paper/manufacturer work or physical work |
|---|---|
| A5 current proof | Obtain limits for the audited 29 logic inputs and discrete paths, including TPS709 low-load regulation/ground-current behavior; no 100 µA preload |
| Capacitors | Exact Murata approval-sheet bias/aging/IR/ESR; combined CCLK stress/DC qualification; FR capacitor loop-equivalence analysis, then bias/temperature/ripple/load-step measurements |
| QP/DZ | Off leakage at actual nonzero VGS, hot clamp range and inrush/SOA proof, then assembly gate/thermal tests; published 70 µA hot IDSS is at VGS=0 |
| Drivers/opto/clock | Actual-network hot transistor/opto limits, loaded CMOS extra ICC, oscillator startup/load bounds; assembled endpoint/ramp tests follow. ICBO is not ICE under a 100k base pulldown |
| Vehicle protection | Owner feed/pulse/source/harness/fuse requirements are genuine external inputs; <=28 V protected P12 remains mandatory. Neither TVS candidate closes it |
| Isolation | LRA-03/04 accept aggregate 10/25 µA energized-interface budget and upstream divider isolation; no competing as-built/bus design supplied |

The next bounded electrical action is supplier specification closure for the
audited nodes and selected parts, followed by reviewed fixture
qualification. The document defines 12–16 V simulated supply, 50/250/500 mA
staged battery-source limits and 30 mA IGN limit, with all vehicle inputs
initially disconnected. This is a future test specification, not authorization
to operate hardware. Disconnected-input results cannot earn whole-system acceptance.

## Reviews and validation

Electrical/manager review: disposition each BOM row and proposed contract
addendum before schematic freeze. R03/R04 remain open; this packet's first
bounded deliverable is complete as a reviewable paper package. Original LRA-01
candidate remains pending independent firmware review.

Firmware review items remain GP6/4 mA/2.6 V, early HOLD/startup, <=10 ms power
supervision, qualified-IGN semantics, monotonic-clock allowance, shutdown
generations/SD handling and watchdog. This package introduces **no GPIO,
polarity, divider-count or 1770/1800/1801 s policy change**. Reviewer must check
startup feasibility with actual A5/VCLK ramps and changed capacitance. DOR
forward-drop/thermal/USB recovery and larger COUT decay tests are still required.

Run from repository root:

```sh
python3 -B logger/hardware/power/check_max_on_logic.py
python3 -B logger/hardware/power/check_cutoff_margins.py
python3 -B logger/hardware/power/check_interface_contract.py
python3 -B logger/hardware/power/check_component_margins.py
```

Results: **11 + 8 + 14 + 11 = 44 checks pass**. Eleven imported SHA-256 hashes
match the unchanged manifest. All three BOM CSVs have consistent row widths;
new delta has 15 rows including header, 8 columns. `git diff --check` passes.
Tests validate models/arithmetic/artifact integrity only; no physical tests,
configured firmware build or firmware implementation tests were performed.
Exact staged scope/content reviewed before publication: four allowed new files,
no downloaded manufacturer PDFs, credentials, binaries or private runtime data.
No uncommitted owned work remains after the return commit.

> **Required agent attribution:** Follow `logger/coordination/AGENT_ATTRIBUTION.md`
> relative to this repository root. Use your own tool, role and verified current
> session ID for Git author and committer identity (`<Tool> <role> [<short-id>]`),
> with per-command settings. End each new commit message with `Agent-Session: <role>`
> and your full tool-specific session-ID trailer (`Codex-Session-ID`,
> `Claude-Session-ID` or `Antigravity-Session-ID`). This includes documentation-only
> commits. Identify yourself and your resume command in new coordination documents
> and dated updates. Preserve predecessor bookmarks and original attribution when
> transporting existing commits. If your ID is unavailable, say so rather than
> inventing one. Include this requirement in any seeds or handoffs you create.
