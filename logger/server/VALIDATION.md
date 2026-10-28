# Public server extraction validation — October 28, 2026

Codex `pcb-manager`, session `01a17045-1855-7af2-b76a-32c2b778cd64`.
Bookmark: `codex resume 01a17045-1855-7af2-b76a-32c2b778cd64`.

- Seven host modules and two canonical conversion tools preserve their source
  bytes. Source paths and hashes are in `SOURCE_MANIFEST.json`.
- Synthetic Wi-Fi contract tests pass: authenticated completion, retry/restart,
  seals, final-trip publication, torn tails, clock-conflict holds, immutable
  identities, append/seal races and retry of failed durability barriers.
- Synthetic loopback HTTP uploads produce the same trip measurements and IDs
  as direct card replay. Repeat processing emits no duplicate packets.
- Standalone startup rejects missing credentials, repository-local state and
  database configuration. A temporary service reports database loading off
  and terminates cleanly.
- The supplied systemd unit passes `systemd-analyze verify`.
- Public candidate files and existing Git-history blobs were scanned for
  known private deployment credentials and common private-key/token signatures;
  none were found. Configuration is placeholder-only; no private recording,
  database, configured binary or runtime state was imported. This is a bounded
  review, not a guarantee against every possible secret representation.
- No firmware was changed or flashed. No deployed receiver, scheduler,
  database or dashboard was changed. No live vehicle test was performed.

The existing firmware native tests passed during the preceding repository
review. Real-drive regression fixtures remain private; the public synthetic
suite is not a replacement for every historical hardware/drive validation.
