# allox

`allox` is a reusable framework product for bootstrapping and maintaining Codex-led development repositories where Codex is the only visible runtime and Claude/Gemini act as hidden reviewer lanes.

## Install

```bash
pipx install <git-url>
```

Or for local development:

```bash
python3 -m pip install -e .
```

## Quick start

```bash
allox doctor
allox doctor --online
allox new my-project --init-git
cd my-project
```

Then open the generated project in Codex and start with [PROMPTS/CODEX_PROJECT_START.md](/Users/ryan/Development/allox/src/allox/assets/project_template/default/PROMPTS/CODEX_PROJECT_START.md).

## Commands

- `allox new <path>` bootstraps a new project from the default template and aborts before writing if it detects file or folder conflicts.
- `allox new <path> --dry-run` previews the planned create and append actions without writing anything.
- `allox doctor` checks local prerequisites and project health.
- `allox doctor --online` checks provider-authenticated readiness for Codex, Claude, and Gemini.
- `allox upgrade [path]` safely updates managed framework files.
- `allox self-test` renders a temp project and validates the scaffold.

## Runtime discovery notes

`allox` supports `ALLOX_CODEX_BIN`, `ALLOX_CLAUDE_BIN`, and `ALLOX_GEMINI_BIN`, and it also auto-discovers common user installs such as `~/.nvm/versions/node/*/bin/gemini`.

If a wrapper binary lives outside the current non-interactive `PATH`, `allox` will prepend the discovered parent directory for child commands automatically. `allox` is project-scoped and does not write user-level instruction files.

See [docs/quickstart.md](/Users/ryan/Development/allox/docs/quickstart.md) and [docs/architecture.md](/Users/ryan/Development/allox/docs/architecture.md) for more detail.
