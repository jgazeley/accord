# Agent attribution — required from October 26, 2026

Maintainer: Codex `pcb-manager`
Session: `01a17045-1855-7af2-b76a-32c2b778cd64`
Bookmark: `codex resume 01a17045-1855-7af2-b76a-32c2b778cd64`

The owner requested attribution for every agent working on Accord code or
coordination documents, including the manager, locally and remotely. Follow the
logger agent's example in `e3eb69d`: an identifiable Git author and committer,
plus the role and full session ID in the commit message. These are commit
metadata, not Git release tags. Apply prospectively; do not rewrite published
history to retrofit attribution.

## Commit convention

- Author and committer name: `<Tool> <role> [<first eight session-ID characters>]`.
  Use a stable role such as `pcb-manager`, `logger-wifi-piless`, `fuel`,
  `bridge`, `db-dashboard`, `proximity` or `logger-power`.
- Agent email: `<tool>@local.invalid`, for example `codex@local.invalid`.
- Commit trailers: `Agent-Session: <role>` and the tool-specific full ID:
  `Codex-Session-ID: <id>`, `Claude-Session-ID: <id>` or
  `Antigravity-Session-ID: <id>`. Keep trailers together at the end of the body.
- Use the actual current session ID, verified from session metadata or the
  owner-provided bookmark. If unavailable, state `unavailable` explicitly and
  retain the role/tool identity; never guess or borrow another session's ID.
- Use per-command identity settings. Do not change shared repository or global
  Git identity: concurrent agents can use the same checkout.
- When cherry-picking or rebasing another agent's work, preserve its original
  author and attribution trailers; identify yourself as committer. Attribute
  substantive additional work explicitly in the body. Do not claim authorship
  merely for transporting a commit.

Example for this manager (other sessions must substitute their own identity):

```sh
git -c user.name='Codex pcb-manager [01a17045]' \
    -c user.email='codex@local.invalid' \
    commit -F /tmp/accord-commit-message.txt
```

Example message file:

```text
coordination: describe the concrete change

Explain the result and relevant verification.

Agent-Session: pcb-manager
Codex-Session-ID: 01a17045-1855-7af2-b76a-32c2b778cd64
```

Check `git show -s --format=fuller HEAD` before pushing; inherited author or
committer environment overrides must not silently attribute work to the owner
or another agent. Use `git log --format=fuller` to inspect attribution and
`git log --all --grep='Codex-Session-ID: <full-id>'` to find a session's commits.

## Documents and handoffs

New coordination documents must identify their authoring tool, role, full
session ID and resume command near the top. When updating an existing record,
preserve its original attribution and identify the new contributor in the
dated update. Keep current and predecessor bookmarks distinct.

The manager must include the following block in every future or refreshed
project seed, task prompt and handoff, even when the recipient is remote or
working outside this checkout. Include this convention with seeds for other
repositories if the linked file will not be available there.

### Reusable prompt block

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

Attribution does not expand artifact ownership or authorize deployment,
database writes or external messages.
