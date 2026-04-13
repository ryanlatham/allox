# allox

`allox` bootstraps and maintains Codex-led repositories without turning every project into a pile of copied workflow glue.

It keeps Codex as the normal development surface, moves orchestration into the installed CLI, and gives generated repos a durable, inspectable contract for planning, milestone review, and closeout.

## Why allox

- Keep the day-to-day workflow simple. Developers work in Codex from their normal task, issue, or spec instead of learning a custom repo-local prompt maze.
- Add hidden reviewer lanes without handing your main worktree to multiple tools. Codex stays the visible writer while Claude and Gemini can act as structured background critics.
- Keep repos lightweight and upgradeable. The installed `allox` CLI owns runtime behavior, while generated projects keep thin shims, prompts, config, and durable state.
- Preserve evidence. Review packets, raw reviewer output, normalized findings, checks, and closeout artifacts are stored in the repo under `.allox/state/`.
- Stay repo-scoped. `allox` sets up project-local instructions and workflow files without mutating machine-wide instruction files.

## Install

`allox` requires Python 3.13+.

Install from PyPI:

```bash
uv tool install allox
```

Install the latest version directly from GitHub:

```bash
uv tool install git+https://github.com/ryanlatham/allox
```

For local development from a checkout:

```bash
uv sync
uv run allox --help
```

## Quick start

If you installed `allox` as a tool, run `allox ...`. If you are working from a local checkout, prefix commands with `uv run`.

```bash
allox doctor
allox doctor --online
allox new my-project --init-git
cd my-project
```

You can also run `allox new --dry-run` to preview the scaffold, or run `allox new` with no path to initialize the current working directory.

Then open the generated project in Codex and work normally from your task, issue, or product spec.

The generated project contract lets Codex handle task bootstrap and the managed `allox` workflow behind the scenes.

## What You Get

A generated project includes:

- `AGENTS.md` as the shared repo contract.
- `allox/` as the visible workflow surface for prompts, schemas, templates, and project-owned config.
- `.allox/` as hidden runtime state for packets, reviews, archive artifacts, and thin wrapper scripts.
- Built-in reviewer lane wiring for Codex, Claude, and Gemini, with local provider detection handled by `allox doctor` and runtime resolution.
- An upgrade-safe manifest so framework-managed files can evolve without trampling project-owned files.

In practice, that means you can standardize planning and review behavior across repos without copying orchestration code into each one.

## Commands

- `allox new [path]` bootstraps a new project from the default template and aborts before writing if it detects file or folder conflicts. If `path` is omitted, it uses the current working directory.
- `allox new [path] --dry-run` previews the planned create and append actions without writing anything.
- `allox doctor` checks local prerequisites and project health.
- `allox doctor --online` checks provider-authenticated readiness for Codex plus the managed background reviewers.
- `allox upgrade [path]` safely updates managed framework files.
- `allox self-test` renders a temp project and validates the scaffold.

Generated projects also use internal `allox project ...` commands for task bootstrap, plan review, milestone review, closeout, and cleanup. Those commands are normally driven by the generated project contract rather than by humans directly.

## Runtime discovery notes

`allox` supports `ALLOX_CODEX_BIN`, `ALLOX_CLAUDE_BIN`, and `ALLOX_GEMINI_BIN`, and it also auto-discovers common user installs such as `~/.nvm/versions/node/*/bin/gemini`.

If a wrapper binary lives outside the current non-interactive `PATH`, `allox` will prepend the discovered parent directory for child commands automatically.

The default project template wires built-in Claude and Gemini reviewer lanes with `enabled: "auto"`, so reviewer gates follow `allox`'s resolver instead of relying on raw shell `PATH` checks.

`allox` is project-scoped and does not write user-level instruction files.

## Learn More

See [docs/install.md](/Users/ryan/Development/allox/docs/install.md), [docs/development.md](/Users/ryan/Development/allox/docs/development.md), [docs/publishing.md](/Users/ryan/Development/allox/docs/publishing.md), [docs/quickstart.md](/Users/ryan/Development/allox/docs/quickstart.md), and [docs/architecture.md](/Users/ryan/Development/allox/docs/architecture.md) for more detail.
