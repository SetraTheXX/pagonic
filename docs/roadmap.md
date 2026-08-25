# Roadmap

This roadmap replaces the older local phase plans. The old plans were useful for history, but they mixed experiments, stale dates, and future ideas that should not be part of the public repository.

## 0.3.x Stabilization - Completed

- The public tree is clean and CI-backed.
- `inspect`, `verify`, and `safe-extract` are the main CLI value path.
- Invalid and risky archive behavior has explicit CLI policies and tests.
- GUI import smoke coverage does not require PyQt6 for CLI-only users.
- Architecture and user documentation describe the inspection-first flow.
- The supported CI matrix covers Windows/Linux and Python 3.10-3.13.
- Wheel installation, CLI smoke, coverage, and `pip check` run in CI.

## 0.4.x API Polish

- Completed foundation: `ZipReader`, `ZipWriter`, and `inspect_archive` are the
  preferred APIs; `ZipHandler` is a thin compatibility facade.
- Completed foundation: legacy performance dependencies are outside the base
  runtime dependency set.
- Next: review typed return values for archive metadata and operation results.
- Next: clarify config file behavior and CLI defaults.
- Next: decide whether and when to deprecate the compatibility facade in a
  breaking release.
- Keep risk flag meanings and report formats tied to the catalog and schema.

## 0.4.x Release Gate

- Complete the migration review documented in `docs/migration-0.4.md`.
- Re-run the full local validation and review the CI matrix before a 0.4
  version decision.
- Do not publish or change the package version as part of roadmap work alone.

## Later Work

- Consider a lowercase `pagonic` import package with a compatibility plan.
- Revisit benchmarks with repeatable fixtures.
- Treat any Rust or native-performance direction as a separate project plan, not part of this Python public cleanup.
- Consider a minimal GUI only after the CLI inspection workflow is stable.
