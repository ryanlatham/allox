# {{ project_name }} Agent Contract

<!-- allox:begin managed -->
## Managed Framework Contract

- This repository uses the `allox` framework (`{{ framework_version }}`) and treats Codex as the only visible implementation runtime.
- Work from the developer's normal request flow. Do not require a dedicated kickoff prompt file.
- Stay in plan-first mode for substantial work, then implement milestone by milestone.
- Use the `allox project ...` commands for task bootstrapping, review gates, closeout, and cleanup. The project shims in `scripts/ai/` are thin wrappers around the same runtime.
- Run the plan gate before implementation, the milestone gate after non-trivial milestones, and the closeout command as the final gate before task completion.
- Background reviewer and planning lanes are managed behind the scenes. They should not directly edit this worktree.
- Keep durable task state in `ai/tasks/`, `ai/plans/`, `ai/progress/`, `ai/packets/`, `ai/reviews/`, and `ai/archive/`.
- Build deterministic checks before reviewer gates where practical, and fail hard if required reviewer lanes are unavailable.
- Preserve project-owned files such as `ai/config/project_commands.json` and `ai/config/review_redactions.json`.
<!-- allox:end managed -->

## User Notes

Add project-specific guidance, product constraints, and style preferences below this heading. This section is preserved across `allox upgrade`.
