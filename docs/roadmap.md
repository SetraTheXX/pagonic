# Pagonic Roadmap

This roadmap describes the direction of the project. It is a public planning
document, not a promise that every item will ship on a fixed date.

## Product Direction

Pagonic is a Python-first ZIP inspection and safe extraction toolkit for
developers, CI jobs, and applications that receive archives from untrusted or
uncertain sources.

> Inspect before you extract.

Pagonic is not trying to replace a general desktop archive manager. The
roadmap does not target a WinRAR-style GUI, broad archive-format support,
universal benchmark superiority, or runtime AI features.

## Current Baseline

### 0.3.0 Alpha - Available

The current baseline includes:

- `pagonic inspect` with terminal, JSON, and Markdown reports.
- `pagonic verify` with a configurable maximum risk level.
- `pagonic safe-extract` with inspection gating and `--dry-run`.
- Cross-platform path safety and ZIP metadata hardening.
- Deterministic risk flags and a versioned inspection report schema.
- `ZipReader`, `ZipWriter`, and `inspect_archive` as the preferred Python APIs.
- `ZipHandler` as a compatibility facade for older callers.
- Windows/Linux CI coverage for Python 3.10 through 3.13.

The current package version remains `0.3.0` until a separate release decision is
made. Roadmap work alone does not bump the version, create a tag, or publish a
package.

### 0.4 API Polish - Foundation Completed

The main branch now has the 0.4 API polish foundation:

- Stable typed contracts for core result mappings.
- Defensive configuration state handling.
- Migration notes for the focused reader/writer/inspection APIs.
- Compatibility boundaries and public claim rules documented.

The next product milestone is 0.5, not a blind version bump.

## 0.5 Proposed Milestone

### Theme: Trustworthy Inspection for Automation

The 0.5 goal is to make the existing inspector easier to integrate and harder
to misunderstand. It should improve confidence in the report and policy
surfaces without expanding Pagonic into a general archive manager.

### Workstream A: Stable Inspection and Policy Contracts

- Document the inspection schema as a compatibility contract.
- Define deterministic ordering for risk flags, warnings, errors, and entries.
- Make policy decisions and exit-code behavior explicit for CI users.
- Review configurable resource limits without weakening secure defaults.
- Keep typed Python result contracts synchronized with runtime mappings.

### Workstream B: Security Regression Corpus

- Add small synthetic fixtures for traversal and mixed separators.
- Cover duplicate names, normalized path collisions, case collisions, and
  Unicode normalization collisions.
- Cover symlink metadata, encrypted entries, unsupported methods, long names,
  nested archives, corrupt structures, and resource limits.
- Run the relevant fixture set on Windows and Linux.
- Keep malicious or sensitive samples out of the public repository.

### Workstream C: Automation and Reporting

- Add concise integration examples for JSON inspection and exit codes.
- Document how a CI job can inspect an upload before extraction.
- Keep Markdown output useful as a saved human report.
- Evaluate SARIF output as a separate issue; it is not committed to the 0.5
  scope until the existing schema and policy behavior are stable.

### Workstream D: Public Packaging and Onboarding

- Audit the source distribution and wheel contents before any package publish.
- Decide whether a TestPyPI or PyPI alpha release is appropriate.
- Keep the base dependency set small and GUI optional.
- Improve examples, contribution guidance, security reporting, and issue
  triage so outside contributors can make focused changes.

## 0.5 Release Gates

A 0.5 candidate should not be called ready until all of these are true:

- Normal and comprehensive local suites pass.
- Windows and Linux CI passes for the supported Python range.
- Security regression fixtures cover every documented high-impact rule.
- JSON report keys, risk severities, and CLI exit codes are documented and
  tested.
- Wheel and source distribution contents are reviewed.
- Clean-environment CLI smoke passes for inspect, verify, and safe extraction.
- `pip check` passes in the supported installation path.
- Public docs contain no unsupported speed, AI, or archive-manager claims.
- A release decision explicitly chooses the version, tag, and package target.

## Issue Backlog Candidates

These are the first focused issues for the 0.5 milestone. Each should remain
small enough to review independently.

1. [Define and test the 0.5 inspection policy contract.](https://github.com/SetraTheXX/pagonic/issues/1)
2. [Expand the synthetic ZIP security regression corpus.](https://github.com/SetraTheXX/pagonic/issues/2)
3. [Document JSON schema compatibility and deterministic ordering.](https://github.com/SetraTheXX/pagonic/issues/3)
4. [Add a CI integration example for `verify --max-risk`.](https://github.com/SetraTheXX/pagonic/issues/4)
5. [Audit wheel and source distribution contents for a future alpha publish.](https://github.com/SetraTheXX/pagonic/issues/5)
6. [Evaluate SARIF output without changing the current report schema.](https://github.com/SetraTheXX/pagonic/issues/6)
7. [Write a compatibility decision for the future `ZipHandler` deprecation.](https://github.com/SetraTheXX/pagonic/issues/7)

Issues that add a new archive format, redesign the GUI, rewrite the engine in a
native language, or make universal speed claims should be discussed separately
and are not 0.5 acceptance criteria.

## After 0.5

Possible later work, subject to evidence and maintainer review:

- A formal lowercase `pagonic` import-package migration with compatibility
  shims.
- Optional report integrations beyond JSON and Markdown.
- A minimal inspector GUI only if the CLI/API workflow proves useful first.
- A separately maintained native-performance experiment, if benchmarks show a
  real need and the maintenance cost is understood.
- A clearer compatibility and deprecation policy for `ZipHandler`.

## How to Contribute to the Roadmap

Open a focused issue using the repository templates. Include the user problem,
the affected command or API, compatibility impact, and measurable acceptance
criteria. Read [CONTRIBUTING.md](../CONTRIBUTING.md) before opening a pull
request and use [SECURITY.md](../SECURITY.md) for vulnerabilities.
