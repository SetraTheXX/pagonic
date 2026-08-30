# Package Surface Audit

This document records the historical `0.4.0` package-surface snapshot. The
current release audit is in [0.5.0 Release Audit](release-audit-0.5.md).

This document records the package-surface review for the historical `0.4.0`
baseline. It is an audit record, not a package publication announcement.

## Scope and decision

- Audited source state: commit `b0e5cdf4a58d165484db8d7ed3328fd7504f5188`
  (`main`).
- Artifacts reviewed: `pagonic-0.4.0-py3-none-any.whl` and
  `pagonic-0.4.0.tar.gz`.
- Audit date: 2026-08-30.
- Publication decision: **do not publish this `0.4.0` artifact to PyPI or
  TestPyPI**.

The existing `v0.4.0` GitHub release points to an earlier release commit. The
audited commit contains later documentation and CI-integration work while the
package metadata still says `0.4.0`. Rebuilding and uploading it under the
existing version would make the version/tag relationship ambiguous. No PyPI or
TestPyPI upload command was run.

## Artifact contents

The artifacts were built from a clean exported source state with
`python -m build` and inspected with standard-library archive readers.

### Wheel

The wheel contained 51 members:

- `Pagonic/` runtime package files.
- `pagonic-0.4.0.dist-info/` metadata, license, and recording files.
- Both declared console scripts: `pagonic` and `pagonic-gui`.

The wheel contained no tests, documentation, examples, demo assets, generated
archives, private files, editor state, cache directories, or machine-local
path markers. This is the expected runtime installation surface.

### Source distribution

The sdist contained 91 members:

- Runtime package files, `README.md`, and `LICENSE`.
- The root-level pytest files that setuptools currently includes in an sdist.
- Normal generated `pagonic.egg-info` source metadata.

The sdist contained no private files, secrets, editor state, cache directories,
generated archives, or machine-local path markers. It does not include the
public `docs/`, `examples/`, or `assets/` directories, nor the nested security
fixture directories. Tests are intentionally excluded from the wheel, while
the current source-distribution behavior may include root tests. If a future
release needs an sdist that reproduces the complete contributor test/document
surface, it should add an explicit manifest policy as a separate packaging
change. This is recorded as follow-up, not as a blocker for the current
no-publish decision.

## Metadata and entry points

The built metadata was checked for both artifacts.

| Field | Audited value |
| --- | --- |
| Distribution name | `pagonic` |
| Import package | `Pagonic` (kept for compatibility) |
| Version | `0.4.0` |
| Python requirement | `>=3.10` |
| License | MIT, with the license file included |
| Base dependencies | `click>=8.1.7`, `rich>=13.7.0` |
| Optional GUI dependency | `PyQt6>=6.6.0` under the `gui` extra only |
| Optional performance dependencies | `numpy` and `psutil` under `performance` |
| Console scripts | `pagonic`, `pagonic-gui` |
| Release classification | Alpha |

The base installation does not require PyQt6. In clean base environments,
`pagonic-gui` was present as a declared entry point and returned a clear
install message with a non-zero exit code. This preserves CLI-only installation
while keeping the GUI explicitly optional.

## Clean-environment verification

Wheel and sdist installations were tested in separate fresh Python 3.13
virtual environments. For both installation paths:

- Installation completed with the declared runtime dependencies.
- `python -m pip check` returned `No broken requirements found.`
- `pagonic --version` reported `Pagonic, version 0.4.0`.
- `pagonic inspect --help`, `pagonic verify --help`, and
  `pagonic safe-extract --help` completed successfully.
- The package imported as `Pagonic` and reported version `0.4.0`.

These checks validate installation and command registration. They do not make a
production-readiness claim.

## Version and tag policy

The current `v0.4.0` tag remains attached to its existing release commit and
must not be moved. A future package release should follow this sequence:

1. Complete the intended milestone work and release gates.
2. Bump the package metadata and runtime version to the selected release, for
   example `0.5.0`.
3. Build and inspect fresh wheel and sdist artifacts from the release commit.
4. Create the matching immutable tag, for example `v0.5.0`, on that same
   commit.
5. Choose the package target explicitly. If publication is authorized later,
   TestPyPI is the safer first alpha checkpoint before considering PyPI.

The version, tag, artifact, and package target must agree before any upload.
Publication remains a separate, explicitly authorized action.

## Follow-up when publication is reconsidered

- Re-run this audit after the version bump; these file counts are a snapshot,
  not a permanent package contract.
- Decide whether an explicit sdist manifest should include the complete test,
  documentation, example, and demo-asset surface.
- Verify how the README demo GIF renders on the selected package index before
  announcing a published package.
