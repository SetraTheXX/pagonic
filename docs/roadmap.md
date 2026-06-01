# Roadmap

This roadmap replaces the older local phase plans. The old plans were useful for history, but they mixed experiments, stale dates, and future ideas that should not be part of the public repository.

## 0.3.x Stabilization

- Keep the public tree clean and CI-backed.
- Tighten CLI behavior and error messages.
- Add focused GUI smoke coverage without requiring PyQt6 for CLI-only users.
- Refresh architecture and user docs as APIs settle.
- Keep the test suite green on Windows and Linux.

## 0.4.x API Polish

- Review `ZipWriter`, `ZipReader`, and `ZipHandler` for a smaller stable public surface.
- Remove or quarantine internal experimental helpers that are not part of the API.
- Improve typed return values for archive metadata and operation results.
- Clarify config file behavior and CLI defaults.

## 0.5.x Packaging and Release Prep

- Add release automation only after the package metadata is stable.
- Validate editable install, wheel build, and CLI entry points in CI.
- Publish release notes with tested features and known limitations.

## Later Work

- Consider a lowercase `pagonic` import package with a compatibility plan.
- Revisit benchmarks with repeatable fixtures.
- Treat any Rust or native-performance direction as a separate project plan, not part of this Python public cleanup.
