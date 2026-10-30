# Agent instructions

This repository (`jgazeley/accord`) holds two Pico W modules for the owner's
Honda Accord, plus the logger's server side:

- `keyless/`: the keyless board (firmware, native tests, KiCad). In service in
  the car. **It is the template for logger hardware.**
- `logger/`: recording/upload firmware, native tests, build tooling, the
  `server/` raw receiver and trip converter, and `hardware/` for the Rev A
  board.

The two modules are separate: keyless does not talk to the logger's VM bridge.
The Pi 4 is a portable bench, not part of normal ingestion.

## How work is done here (owner direction, October 29, 2026)

**One agent works directly with the owner and commits to git.** The earlier
multi-agent arrangement (manager and specialist sessions, task packets,
reviews, claims and handoffs) is retired. Its records stay in `coordination/`
as history; do not restart it.

1. **Read [coordination/STATUS.md](coordination/STATUS.md) first.** It says
   where things stand and what's next. Rewrite it when that changes; don't
   append to it.
2. **Record owner statements the moment they are made** in
   [coordination/DECISIONS.md](coordination/DECISIONS.md): dated, quoted
   where possible, before carrying on. Lost owner statements caused most
   past rework.
3. **The owner is the authority on what is physically built and run.**
   Firmware comments and older documents can be stale. If something matters
   and isn't recorded, ask.
4. **Keyless is the default template** for every logger block (buck,
   protection, car inputs, RS-485, connectors) unless the owner or a
   concrete logger-specific difference says otherwise (DECISIONS: D-REUSE-02).
5. Check engineering against the physical fact (net, pin, part, polarity),
   not against a symbolic record that might share your misreading.

## Git

- Keep the shared checkout `/srv/agent_share/accord` on `main`. Use a
  separate worktree for branch work.
- Commit identity per command, never by changing global config:
  `git -c user.name='<Tool> <role> [<short-session-id>]' -c user.email='<tool>@local.invalid' commit …`.
  End the message with your tool's session-ID trailer (`Claude-Session-ID:`,
  `Codex-Session-ID:`), plus any trailer your tool requires.
  This replaces `logger/coordination/AGENT_ATTRIBUTION.md`, which is kept
  unchanged because the logger import manifest pins its hash.
- Push needs the explicit key (no agent or SSH config on this host):
  `git -c core.sshCommand='ssh -i ~/.ssh/id_ed25519_accord_public -o IdentitiesOnly=yes' push git@github.com:jgazeley/accord.git main:main`.
  Ask the owner before pushing.
- Inspect exactly what is staged before every commit. **Never commit**
  credentials, `secrets.h`, configured firmware binaries, private runtime
  data, or `keyless/hardware/3d/039301160.stp` (excluded pending licence
  provenance).

## Safety boundaries

Publishing source does not authorize flashing, deployment, service changes,
database writes, purchases, wiring or bench work. Each of those needs the
owner's go-ahead at the time. To flash a Pico, use `pico-flash` (see the
owner's global instructions), never bare `picotool load`.

## Configuration and licensing

- A configured logger build needs an independent private `secrets.h`; see
  [logger/NEXT_AGENT.md](logger/NEXT_AGENT.md). The build helper uses dummy
  credentials unless `--secrets` is given.
- Before collecting or adapting server files, read
  [docs/SERVER_MIGRATION_NOTES.md](docs/SERVER_MIGRATION_NOTES.md). The public
  server stops at raw storage and trip JSON.
- Original software and docs are Apache 2.0 and original hardware is
  CERN-OHL-P-2.0; preserve notices and third-party terms
  ([LICENSING.md](LICENSING.md)).

## Provenance

`jgazeley/accord-logger` is the historical repository: reference only, not a
tracker. Each component's `SOURCE_MANIFEST.json` records source revisions and
hashes; don't edit files a manifest pins. Path history is in
[coordination/MIGRATION_MAP.md](coordination/MIGRATION_MAP.md).

| Historical name | Meaning here |
|---|---|
| `hondaPico` | Usually the keyless board. `hondaPico/hondaPico.ino` was a Wi-Fi dashboard sketch, not keyless firmware |
| `benchlink/uart_main/` | Keyless firmware, now `keyless/firmware/accord-keyless/` |
| `hondaPico-kicad/` | Keyless hardware, now `keyless/hardware/`; keep `hondaPico.kicad_pro` as its filename |
| `picow-logger` | Logger firmware, now `logger/firmware/accord-logger/` |
| `bridge`, `accord-bridge` | Logger upload/processing service, not keyless |

Do not globally rename `hondaPico` in code, protocol identifiers or KiCad
references. Keyless host tooling (`hp`, `cm5sim`) lives outside this repo at
`/srv/agent_share/pcb/benchlink/`.
