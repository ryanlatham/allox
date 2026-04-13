# Publishing allox

`allox` uses `uv` for release checks, package builds, and PyPI uploads.

## Local release checks

Before any release, update the version in `pyproject.toml`, `src/allox/version.py`, and the template `bundle_version` in `src/allox/assets/project_template/default/manifest.json`, then run:

```bash
uv sync
uv run python -m unittest discover -s tests -v
uv run allox self-test
uv build
uv run --isolated --no-project --with dist/*.whl -- allox self-test
uv run --isolated --no-project --with dist/*.tar.gz -- allox self-test
```

This verifies the working tree, the built wheel, and the built source distribution.

## Manual PyPI publishing with uv

Keep this as a bootstrap or emergency fallback path.

Set your token in `UV_PUBLISH_TOKEN`, then publish with:

```bash
uv publish --check-url https://pypi.org/simple
```

`uv publish` defaults to uploading `dist/*` to PyPI, and `--check-url` makes retries safer if a release partially uploads.

## GitHub Trusted Publishing

Trusted Publishing is the preferred release path for this repository. The workflow lives at [release.yml](/Users/ryan/Development/allox/.github/workflows/release.yml:1) and publishes only from Git tags that start with `v`.

### One-time GitHub setup

1. In GitHub, open `ryanlatham/allox` and create the environment `pypi` under Settings, Environments.
2. Optionally add required reviewers to that environment if you want a manual approval gate before publish.
3. Add tag protection for `v*` so only trusted maintainers can create release tags.

### One-time PyPI setup

In the PyPI project settings for `allox`, add a Trusted Publisher with these values:

- Publisher: GitHub Actions
- Owner: `ryanlatham`
- Repository name: `allox`
- Workflow name: `release.yml`
- Environment name: `pypi`

The workflow uses the `pypi` GitHub environment, so the environment name in PyPI must match exactly.

### Release flow after setup

1. Land the release commit on `main`.
2. Create and push a version tag that matches `pyproject.toml` exactly. This tag push is the normal release trigger for this repository:

```bash
git tag -a v0.1.1 -m v0.1.1
git push origin v0.1.1
```

3. GitHub Actions will:

- sync the project with `uv`
- verify the tag version matches `pyproject.toml`
- run the unit suite
- run `allox self-test`
- build the wheel and sdist
- smoke-test both artifacts in isolated environments
- publish to PyPI with `uv publish --trusted-publishing always`

### Verify the release

Confirm the GitHub Actions workflow succeeded, then verify the published package:

```bash
uv tool install --force allox
allox version
```

Do not reuse a version number or retag a changed release artifact. PyPI treats uploaded files as immutable, so any content change requires a new version.
