# Server migration: source map and outstanding work

Recorded October 27, 2026 by Codex `logger-wifi-piless`.
Session: `01a17526-034c-78f1-9d09-24c3b88c3dc7`.
Bookmark: `codex resume 01a17526-034c-78f1-9d09-24c3b88c3dc7`.

This note records an assessment, not a server migration. No server files have
been copied into this new project and no live services or data were changed.
The Pi 4 is a portable flashing/observation bench. Keyless operates locally
and does not depend on the logger's VM receiver.

## Verified source baseline and current path

The assessment fetched `jgazeley/accord-logger`; `origin/master` was
`1e994494f933da99636942d6ec135e857f2b3f6b`. The server source paths below were
identical on that revision and Wi-Fi scheduling branch revision
`426a43df1ea3bb60540b12e99b3ae9862dec3bb0`.

The October 27 deployment records describe this path:

```text
Pico W Wi-Fi upload
  -> VM receiver and durable raw storage
  -> cardconv.py -> tripd -> trip packet spool
  -> guarded intake -> existing tripload.py -> database -> dashboard
```

Cron runs intake every minute and at boot. Intake supervises the receiver and
guards database admissions. The receiver's direct database loader is disabled;
`/health` reporting `database_loading:false` does not mean automatic guarded
intake is disabled. Check intake's own status for that.

These are source/configuration and recorded deployment findings. The live VM
was not contacted during this assessment. Verify its actual files and schedule
before a future cutover.

## Active source available in the historical repository

Paths in this table are relative to the old `accord-logger` repository.

| Responsibility | Files |
|---|---|
| HTTP upload handling and durable raw storage | `bridge/host/server.py`, `storage.py` |
| Service and processing worker | `bridge/host/accord_bridge.py`, `pipeline.py`, `replay.py`, `events.py` |
| Pico raw-log timestamp conversion | `benchlink/picow-logger/tools/cardconv.py` |
| Canonical trip building | `benchlink/tripd` |
| Receiver supervision and guarded database admission | `benchlink/vm-intake/intake.py` |
| Current deployment configuration and admission policy | `benchlink/vm-intake/vm.json`, `policy.json` |
| Operator commands | `bridge/host/bridgectl.py` |

`events.py` is imported by the service; MQTT use and its `paho-mqtt` dependency
are optional. Despite its Pi-era name and comments, `tripd` remains essential
server code. `cardconv.py` is server code even though it currently sits beneath
the firmware directory. Retain one canonical copy of each processing tool.

Carry forward relevant tests from `bridge/tests/`, `benchlink/tests/` and the
converter tests under `benchlink/picow-logger/tests/`. Review their fixture and
path dependencies; the bridge suite includes firmware-client integration tests
and historical recording fixtures, so copying only the test scripts is not enough.

The processing hash calculated from `tripd`, `cardconv.py`, timezone,
`pipeline.py` and `replay.py` matches the current intake policy:
`17b75fcf59343da6962dd49e1e2dd7ee76528cb57c367dc215e75fc81035aefa`.

## Stale or misleading instructions

- `bridge/README.md` still describes an October 24 deployment hold, an active
  Pi/VM pipeline and an earlier receiver-only trial. Those statements do not
  describe the subsequently deployed October 27 guarded VM intake.
- `bridge/DEPLOY_hacienda_2026-10-24.md`, `MIGRATION_PLAN.md`, the installation
  script and systemd unit concern earlier/proposed production deployment.
  Do not treat them as a record of the current cron-managed VM installation.
- `benchlink/README.md` contains obsolete Pi ingestion instructions and says
  the Pico logger is not yet built. Do not import it as current operating guidance.
- `build-wifi-trial-20261026/` and `build-vm-intake/` sound disposable but hold
  retained deployment files, raw data, status, logs or backups on the VM.
  They must not be removed as ordinary compiler output.
- The bridge environment example describes direct full-spool database loading.
  The current installation instead uses guarded intake. Do not enable that
  direct loader as a shortcut during migration.

The better current references in the historical repository are
`benchlink/vm-intake/README.md`,
`coordination/reviews/VM_AUTO_INTAKE_2026-10-27.md`, and
`coordination/reviews/MORNING_TRIPS_2026-10-27.md`. The recorded replacement
crontab is `coordination/evidence/vm-auto-intake-20261027/crontab.after`.

## Missing from Git / collect from the deployment machine

These paths describe the other machine, not this workspace:

| Item | Recorded location / action |
|---|---|
| Database loader and its imports | `/srv/agent_share/honda/service/tripload.py`; inspect and collect its actual dependencies |
| Dashboard renderer and its imports/assets | `/srv/agent_share/honda/tools/build_accord_record.py`; inspect and collect dependencies |
| Receiver launcher | `/srv/agent_share/pcb/build-wifi-trial-20261026/run_receiver.py`; inspect its environment handling and package paths |
| Private receiver configuration | Same directory, `receiver-env.json`; retain privately and derive a placeholder-only template |
| Deployed receiver package and upstream tools | Same directory, `accord-bridge/`; compare actual deployed bytes with the selected source revision |
| Operational state | Same directory, `state/`: raw uploads, completion records, processed records, pending packets and processing state |
| Database, dashboard and backups | `/srv/agent_share/honda/accord_maintenance.db`, `accord_record.html`, backups and related state |
| Actual scheduler and intake state | Current VM crontab and `/srv/agent_share/pcb/build-vm-intake/`; compare against recorded evidence |

The loader, renderer, launcher and private configuration were not found tracked
in this repository and are unavailable at those paths on this machine. Their
dependency closure cannot be claimed complete from the available source.
Runtime data and credentials are separate from the future public source copy.

## Adaptations required before a server copy can be deployed

1. Choose the new server source layout and runtime-state locations. Update
   `vm.json`'s old absolute paths, launcher paths, cron commands, logs and locks
   together. Keep runtime state outside disposable build directories.
2. Adapt `bridge/tools/stage-upstream.sh` and `pack.sh`: they assume the old
   `benchlink/tripd` and `benchlink/picow-logger/tools/cardconv.py` layout. Preserve
   byte-identical canonical processing tools rather than creating edited variants.
3. Adapt tests and their data paths, including firmware integration references.
   Review any real vehicle recordings before including them in public fixtures.
4. Preserve/review `policy.json`: its logger unit, cutover time, historical
   exclusions and processing hash are deliberate data-admission settings.
   Editing processing-file contents changes the hash even if behavior seems
   unchanged. Review any new hash against existing processed state; do not
   simply bypass the version check.
5. Preserve the guarded loader API and backup/transaction behavior. Confirm
   receiver direct loading remains disabled and only one ingestion scheduler
   is active. Keep packet identities and existing state through the transition.
6. Replace stale deployment instructions with the chosen actual arrangement.
   Collect and review the deployed launcher before rewriting it. Source copying
   is separate from any live service or database cutover.

The old Pi acquisition/delivery tools (`vssrec`, `tripsend`, `tripcycle`,
`tripdrain`, `carboot` and related scripts) are not requirements for normal
Pico-only ingestion. Retain their history and any useful bench tooling
separately. Do not restore the old Pi cron as an automatic migration fallback.

## Attribution for the next agent

The convention is available at
[logger/coordination/AGENT_ATTRIBUTION.md](../logger/coordination/AGENT_ATTRIBUTION.md).
The bookmark above belongs to the assessment author; use your own session ID.

> **Required agent attribution:** Follow `logger/coordination/AGENT_ATTRIBUTION.md`
> relative to the new project root. Use your own tool, role and verified current
> session ID for Git author and committer identity (`<Tool> <role> [<short-id>]`),
> with per-command settings. End each new commit message with `Agent-Session:
> <role>` and your full tool-specific session-ID trailer (`Codex-Session-ID`,
> `Claude-Session-ID` or `Antigravity-Session-ID`). This includes documentation-only
> commits. Identify yourself and your resume command in new coordination documents
> and dated updates. Preserve predecessor bookmarks and original attribution when
> transporting existing commits. If your ID is unavailable, say so rather than
> inventing one. Include this requirement in any seeds or handoffs you create.
