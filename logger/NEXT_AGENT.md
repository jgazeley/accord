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
