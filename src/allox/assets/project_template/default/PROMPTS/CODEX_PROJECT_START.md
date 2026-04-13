# Start Prompt For {{ project_name }}

Read `AGENTS.md` and `docs/ai-workflow.md` first.

Then:

1. Stay in planning mode first.
2. Bootstrap task artifacts with `python3 scripts/ai/bootstrap_task.py --title "<short task title>"`.
3. Turn the product idea or spec into a milestone plan and run the plan gate before implementation.
4. Wait for plan approval before implementation.
5. After each non-trivial milestone, run the milestone gate workflow.
6. Before calling the task complete, run the final closeout gate with `python3 scripts/ai/closeout.py`.
