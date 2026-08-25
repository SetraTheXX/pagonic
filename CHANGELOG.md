# Changelog

All notable public changes are recorded here. This file describes implemented
changes; future work belongs in [the roadmap](docs/roadmap.md).

## Unreleased

No unreleased changes.

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
