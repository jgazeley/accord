# Reusable task packet and successor handoff

Prepared October 28, 2026 by Codex `pcb-manager`, session `01a17045-1855-7af2-b76a-32c2b778cd64`. Historical bookmark: `codex resume 01a17045-1855-7af2-b76a-32c2b778cd64`. Successors use their own identities.

Copy this format into a task packet under `coordination/handoffs/` when needed.
Task IDs and state remain in the single tracker. A fresh model should need this
packet, 2–4 targeted references and the actual source, not a transcript replay.

```text
Task ID / title / parent milestone:
Specific objective and completion boundary:
Responsible role; current claimant/tool/session or unclaimed:
Reviewer/integration owner:
Repository, base revision, task branch, owned paths:
Minimum context (2–4 exact documents/sections):
Inputs provided and accepted/pending prerequisites:
Environment available (remote/no bench, local test hardware, etc.):
Expected deliverables and destination paths:
Acceptance: check -> expected outcome -> evidence artifact:
Authorized actions / explicitly unauthorized actions:
Dependencies, blocker and next action:
Optional deeper provenance: commits and predecessor bookmarks:
Required attribution block:

Completion and successor section:
Result and reviewer disposition (candidate is not accepted/deployed):
Delivered commits, branch, pushed/local-only status:
Tests performed with conditions; tests not run:
Deployment status; remaining risks and owner participation required:
Uncommitted owned work and preservation instructions:
Next bounded action, exact entry point and revision:
```

Publish only reviewed public-safe task material. For remote workers include
pushed revision/path references; do not depend on machine-specific paths or
private data that was not supplied. A missing artifact is a bounded input request,
not justification to recreate an entire predecessor investigation.

Use role-based ownership. A session ID identifies contribution/history, not a
permanent agent assignment. Browser reviews return assumptions, source references,
findings, options and proposed tests; local agents review before implementation.
The task packet does not authorize flashing, changing live services/DB state,
purchases, fabrication or vehicle wiring unless the owner explicitly grants it.

> **Required agent attribution:** Follow `logger/coordination/AGENT_ATTRIBUTION.md` relative to this repository root. Use your own tool, role and verified current session ID for Git author and committer (`<Tool> <role> [<short-id>]`), using per-command settings. End commits with `Agent-Session: <role>` and your full tool-specific session-ID trailer (`Codex-Session-ID`, `Claude-Session-ID` or `Antigravity-Session-ID`). This includes documentation-only work. Identify yourself and your resume command in coordination documents and dated updates. Preserve predecessor identity and original attribution when transporting commits. If an ID is unavailable, state that explicitly; never invent or borrow one. Include this requirement in subsequent seeds and handoffs.
