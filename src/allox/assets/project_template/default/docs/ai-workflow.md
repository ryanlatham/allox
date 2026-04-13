# AI Workflow For {{ project_name }}

This project uses `allox` to keep Codex as the only visible runtime while still enabling hidden reviewer lanes.

## Workflow

1. Read `AGENTS.md`.
2. Bootstrap a task with `python3 scripts/ai/bootstrap_task.py --title "<task title>"`.
3. Draft the task plan, then run the plan gate before implementation.
4. Implement milestone by milestone.
5. After each non-trivial milestone, run deterministic checks and then `python3 scripts/ai/milestone_gate.py`.
6. Before declaring the task done, run `python3 scripts/ai/closeout.py` so the final gate writes durable artifacts and cleans temporary files.

## Important files

- `ai/config/project_commands.json`: project-specific check and reviewer command config.
- `ai/config/review_redactions.json`: file exclusion and redaction rules for packets.
- `ai/tasks/`, `ai/plans/`, `ai/progress/`: durable task artifacts.
- `ai/packets/`, `ai/reviews/`: generated review packets, check transcripts, raw reviewer outputs, and normalized findings.
- `ai/archive/`: durable closeout and adjudication artifacts for completed tasks.
