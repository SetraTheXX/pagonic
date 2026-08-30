# Pagonic v0.5.0 Release Audit

This is the release-gate record for `v0.5.0`. It covers the source state that
is tagged and published as the GitHub release. The package target is GitHub
Release; no PyPI or TestPyPI upload is made.

## Release decision

- Version: `0.5.0`
- Tag: `v0.5.0`
- Distribution: `pagonic`
- Import package: `Pagonic`
- Classification: Alpha
- Package target: GitHub Release artifacts and source checkout
- PyPI/TestPyPI: not published

The release decision preserves the existing 0.4.0 tag and keeps the version,
tag, source state, and built artifacts aligned for the new release.

## Release gates

- [x] Normal local test suite passes.
- [x] Comprehensive local test suite passes.
- [x] Windows/Linux CI passes for Python 3.10 through 3.13.
- [x] Synthetic security corpus covers the documented high-impact rules and
      safe-extraction refusal boundaries.
- [x] JSON report keys, risk severities, ordering, and CLI exit codes are
      documented and regression-tested.
- [x] Wheel and source distribution contents are reviewed.
- [x] Clean-environment CLI smoke passes for inspect, verify, and safe
      extraction.
- [x] `pip check` passes in the supported installation path.
- [x] Public docs contain no unsupported speed, AI, production-ready, or
      archive-manager replacement claims.
- [x] The version, tag, release target, and package publication decision are
      explicit.

## Code, logic, and security audit

The release changes preserve the focused ownership boundaries:

- `ZipReader`, `ZipWriter`, `inspect_archive`, and the CLI policy layer own
  current behavior.
- `ZipHandler` remains a compatibility facade and delegates archive work to
  the focused APIs.
- Path traversal, POSIX and Windows absolute paths, mixed separators,
  normalized/case/Unicode collisions, symlink metadata, encrypted entries,
  unsupported methods, structure errors, and resource limits are covered by
  generated regression inputs.
- `safe-extract` remains fail-closed for validation errors and unsupported
  compression methods, and does not create its output directory when a gate
  refuses the archive.
- No new runtime dependency or optional-GUI requirement was introduced.

The review found no release-blocking bug or logic contradiction in the tested
surface. The project remains alpha software; untested external archive formats,
future security rules, and real-world downstream usage remain outside this
audit’s proof boundary.

## Verification evidence

- Release-preparation source commit: `8458fa2896b9def0c5e1eb238d528010a721efa8`.
- Final tagged release commit: `d2bb64b694e7f0ed3878e0ea34a3226b1c73f22d`.
- GitHub Actions validation for the final tagged commit: [run `33303740039`](https://github.com/SetraTheXX/pagonic/actions/runs/33303740039), all 8 Windows/Linux Python 3.10–3.13 jobs successful.
- `python -m pytest -q --cov=Pagonic --cov-report=term-missing`: **399 passed,
  8 skipped**; total measured coverage was 60% across the full package,
  including optional and historical compatibility modules.
- `python -m pytest -q --comprehensive`: **404 passed, 3 skipped**.
- `python -m compileall -q Pagonic`: passed.
- `python -m build`: produced the versioned wheel and source distribution
  listed below.
- Separate clean wheel and sdist virtual environments imported `Pagonic` as
  `0.5.0`, reported `Pagonic, version 0.5.0`, and passed `pip check`.
- Clean and traversal-containing synthetic archives passed the expected CLI
  smoke and fail-closed extraction checks in both environments. The optional
  GUI entry point returned its documented PyQt6 installation message when the
  GUI extra was absent.
- `vhs assets/pagonic-demo.tape` rendered the current README demo at 1180x620,
  25 fps, with a 28.16 second duration.

## Package and installation audit

Fresh wheel and source-distribution artifacts were built from the release
source state and inspected with standard-library archive readers. The wheel
contains only the runtime `Pagonic/` package and its distribution metadata. The
source distribution contains the public source, tests, README, license, and
normal build metadata. Repository documentation, examples, and the rendered
demo remain checkout/release assets rather than installed package contents;
private plans, local caches, generated archives, and editor state are excluded.

The explicit 0.5.0 artifacts reviewed were:

| Artifact | Members | Size | SHA-256 |
| --- | ---: | ---: | --- |
| `pagonic-0.5.0-py3-none-any.whl` | 51 | 115,197 bytes | `4b066c2757e004d3480aef96a8464c5dd10b1ef8468bb0c35a5556b391c39071` |
| `pagonic-0.5.0.tar.gz` | 93 | 129,183 bytes | `7f0d7878625a826e2b693fd232d07dd263a43403f144bb1692f17586bf0dfbc7` |

The metadata review confirmed the package name, version, Python `>=3.10`
requirement, MIT license, base `click`/`rich` dependencies, optional GUI and
performance extras, and both console entry points. Clean wheel and source
installation checks include `pagonic --version`, inspect/verify/safe-extract
help, representative CLI behavior, and `pip check`.

## Documentation and demo audit

The README, migration notes, roadmap, changelog, CI guide, security policy,
compatibility policy, SARIF evaluation, package audit, and release audit agree
on the 0.5.0 release state. The README demo is generated from
`assets/pagonic-demo.tape` with VHS and shows the current version, inspection,
verification refusal, and safe-extraction refusal flow.

## Known limits and follow-up

- The release remains alpha and is not a general desktop archive manager.
- The intentional comprehensive-suite skips remain documented test-scope
  limits; they are not converted into a claim of universal coverage.
- SARIF remains deferred until a concrete consumer and safe location strategy
  are available.
- PyPI/TestPyPI publication remains a separate future decision.
- Future work should be driven by dogfood usage, concrete reports, and new
  security regression cases rather than speculative feature expansion.
