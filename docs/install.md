# Install allox

## Prerequisites

- `uv`
- `git`
- `codex`
- `claude`
- `gemini` if you want the full hidden-reviewer workflow

`uv` will provision the pinned Python 3.13 interpreter for this repo when needed.

## Install methods

From PyPI after the first release:

```bash
uv tool install allox
```

From Git before the first release:

```bash
uv tool install git+https://github.com/ryanlatham/allox
```

For local development from a checkout, prefer:

```bash
uv sync
uv run allox doctor
```

Then verify the machine:

From a local checkout:

```bash
uv run allox doctor
uv run allox doctor --online
```

From an installed tool:

```bash
allox doctor
allox doctor --online
```

## Non-interactive CLI discovery

Some standard installs, especially Node-based CLIs installed through `nvm`, work in interactive shells but are not visible to non-interactive subprocesses by default.

`allox` handles this in two ways:

- `allox doctor` auto-discovers common install locations such as `~/.nvm/versions/node/*/bin/gemini`
- `allox` prepends discovered runtime directories for child commands automatically, without modifying user-level instruction files
- the default project template marks built-in reviewer lanes as `enabled: "auto"` so gate execution follows `allox` discovery instead of plain shell `PATH` checks

If you prefer explicit overrides, you can still set `ALLOX_CODEX_BIN`, `ALLOX_CLAUDE_BIN`, or `ALLOX_GEMINI_BIN`.

`allox doctor --online` performs provider-aware readiness checks:

- Codex: `codex login status`
- Claude: `claude auth status --json`
- Gemini: a small best-effort headless probe using the resolved CLI
