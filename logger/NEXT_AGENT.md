# Logger build configuration and LRA-05 candidate notes

**This is a configuration reference, not a task assignment.** Despite the
filename it does not tell you what to work on — the tracker does. It is
[linked from AGENTS.md](../AGENTS.md) because the `secrets.h` gate below is
still unconsumed: no private header exists in this tree, so nothing here has
been done yet.

Current state, October 29, 2026, consolidated by Claude `pcb-manager`, session
`630dea87-5e4d-4bad-a1ff-d41b3a5f509b`, replacing three stacked dated banners
that had to be reconciled in reverse order.

- **Firmware** is the isolated `0.8.1-lra05-dev` candidate from LRA-05, now
  integrated as a reviewed candidate. See
  [LRA05_HANDOFF.md](coordination/LRA05_HANDOFF.md). The import-provenance
  section further down describes the *original copy*, not this candidate.
- **Manual power is the default.** `firmware/accord-logger/power_config.h`
  sets `LOGGER_POWER_QUALIFIED=0`. Qualified GP5/GP6 mode is an explicit opt-in
  pending hardware qualification. Do not select it against the existing manual
  wiring just to try the firmware.
- **Corrected October 29:** the original text below says receiver/server
  migration is deferred. That is **no longer true** — `logger/server/` now holds
  the raw receiver and trip conversion core. Database and dashboard migration
  remain outside this repository.
- **Superseded October 29:** the former note that power/shutdown interface
  agreement must precede implementation. LRA-05 is implemented and integrated.

Tests, from the repository root:

```
python3 logger/tools/test_native.py
python3 logger/tests/check_power_converter.py
python3 logger/tests/build_power_candidates.py --output /tmp/lra05-builds
```

The third compiles both modes with dummy credentials into isolated source
copies, changing only the qualified copy's config default. No private secrets
are read and nothing is flashed. Rollback is a manual-mode build; for exact
pre-LRA-05 source use reviewed base `2c52afd7b5609444641d02cd420bc252a1f494c7`
in an isolated checkout. Deployment and physical wiring need their own
authorization.

---

## Original migration record — October 27, 2026

Kept for provenance. Read the corrections above first.


Prepared October 27, 2026 by Codex `logger-wifi-piless`.
Current copying session: `01a17526-034c-78f1-9d09-24c3b88c3dc7`.
Bookmark: `codex resume 01a17526-034c-78f1-9d09-24c3b88c3dc7`.
A successor must use its own verified session ID; retain this one as history.

This copy is bounded to Pico W logger firmware, native tests and build tooling.
Receiver/server migration is deferred. *(Corrected above: `logger/server/` now
exists.)* The copied source is v0.8.1-dev from
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
