# allox Framework Instructions

This repository builds and maintains the `allox` framework itself.

## Working agreement

- Prefer Python and the standard library unless a small dependency earns its keep.
- Keep the installed `allox` CLI as the source of truth; generated projects should only contain thin shims and repo-local workflow assets.
- Write tests first for non-trivial framework logic, especially templating, markers, manifests, upgrades, redaction, and review normalization.
- Keep upgrade behavior explicit and safe. Managed files may update, project-owned files do not.
- Favor portability, transparent files, and predictable CLI output over cleverness.

## Collaboration defaults

- Start in planning mode for substantial work.
- Make strong defaults when the repository or generated project is underspecified.
- Keep docs and instruction files current when behavior changes.
