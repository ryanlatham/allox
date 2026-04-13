# AI Workflow For {{ project_name }}

This project uses `allox` to keep Codex as the only visible runtime while still enabling hidden reviewer lanes.

This document is Codex-facing operational guidance, not a human quickstart.

## Workflow

1. Read `AGENTS.md`.
2. Bootstrap a task with `allox project bootstrap-task --project . --title "<task title>"`.
3. Draft the task plan, then run `allox project plan-gate --project .` before implementation.
4. Implement milestone by milestone.
5. After each non-trivial milestone, run deterministic checks and then `allox project milestone-gate --project .`.
6. Before declaring the task done, run `allox project closeout --project .` so the final gate writes durable artifacts and cleans temporary files.

The repo-local scripts under `scripts/ai/` are thin shims around the same `allox project ...` commands and may be used when the installed CLI is not directly reachable.

## Important files

- `ai/config/project_commands.json`: project-specific check and reviewer command config.
- `ai/config/review_redactions.json`: file exclusion and redaction rules for packets.
- `ai/tasks/`, `ai/plans/`, `ai/progress/`: durable task artifacts.
- `ai/packets/`, `ai/reviews/`: generated review packets, check transcripts, raw reviewer outputs, and normalized findings.
- `ai/archive/`: durable closeout and adjudication artifacts for completed tasks.
