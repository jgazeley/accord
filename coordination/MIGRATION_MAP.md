# Active-source migration and historical boundaries

Prepared October 28, 2026 by Codex `pcb-manager`, session `01a17045-1855-7af2-b76a-32c2b778cd64`. Historical bookmark: `codex resume 01a17045-1855-7af2-b76a-32c2b778cd64`. Successors use their own identities.

Owner direction: `jgazeley/accord` is the preferred and authoritative home for
new active development, hardware and coordination. Selectively recover missing
material from `jgazeley/accord-logger`; do not clean up or migrate everything.

## Already migrated — do not repeat the extraction

| Historical source | Active destination | Provenance |
|---|---|---|
| `benchlink/uart_main/` | `keyless/firmware/accord-keyless/` | `keyless/SOURCE_MANIFEST.json`, initial import `8300d68` |
| `hondaPico-kicad/` | `keyless/hardware/` | Same manifest; original board contents and known warnings retained |
| Logger task-branch firmware | `logger/firmware/accord-logger/` | `logger/SOURCE_MANIFEST.json`; source `426a43d`, v0.8.1 baseline |
| `bridge/host/`, canonical converter and trip engine | `logger/server/host/`, `logger/server/upstream/` | `8261314`, server manifest and validation |
| Raw/upload contracts and synthetic tests | `logger/protocols/`, logger/server tests | Component manifests and validation |
| Current cross-project task authority | `coordination/PROJECT_MILESTONES.md` | This transition, derived from old M1–M6 and Oct 28 owner priorities |

Public `8261314` is the pre-coordination baseline. Historical private master
`1e994494f933da99636942d6ec135e857f2b3f6b` and logger branch
`426a43df1ea3bb60540b12e99b3ae9862dec3bb0` anchor the summaries. Source snapshots
are provenance; later changes here must record new validation rather than
pretend to retain the original source hashes.

## Selective material still to recover

- Power detailed design/BOM/check scripts: historical `logger-power/`, reviewed
  `9527a14`. Active destination when selected: `logger/hardware/power/`.
  [Rev A context](../logger/hardware/REV_A_CONTEXT.md) carries immediate blockers
  and interface requirements. No blanket copy of inventory or session exports.
- Consolidated current as-built: reconstruct from corrected historical notes,
  ADC specification and owner confirmation. Active destination: logger hardware.
  Unknown component values must stay unknown, not be inferred from a proposal.
- Fuel/keyless follow-ups: move the needed task context and anonymized fixtures
  when claimed. Personal readings, fill records and road recordings stay private.
- Private DB writer, dashboard and guarded intake: their ongoing deployment is
  not migrated by source/coordination publication. Generic code can be considered
  later with an explicit dependency/public-data review; no such migration is
  needed to order a logger prototype.

## Runtime survives repository transition

The hardware-side VM still runs the old receiver package and guarded intake
from retained `build-wifi-trial-20261026/` and `build-vm-intake/` directories in
the historical checkout. Their names do not make them disposable. The receiver's
`database_loading:false` is intentional; the separate guarded loader performs
automatic DB writes. Read-only operations/rollback remain documented in old
`benchlink/vm-intake/README.md`. Do not run the public receiver against that state
or reinstate Pi ingestion as a migration shortcut.

The Pi is a portable bench; another remote machine has no hardware access.
GitHub task branches and reviewed artifacts are the cross-machine interface.
Future production-server and VM parallel-feed work remains separate and unbuilt.
No credentials, database, runtime state or recordings are needed in public Git.

## Integration rule

New agents start here. If an old task has uncommitted/unpublished work, preserve
it and integrate only the chosen scope once, retaining original authorship and
identifying the transporting agent. Record source/destination revisions and
adaptations. Do not ask the predecessor to continue a parallel tracker. If an
emergency requires changing retained runtime, coordinate that single scoped
exception through this manager and owner; the old tree is not thereby restored
as development authority.

Before publishing, inspect exact staged paths, configuration literals and evidence;
check known private credentials without printing them. Private agent transcripts,
configured binaries, deployment settings and personal records remain outside this
repo. Existing review-only briefing/proposal documents were not wholesale copied.
