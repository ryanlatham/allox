# Publishing allox

`allox` uses `uv` for release checks, package builds, and PyPI uploads.

## Prepare a release

1. Update the version in `pyproject.toml` and `src/allox/version.py`.
2. Run `uv lock` if you changed the Python requirement or dependencies.
3. Run the local checks:

```bash
uv sync
uv run python -m unittest discover -s tests -v
uv run allox self-test
```

## Build distributions

```bash
uv build
```

This writes the source distribution and wheel to `dist/`.

## Publish to PyPI

For the very first release of a new project name, create a PyPI account and use an account-scoped token. After the project exists on PyPI, you can switch to a project-scoped token until Trusted Publishing is configured.

Set your token in `UV_PUBLISH_TOKEN`, then publish with:

```bash
uv publish --check-url https://pypi.org/simple
```

`uv publish` defaults to uploading `dist/*` to PyPI, and `--check-url` makes retries safer if a release partially uploads.

## Verify the release

Confirm the project page on PyPI, then verify installability:

```bash
uv tool install --force allox
allox version
```
