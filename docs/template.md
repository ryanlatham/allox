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

## Workflow state under `ai/`

- `ai/config/project_commands.json`
  Project-owned command wiring for deterministic checks and reviewer commands. New projects get gate-specific placeholders for `plan_gate`, `milestone_gate`, and `final_gate`.
- `ai/config/review_redactions.json`
  Project-owned packet exclusion and redaction rules.
- `ai/prompts/*.md`
  Prompt templates used by the runtime when invoking reviewer lanes. `managed`.
- `ai/schemas/*.json`
  Shared normalized output shapes for reviewer findings. `managed`.
- `ai/templates/TASK.md`, `PLAN.md`, `PROGRESS.md`
  Durable task-state templates used by `bootstrap-task`. `managed`.
- `ai/templates/ADJUDICATION.md`, `CLOSEOUT.md`
  Durable closeout artifacts rendered by `allox project closeout`. `managed`.
- `ai/tasks/`, `ai/plans/`, `ai/progress/`
  Durable task records created per task.
- `ai/packets/`
  Generated plan, milestone, and final review packets.
- `ai/reviews/`
  Check transcripts, raw reviewer output, normalized findings, and skip notes.
- `ai/archive/`
  Final closeout and adjudication artifacts for completed tasks.
- `ai/tmp/`
  Temporary prompt files and worktree metadata. Cleaned during closeout and manual cleanup.

## Kickoff And Runtime Entry Points

- `PROMPTS/CODEX_PROJECT_START.md`
  Human-readable kickoff prompt for starting a new product build in Codex. It tells Codex how to enter the managed workflow. `managed`.
- `scripts/ai/*.py`
  Thin Python shims for the internal workflow that call the installed `allox project ...` commands. They are convenience wrappers, not the canonical onboarding path. `managed`.

## Framework metadata

- `.allox/manifest.json`
  Tracks the framework version, template version, and managed-file fingerprints used for safe upgrades.
