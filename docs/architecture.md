# Architecture

`allox` keeps orchestration in the installed CLI so generated repositories stay lightweight, upgradeable, and portable across machines.

## Why the CLI owns orchestration

- The installed `allox` package is the source of truth for bootstrap, doctor, upgrade, and task runtime behavior.
- Generated projects only contain thin Python shims, prompts, schemas, reviewer definitions, and durable task artifacts.
- This keeps upgrade logic centralized and avoids copying orchestration code into every generated repo.

## Managed project contract

- `allox` is repo-scoped, not machine-scoped. It does not install or mutate user-level instruction files.
- `AGENTS.md` is the canonical shared instruction file in generated projects.
- `CLAUDE.md` and `GEMINI.md` are thin wrappers that keep hidden reviewer lanes aligned with `AGENTS.md`.
- Managed files are tracked in `.allox/manifest.json`.
- Section-managed files use explicit markers so upgrades can preserve user-owned sections.
- Project-owned files such as `ai/config/project_commands.json` and `ai/config/review_redactions.json` are created once and then preserved.

## Three-gate workflow

- Plan gate:
  build a plan packet, invoke the hidden planning lanes, and normalize the critique before implementation begins.
- Milestone gate:
  run deterministic checks, build a review packet from task state plus repo changes, invoke hidden reviewer lanes, and normalize findings after each non-trivial milestone.
- Closeout:
  use `allox project closeout` as the final gate. It runs final deterministic checks, optionally runs final reviewers, writes adjudication and closeout artifacts, and cleans temporary state.

## Model roles

- Codex is the only visible runtime and the only writer in the main worktree.
- Claude lanes are biased toward semantic correctness, security, and test quality.
- Gemini lanes are biased toward architecture, regression risk, and performance or scalability.

## Runtime discovery

- Binary resolution is centralized so `allox` can honor `ALLOX_CODEX_BIN`, `ALLOX_CLAUDE_BIN`, and `ALLOX_GEMINI_BIN`.
- `allox` also supports fallback discovery for common installs like `~/.nvm/versions/node/*/bin/gemini`.
- When a wrapper binary is discovered outside the current non-interactive `PATH`, `allox` prepends the discovered runtime directory in memory for child commands.
