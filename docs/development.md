# Developing allox

## Local setup

```bash
uv python install 3.13
uv sync
uv run python -m unittest discover -s tests -v
```

The repository pins Python 3.13 in `.python-version`, so `uv sync` will create or update `.venv` with the managed interpreter automatically.

## Common commands

```bash
uv run allox doctor
uv run allox self-test
uv build
```

## Dependency and interpreter changes

- Use `uv add`, `uv remove`, and `uv lock` when project dependencies change.
- Commit `.python-version` and `uv.lock` whenever you intentionally change the managed Python version or dependency resolution.

## Suggested workflow

1. Add or update tests for non-trivial logic first.
2. Implement the smallest working vertical slice.
3. Run unit tests and `uv run allox self-test`.
4. Keep docs and instruction files in sync with behavior changes.

## Binary-resolution testing

Keep coverage around non-interactive binary discovery. In particular, preserve tests for:

- env-var overrides,
- `nvm`-style fallback discovery,
- wrapper binaries that require sibling runtimes like `node`,
- project-only behavior with no dependency on `~/.allox/`.
