# Start Prompt For {{ project_name }}

Read `AGENTS.md` and `docs/ai-workflow.md` first. Treat them as the project contract for how this repository uses `allox`.

Then:

1. Stay in planning mode first.
2. Bootstrap task artifacts with `allox project bootstrap-task --project . --title "<short task title>"`.
3. Turn the product idea or spec into a milestone plan and run `allox project plan-gate --project .` before implementation.
4. Wait for plan approval before implementation.
5. After each non-trivial milestone, run deterministic checks and then `allox project milestone-gate --project .`.
6. Before calling the task complete, run `allox project closeout --project .`.

If the installed `allox` CLI is not directly available in this repo context, the managed shims under `scripts/ai/` mirror the same commands.
