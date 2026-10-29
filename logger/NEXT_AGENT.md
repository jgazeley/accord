> LRA-05 candidate update, October 29, 2026 — Codex `logger-power`, session
> `01a18463-5ed7-7041-ad90-ec3a7480c4e6`.
> Resume: `codex resume 01a18463-5ed7-7041-ad90-ec3a7480c4e6`.
> Firmware is now the isolated `0.8.1-lra05-dev` candidate described in
> [LRA05_HANDOFF.md](coordination/LRA05_HANDOFF.md). The historical import
> provenance below remains unchanged; its statement of unchanged behavior
> describes the import, not this candidate.
>
> Manual power remains the default: `firmware/accord-logger/power_config.h`
> defines `LOGGER_POWER_QUALIFIED=0`. Qualified GP5/GP6 mode is an explicit
> opt-in (`1`) pending manager/firmware review and hardware qualification.
> Do not select it for the existing manual wiring merely to try the firmware.
>
> From the repository root, run `python3 logger/tools/test_native.py` and
> `python3 logger/tests/check_power_converter.py`. To compile both modes with
> dummy credentials, run
> `python3 logger/tests/build_power_candidates.py --output /tmp/lra05-builds`.
> This stages isolated source copies and invokes the unchanged documented
> `tools/build_candidate.py` helper; only the qualified copy's config default
> changes to `1`. Manifests record effective source/config hashes. No private
> secrets are read and neither profile is flashed. The ordinary build helper
> still builds the checked-out manual default unless explicitly configured.
>
> Rollback is a manual-mode build (`0`), which reserves no GP6, installs no
> power alarm, and enables no application watchdog. For exact pre-LRA-05 source,
> use reviewed main base `2c52afd7b5609444641d02cd420bc252a1f494c7` in an isolated
> checkout. Deployment/physical wiring changes require their own authorization.

> Current coordination, October 28, 2026: new work starts in this repository.
> Read [current tasks](../coordination/PROJECT_MILESTONES.md); power/shutdown
> interface agreement precedes that implementation. The configuration instructions
> below remain applicable; this older packet does not itself assign a new task.
> Updated by Codex pcb-manager, session `01a17045-1855-7af2-b76a-32c2b778cd64`.

# Next agent: logger configuration after restructuring

Prepared October 27, 2026 by Codex `logger-wifi-piless`.
Current copying session: `01a17526-034c-78f1-9d09-24c3b88c3dc7`.
Bookmark: `codex resume 01a17526-034c-78f1-9d09-24c3b88c3dc7`.
A successor must use its own verified session ID; retain this one as history.

This copy is bounded to Pico W logger firmware, native tests and build tooling.
Receiver/server migration is deferred. The copied source is v0.8.1-dev from
`session/logger-wifi-scheduling-01a17526` at `426a43d`, with source hashes in
`SOURCE_MANIFEST.json`. The sketch is now
`firmware/accord-logger/accord-logger.ino`.

## Required before the next configured build

1. Create or update a private, logger-specific `secrets.h` using
   `firmware/accord-logger/secrets.h.example`. The former shared/symlinked
   `hondaPico/secrets.h` path is obsolete in this layout. No private header was
   copied, and the keyless module does not supply logger credentials.
2. Populate `WIFI_SSID`, `WIFI_PASS`, `API_TOKEN`, `UPLOAD_HOST` and
   `UPLOAD_PORT` from the owner's existing private configuration. Verify the
   receiver token and current endpoint on the deployment machine. The host is
   a literal IPv4 address without a scheme or path. The example address and
   token are placeholders, not deployment settings. Empty/omitted host disables
   uploads. Never print credentials in handoffs or commit them.
3. Pass the header explicitly with `tools/build_candidate.py --secrets` and
   use a private dedicated `build-*` output directory. Without `--secrets`,
   the helper always builds with dummy credentials, even if a local header
   exists. Both firmware binaries and generated build files can embed secrets.
4. Run the native tests and compile using Arduino-Pico 6.1.0 and bundled
   SdFat 2.3.1. Keep the new build manifest with the private build output.
   No board was flashed during migration, and no receiver was contacted.

The renamed sketch and relocated tools are the changes here; all firmware
behavior remains as copied. New build hashes may differ from historical
artifacts because the sketch/build paths changed. This copy is not proof of
what is currently installed on a physical board.

## Attribution for subsequent work

> **Required agent attribution:** Follow `coordination/AGENT_ATTRIBUTION.md`.
> Use your own tool, role and verified current session ID for Git author and
> committer identity (`<Tool> <role> [<short-id>]`), with per-command settings.
> End each new commit message with `Agent-Session: <role>` and your full
> tool-specific session-ID trailer (`Codex-Session-ID`, `Claude-Session-ID` or
> `Antigravity-Session-ID`). This includes documentation-only commits. Identify
> yourself and your resume command in new coordination documents and dated
> updates. Preserve predecessor bookmarks and original attribution when
> transporting existing commits. If your ID is unavailable, say so rather than
> inventing one. Include this requirement in any seeds or handoffs you create.
