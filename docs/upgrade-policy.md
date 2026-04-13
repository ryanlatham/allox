# Upgrade Policy

## Bootstrap safety

- `allox new` does not overwrite existing repo files.
- Existing markdown files may be appended with managed allox sections.
- File or folder conflicts are detected before any framework artifacts are written.
- `allox new --dry-run` previews the planned bootstrap actions without writing files.

## Managed file types

- Fully managed: replaced when unchanged since the last framework write.
- Section-managed: only the managed block is updated.
- Project-owned: created once and never overwritten automatically.

## Conflict handling

- `allox upgrade` never silently overwrites local edits to framework-managed content.
- Conflicts are reported in CLI output.
- Proposed replacements are written to `.allox/conflicts/<path>.allox.new` by default.

## Version tracking

`.allox/manifest.json` records the framework version, template version, and managed-file fingerprints used for safe upgrades.
