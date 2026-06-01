# Changelog

## 0.3.0 - 2026-06-02

- Prepared the repository for public visibility with a clean root layout.
- Moved the active test suite to root `tests/`.
- Added `pyproject.toml`, MIT license, examples, and GitHub Actions test workflow.
- Added public English documentation under `docs/`.
- Added CLI and GUI entry points in package metadata.
- Synced package, CLI, and GUI versions to `0.3.0`.
- Kept PyQt6 as an optional `gui` dependency with a lazy GUI entry point.
- Removed old local plans, generated artifacts, logs, coverage outputs, bytecode, and packaging leftovers from the public tree.

## 0.2.0 - 2026-01-09

- Split ZIP reader and writer responsibilities out of the older handler-centered structure.
- Added security-focused tests for path traversal and ZIP safety.
- Added callback support used by CLI and GUI workflows.

## 0.1.0

- Initial local prototype.
