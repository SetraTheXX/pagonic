# Changelog

All notable public changes are recorded here. This file describes implemented
changes; future work belongs in [the roadmap](docs/roadmap.md).

## Unreleased

- Added public contribution, security reporting, and review guidance.
- Added issue and pull request templates for focused contributions.
- Added the 0.5 roadmap and explicit product boundaries.

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
