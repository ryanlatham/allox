# Install allox

## Prerequisites

- Python 3.9 or newer
- `git`
- `codex`
- `claude`
- `gemini` if you want the full hidden-reviewer workflow

## Install methods

Use one of:

```bash
pipx install <git-url>
uv tool install <git-url>
python3 -m pip install -e .
```

Then verify the machine:

```bash
allox doctor
allox doctor --online
```

## Non-interactive CLI discovery

Some standard installs, especially Node-based CLIs installed through `nvm`, work in interactive shells but are not visible to non-interactive subprocesses by default.

`allox` handles this in two ways:

- `allox doctor` auto-discovers common install locations such as `~/.nvm/versions/node/*/bin/gemini`
- `allox` prepends discovered runtime directories for child commands automatically, without modifying user-level instruction files

If you prefer explicit overrides, you can still set `ALLOX_CODEX_BIN`, `ALLOX_CLAUDE_BIN`, or `ALLOX_GEMINI_BIN`.

`allox doctor --online` performs provider-aware readiness checks:

- Codex: `codex login status`
- Claude: `claude auth status --json`
- Gemini: a small best-effort headless probe using the resolved CLI
