# Manager-to-manager handoff — start in accord

Prepared October 28, 2026 by Codex `pcb-manager`, session `01a17045-1855-7af2-b76a-32c2b778cd64`. Historical bookmark: `codex resume 01a17045-1855-7af2-b76a-32c2b778cd64`. Successors use their own identities.

## Start prompt

You are the new `pcb-manager` for `jgazeley/accord`. The owner has moved active
project authority here. Claim the role with your own verified session ID in the
current tracker; this predecessor session is historical and must not remain a
parallel manager. Coordinate from documents/source; consult old conversations
only for a specific unresolved historical question.

Read in order: [current milestones/tasks](../PROJECT_MILESTONES.md),
[Rev A hardware context](../../logger/hardware/REV_A_CONTEXT.md),
[migration boundaries](../MIGRATION_MAP.md), and [LRA-01](LRA-01_POWER_INTERFACE.md).
Root `AGENTS.md` and the attribution convention apply. These are sufficient to
begin coordination; no full transcript or private-repo reconstruction required.

## Immediate objective and first actions

Ship a safe, testable logger Rev A prototype with autonomous power and a bounded
RS-485/CAN expansion path. Fuel calibration, dashboards, full CAN implementation
and future modules do not gate fabrication unless they reveal a specific hardware
requirement. Prototype order, board bring-up and unattended vehicle acceptance
are distinct; owner fabrication/hardware authorization remains necessary.

1. Check Git status/fetch before work; preserve other agents' edits. Record your
   own manager claim and which tasks actually have current claimants.
2. Issue/perform LRA-01 (power/firmware contract) with role-based ownership and
   firmware review. No evidence says the old power agent is currently running.
3. Prepare LRA-03 as-built consolidation and LRA-04 communications review in
   parallel. Use the task template; select exact paths and deliverables.
4. Retrieve missing detailed power material only as needed; make the chosen
   reviewed version active here. Use GitHub-pushed task revisions for remote agents.
5. Keep operational monitoring separate from implementation. Do not replace the
   functioning VM installation merely because its code lives in an old checkout.

## What works, and what is not done

Recorded deployed firmware is configured v0.8.1 from `84e8bd8`; the public
firmware source baseline derives from `426a43d`, all 15 source files verified in
prior extraction. Pi-disconnected road logging, one-second samples, ignition-off
Wi-Fi windows and later backlog delivery have physical/data evidence. Public
native and server tests passed; no new flash accompanied publication.

The VM still uses the historical receiver and guarded intake, not the public
systemd template. Last read-only heartbeat checked Oct 28 20:24 UTC: receiver
running, intake healthy, dashboard current, no admission holds/source errors.
Receiver `database_loading:false` is intentional; guarded intake performs the
private DB writes. Some old raw files retain open tails. Neither health nor a
source commit proves full physical acceptance.

Power remains a candidate, not an assembled/accepted automatic-cutoff circuit.
Shared-qualified IGN/startup timing, protection compatibility, current budget,
off-state signal paths and combined firmware behavior are the critical gaps.
The complete current logger circuit is scattered across historical notes; exact
latest opto component values and fitted ADC details remain unconfirmed. The new
hardware context explicitly distinguishes those gaps from known pin assignments.

Keyless is independent, with recorded installed BLE/automatic-operation evidence;
current settings and repeatability are not freshly verified. Its KiCad has known
warnings/parity discrepancies. Do not reuse it as the logger schematic.

SD capacity/retention, reset/offline time, fuel interpretation and production-host
parallel-feed work remain separate tasks. Historical date/fill corrections need
an audit before assuming they remain pending or have been completed. No successor
fuel delivery or current remote-agent activity was established by this transition.

## Source revisions and evidence

- Public pre-transition HEAD: `8261314a8ad69282908b61a7546cf11d418200c3`.
  It contains the already-extracted firmware/keyless/server core. Do not repeat.
- This handoff and tracker arrive together in the coordination-transition commit;
  use `git log --format=fuller -- coordination/PROJECT_MILESTONES.md` to identify
  it without embedding a self-referential commit hash.
- Historical private master: `1e994494f933da99636942d6ec135e857f2b3f6b`;
  logger branch `426a43df1ea3bb60540b12e99b3ae9862dec3bb0`; power candidate `9527a14`.
- Public evidence: component SOURCE_MANIFEST files, `logger/server/VALIDATION.md`,
  keyless KiCad validation. Historical deployment/power review locations are
  identified in the migration map and hardware context.

Optional predecessor bookmarks: this manager's author block; firmware/migration
`codex resume 01a17526-034c-78f1-9d09-24c3b88c3dc7`; remote power
`codex resume 01a17407-4357-7031-b3ac-a51c97864fbe`; earlier power
`codex resume 01a173c4-d2fd-7f71-a396-8996d502387b`. History is not a task dependency.

## Boundaries, staffing and integration

No specialist is newly spawned by this handoff. Suggested roles: remote electrical
lead for LRA-01/02, logger developer for contract review/05, local bench for 07,
KiCad owner for 06 then 08, bounded browser reviewer for 04. With limited agents,
combine sequential responsibilities; do not multiply sessions unnecessarily.

The hardware-side VM/portable Pi can support authorized tests; remote agents have
no bench and exchange selected artifacts via GitHub. Task ownership is by role
and scope, with a current session claim; IDs preserve authorship and optional
conversation access. One editor per artifact. Manager integrates reviewed task
branches and updates one tracker. Browser conclusions require local review.

Existing private runtime directories and DB/dashboard data remain where they are.
Do not delete old build-named runtime state, change cron, restart/replace services,
flash, modify DB records or order boards as part of taking over management.
Those need explicit owner scope; ongoing authorized automated ingestion continues.
Keep credentials, configured binaries, personal recordings and database data out
of public Git. Private uncommitted fuel/archive work remains preserved in the old
checkout; importing it wholesale would lose the selective-migration boundary.

The predecessor will stop active management after delivering this handoff. Your
first bounded outcome is an acknowledged manager claim and a reviewable LRA-01
assignment, not another broad reorientation exercise or a second task tracker.

> **Required agent attribution:** Follow `logger/coordination/AGENT_ATTRIBUTION.md` relative to this repository root. Use your own tool, role and verified current session ID for Git author and committer (`<Tool> <role> [<short-id>]`), using per-command settings. End commits with `Agent-Session: <role>` and your full tool-specific session-ID trailer (`Codex-Session-ID`, `Claude-Session-ID` or `Antigravity-Session-ID`). This includes documentation-only work. Identify yourself and your resume command in coordination documents and dated updates. Preserve predecessor identity and original attribution when transporting commits. If an ID is unavailable, state that explicitly; never invent or borrow one. Include this requirement in subsequent seeds and handoffs.
