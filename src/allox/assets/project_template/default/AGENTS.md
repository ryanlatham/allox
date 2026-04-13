# {{ project_name }} Agent Contract

<!-- allox:begin managed -->
## Managed Framework Contract

- This repository uses the `allox` framework (`{{ framework_version }}`) and treats Codex as the only visible implementation runtime.
- Work from the developer's normal request flow. Do not require a dedicated kickoff prompt file.
- Stay in plan-first mode for substantial work, then implement milestone by milestone.
- Use the `allox project ...` commands for task bootstrapping, review gates, closeout, and cleanup. Hidden project shims under `.allox/scripts/` wrap the same runtime when needed.
- Run the plan gate before implementation, the milestone gate after non-trivial milestones, and the closeout command as the final gate before task completion.
- Background reviewer and planning lanes are managed behind the scenes. They should not directly edit this worktree.
- Inspectable allox workflow files live under `allox/`. Durable task state lives under `.allox/state/`.
- Build deterministic checks before reviewer gates where practical, and fail hard if required reviewer lanes are unavailable.
- Use `allox doctor` and `allox doctor --online` to judge Codex, Claude, and Gemini availability. `allox` may resolve supported CLIs outside the current non-interactive `PATH`.
- Preserve project-owned files such as `allox/config/project_commands.json` and `allox/config/review_redactions.json`.
<!-- allox:end managed -->

## User Notes

Add project-specific guidance, product constraints, and style preferences below this heading. This section is preserved across `allox upgrade`.
