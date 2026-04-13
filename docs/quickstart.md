# Quickstart

```bash
allox doctor
allox doctor --online
allox new my-project --dry-run
allox new my-project --init-git
cd my-project
```

If you are already inside the target folder, `allox new` uses the current working directory by default.

Then:

1. Open the generated project in Codex.
2. Read `AGENTS.md` and `docs/ai-workflow.md`.
3. Paste your product idea or spec using `PROMPTS/CODEX_PROJECT_START.md` as the starting shape.
4. Bootstrap the first task with `python3 scripts/ai/bootstrap_task.py --title "<task title>"`.
5. Draft the plan, run the plan gate, and wait for plan approval before implementation.
6. After each non-trivial milestone, run `python3 scripts/ai/milestone_gate.py`.
7. Before calling the task complete, run `python3 scripts/ai/closeout.py`.
