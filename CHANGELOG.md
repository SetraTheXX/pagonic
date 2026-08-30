# Changelog

All notable public changes are recorded here. This file describes implemented
changes; future work belongs in [the roadmap](docs/roadmap.md).

## Unreleased

- Added project URLs and a manually dispatched Trusted Publishing workflow that
  builds from an explicitly selected, version-matched source tag.
- Added maintainer instructions for the TestPyPI-first publication sequence.
- Published `v0.5.0` to TestPyPI and PyPI through GitHub Actions Trusted
  Publishing after clean Windows and Linux package-install smoke tests.
- Updated the package publishing action to support the current core metadata
  format used by the release artifacts.
- No runtime behavior changed; `v0.5.0` remains the latest public release.

## 0.5.0 - Trustworthy inspection for automation

- Promoted the explicit inspection-policy, risk-threshold, and exit-code
  contract for `verify` and `safe-extract` into the supported release surface.
- Added a generated synthetic ZIP security regression corpus covering traversal,
  collisions, metadata, structure, unsupported methods, and resource limits.
- Documented the stable inspection JSON schema, deterministic ordering, CI
  integration examples, and typed operation-result contracts.
- Completed a fresh package-surface and clean-install audit for the 0.5.0
  artifacts. The release is distributed through GitHub; no PyPI or TestPyPI
  upload is made.
- Evaluated SARIF without changing the current report schema and deferred its
  implementation until a concrete consumer and location strategy exist.
- Recorded the `ZipHandler` compatibility policy: the facade remains available
  without a new deprecation warning throughout the 0.5 line.
- Refreshed the inspect-first terminal demo for the current CLI surface.

## 0.4.0 - API polish and public surface

- Stabilized typed result contracts for archive, compression, extraction, and
  file information mappings.
- Added defensive configuration state handling so returned values cannot mutate
  another manager instance or persisted state implicitly.
- Isolated the historical `ZipHandler` behind the focused `ZipReader` and
  `ZipWriter` APIs while preserving compatibility for existing callers.
- Documented the 0.3 to 0.4 migration path and the stable inspection report
  fields.
- Kept inspection, verification, and safe extraction behavior covered by the
  Windows/Linux CI matrix and clean wheel smoke tests.
- Added a directly runnable inspect-first example and a regression test for it.
- Added public contribution, security reporting, review guidance, issue
  templates, and the 0.5 roadmap.

## 0.3.0 - Alpha baseline

- Added security-aware ZIP inspection with terminal, JSON, and Markdown reports.
- Added `verify` and gated `safe-extract` CLI workflows.
- Added deterministic risk flags for path safety, archive metadata, and resource
  limits.
- Hardened cross-platform path handling, including Windows drive paths on POSIX.
- Kept `ZipReader` and `ZipWriter` as the preferred Python APIs.
- Kept `ZipHandler` as a compatibility facade for older callers.
- Added Windows/Linux CI coverage for Python 3.10 through 3.13.
- Kept the optional GUI and experimental performance helpers outside the base
  inspection workflow.

Pagonic remains an alpha-stage, ZIP-focused toolkit. It is not a general
multi-format archive manager and does not make universal performance claims.
