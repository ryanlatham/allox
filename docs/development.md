# Developing allox

## Local setup

```bash
python3 -m pip install -e .
python3 -m unittest discover -s tests -v
```

## Suggested workflow

1. Add or update tests for non-trivial logic first.
2. Implement the smallest working vertical slice.
3. Run unit tests and `allox self-test`.
4. Keep docs and instruction files in sync with behavior changes.

## Binary-resolution testing

Keep coverage around non-interactive binary discovery. In particular, preserve tests for:

- env-var overrides,
- `nvm`-style fallback discovery,
- wrapper binaries that require sibling runtimes like `node`,
- project-only behavior with no dependency on `~/.allox/`.
