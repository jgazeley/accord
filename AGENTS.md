# Agent instructions and migration context

Prepared October 27, 2026 by Codex `logger-wifi-piless`, session
`01a17526-034c-78f1-9d09-24c3b88c3dc7`.
Bookmark: `codex resume 01a17526-034c-78f1-9d09-24c3b88c3dc7`.
This identifies the migration/documentation work, not authorship of all copied
firmware or hardware. Successors must use their own verified session identities.

## Active authority — October 28, 2026

Owner direction: this repository is the authoritative home for new active
Accord development, hardware and coordination. `jgazeley/accord-logger` is
historical reference and retained deployment storage, not a competing tracker.
Read [current tasks](coordination/PROJECT_MILESTONES.md) and the
[current manager handoff](coordination/handoffs/PCB_MANAGER_LAYOUT_HANDOFF_2026-10-29.md).
New agents start here; recover only missing material with provenance/public review.
The successor manager claims its own identity; predecessor sessions are history.

Artifact owners: manager owns root/coordination; logger role owns logger firmware;
bridge role owns logger/server; electrical/KiCad roles own logger/hardware with
one claimed edit scope; keyless role owns keyless. Preserve others' work and stage
only explicit task paths. The single tracker records actual claimants/dependencies.
Publishing source does not authorize deployment, hardware changes or DB writes.

Prepared October 28, 2026 by Codex `pcb-manager`, session `01a17045-1855-7af2-b76a-32c2b778cd64`. Historical bookmark: `codex resume 01a17045-1855-7af2-b76a-32c2b778cd64`. Successors use their own identities.

### Current manager claim — October 29, 2026

Current manager: Codex `pcb-manager`, session
`01a18447-07c2-7bb3-8318-9b276cfdb3b8`.
Bookmark: `codex resume 01a18447-07c2-7bb3-8318-9b276cfdb3b8`.
Resumed October 29 after the owner closed the Claude manager shift. Identity
verified again from matching `CODEX_SESSION_ID` and `CODEX_THREAD_ID`.
Current assignment: remove layout blockers using the existing project documents
and design candidates; do not reconstruct transcripts or historical work.

Preceding manager, historical attribution: Claude `pcb-manager`, session
`630dea87-5e4d-4bad-a1ff-d41b3a5f509b`
(`claude --resume 630dea87-5e4d-4bad-a1ff-d41b3a5f509b`). That shift completed
the LRA-03 integration, integrated LRA-06, recorded the owner's measurements
and board envelope, and reviewed the LRA-11 candidate. Earlier in the day this
Codex session held the manager role before that Claude shift.

Scope: root/coordination, task assignment and integration. Specialist claims and
dependencies remain in `coordination/PROJECT_MILESTONES.md`. The preceding manager
identities and bookmarks are historical attribution.

## Core-document maintenance — owner direction, October 29

Current project documents are the first source for onboarding and handoff.
Use `coordination/PROJECT_MILESTONES.md` for live claims, decisions and next
steps; `coordination/HANDOFF_INDEX.md` locates the current handoff and packets.
`logger/hardware/REV_A_CONTEXT.md` summarizes hardware and links the detailed
as-built, electrical and KiCad sources. Keep module READMEs accurate about
implemented behavior and limitations.

At each material status change and before a manager handoff, audit those core
entry points against the current artifacts and owner statements. Correct stale
summaries and links; mark historical records clearly instead of stacking
contradictory current instructions. Record what was checked and any unresolved
metadata in the handoff. Do not create another task tracker.

Git, detailed reviews, session IDs/bookmarks and transcripts provide deeper
history when a specific question needs it; they are not mandatory onboarding
reads. Preserve attribution and provenance. Record an owner-reported task as
already assigned even if its agent identity/branch is not yet supplied; a usage
wait does not authorize dispatching a duplicate or editing its claimed scope.

Recorded by Codex `pcb-manager`, session
`01a18447-07c2-7bb3-8318-9b276cfdb3b8`
(`codex resume 01a18447-07c2-7bb3-8318-9b276cfdb3b8`).

## Project boundaries

- `keyless/` contains local Pico W keyless firmware, native tests and KiCad
  hardware. It does not communicate with or depend on the logger's VM bridge.
- `logger/` contains Pico W recording/upload firmware, native tests and build
  tooling. `logger/server/` now contains the raw receiver and trip conversion core;
  database/dashboard migration remains outside this public repository.
- The Pi 4 is a portable bench, not a normal ingestion dependency.
- Preserve the existing source repositories and other agents' worktrees.
  Copying files here does not authorize flashing or service cutover.
- Keep public READMEs focused on modules, build instructions and actual
  limitations. Put agent bookmarks, migration details and handoffs here or in
  linked coordination documents.

## Source provenance

### Historical name and path map

| Historical name/path | Meaning in this project |
|---|---|
| `hondaPico` in documentation | Usually the accord-keyless board/module. Check context: the old name was also used for development sketches and directories. |
| `hondaPico/hondaPico.ino` | Temporary Wi-Fi web dashboard; not the current keyless firmware. |
| `benchlink/uart_main/` | Current keyless firmware, now `keyless/firmware/accord-keyless/`. |
| `hondaPico-kicad/` | Keyless hardware, now `keyless/hardware/`; retain `hondaPico.kicad_pro` as the project filename. |
| `picow-logger`, `benchlink/picow-logger/` | Accord logger firmware, now `logger/firmware/accord-logger/`. The old directory also held server tools and history; do not import it wholesale. |
| `bridge`, `accord-bridge` | Logger upload/processing service; not part of keyless. |

The two Pico modules are distinct. Do not globally replace `hondaPico` in code,
protocol identifiers or KiCad references merely to modernize the name.

The historical repository is `jgazeley/accord-logger`. Each component's
`SOURCE_MANIFEST.json` records the source revision, paths, hashes and validation.

- Keyless firmware came from `benchlink/uart_main/`; its sketch was renamed
  `accord-keyless.ino`. The older `hondaPico/hondaPico.ino` is a development
  Wi-Fi dashboard and is not the live keyless source. Hardware came from
  `hondaPico-kicad/`, with `hondaPico.kicad_pro` as the main project.
- Logger firmware came from `session/logger-wifi-scheduling-01a17526` at
  `426a43df1ea3bb60540b12e99b3ae9862dec3bb0`, with firmware bytes matching the
  v0.8.1-dev build manifest. The historical master branch contains older logger
  firmware and must not be substituted for this baseline.

All copied firmware contents initially remained unchanged; sketch names,
test include paths and build-tool paths were adapted. Historical comments may
still refer to old paths. Hardware design files retain their original contents;
a local Custom symbol library and table were added from embedded definitions.

## Next work and configuration

- **Before the next configured logger build**, prepare an independent private
  `secrets.h`. The old shared `hondaPico/secrets.h` arrangement does not exist
  here. Read [logger/NEXT_AGENT.md](logger/NEXT_AGENT.md). The build helper
  requires explicit `--secrets`; otherwise it uses dummy credentials.
- Read [server migration notes](docs/SERVER_MIGRATION_NOTES.md) before collecting
  or adapting server files. They identify stale guidance, files absent from Git,
  runtime data to retain and the guarded database-intake boundary.
- Keep credentials, configured firmware binaries and private runtime data out
  of source control. Inspect exact staged contents before every public commit/push.
- Owner-approved licensing intent is free reuse with credit. Original software
  and docs use Apache 2.0; original hardware uses CERN-OHL-P-2.0. Preserve
  notices and third-party terms; see [LICENSING.md](LICENSING.md). The unused
  local `keyless/hardware/3d/039301160.stp` is excluded from Git pending license
  provenance. Do not force-add it or include it in a public archive.
- The new GitHub repository is `jgazeley/accord`. The initial import is published. Inspect current Git state before proceeding.

## Required attribution

Follow [logger/coordination/AGENT_ATTRIBUTION.md](logger/coordination/AGENT_ATTRIBUTION.md).
Preserve original authorship when transporting work. Do not change shared or
global Git identity. Use this block in new or refreshed seeds and handoffs:

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

## Public server preparation — October 28, 2026

Codex `pcb-manager`, session `01a17045-1855-7af2-b76a-32c2b778cd64`
(`codex resume 01a17045-1855-7af2-b76a-32c2b778cd64`).
Historical preparation checkpoint: the public server stops at raw storage and trip JSON. The historical server
migration note describes a broader private installation; collecting its DB,
renderer, personal recordings or private settings is not required here.
Keep the private development repository and live services unchanged.
