# Template Layout

The default project template is designed so the generated repo is self-describing, while the heavy workflow logic stays in the installed `allox` package.

## Root instruction files

- `AGENTS.md`
  Canonical shared project instructions. `section` managed so framework guidance can update without overwriting the user notes section.
- `CLAUDE.md`
  Thin wrapper that points Claude back to `AGENTS.md`. `managed`.
- `GEMINI.md`
  Thin wrapper that points Gemini back to `AGENTS.md`. `managed`.

## Codex project config

- `.codex/config.toml`
  Minimal project-scoped Codex defaults. `section` managed.
- `.codex/README.md`
  Explains worktree and local-environment expectations for Codex App. `managed`.

## Hidden reviewer definitions

- `.claude/agents/*.md`
  Claude reviewer lane definitions for plan, code, security, and tests. `managed`.
- `.gemini/agents/*.md`
  Gemini reviewer lane definitions for plan, architecture, regression, and performance. `managed`.
- `.agents/skills/*/SKILL.md`
  Repo-local Codex skills that keep the workflow explicit and inspectable. `managed`.

## Visible allox contract under `allox/`

- `allox/README.md`
  Codex-facing operational guidance for the generated workflow. `managed`.
- `allox/config/project_commands.json`
  Project-owned command wiring for deterministic checks and reviewer commands. New projects get gate-specific placeholders for `plan_gate`, `milestone_gate`, and `final_gate`, with built-in Claude and Gemini lanes set to `enabled: "auto"`.
- `allox/config/review_redactions.json`
  Project-owned packet exclusion and redaction rules.
- `allox/prompts/*.md`
  Prompt templates used by the runtime when invoking reviewer lanes. `managed`.
- `allox/schemas/*.json`
  Shared normalized output shapes for reviewer findings. `managed`.
- `allox/templates/TASK.md`, `PLAN.md`, `PROGRESS.md`
  Durable task-state templates used by `bootstrap-task`. `managed`.
- `allox/templates/ADJUDICATION.md`, `CLOSEOUT.md`
  Durable closeout artifacts rendered by `allox project closeout`. `managed`.

## Hidden runtime state under `.allox/`

- `.allox/state/tasks/`, `.allox/state/plans/`, `.allox/state/progress/`
  Durable task records created per task.
- `.allox/state/packets/`
  Generated plan, milestone, and final review packets.
- `.allox/state/reviews/`
  Check transcripts, raw reviewer output, normalized findings, and skip notes.
- `.allox/state/archive/`
  Final closeout and adjudication artifacts for completed tasks.
- `.allox/state/tmp/`
  Temporary prompt files and worktree metadata. Cleaned during closeout and manual cleanup.

## Internal Runtime Entry Points

- No dedicated kickoff prompt file is required in generated projects. Codex should start from the developer's normal request flow using `AGENTS.md` and the repo-local Codex defaults.
- `.allox/scripts/*.py`
  Thin Python shims for the internal workflow that call the installed `allox project ...` commands. They are convenience wrappers, not the canonical onboarding path. `managed`.

## Framework metadata

- `.allox/manifest.json`
  Tracks the framework version, template version, and managed-file fingerprints used for safe upgrades.
