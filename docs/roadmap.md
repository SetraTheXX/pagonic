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

### 0.4.0 Alpha - Historical baseline

The current release baseline includes:

- `pagonic inspect` with terminal, JSON, and Markdown reports.
- `pagonic verify` with a configurable maximum risk level.
- `pagonic safe-extract` with inspection gating and `--dry-run`.
- Cross-platform path safety and ZIP metadata hardening.
- Deterministic risk flags and a versioned inspection report schema.
- `ZipReader`, `ZipWriter`, and `inspect_archive` as the preferred Python APIs.
- `ZipHandler` as a compatibility facade for older callers.
- Windows/Linux CI coverage for Python 3.10 through 3.13.
- Stable typed contracts for core result mappings.
- Defensive configuration state handling.
- Migration notes for the focused reader/writer/inspection APIs.
- Compatibility boundaries and public claim rules documented.
- Public contribution, security reporting, and issue-template surfaces.
- A directly runnable inspect-first example.
- An explicit automation-facing inspection policy baseline with documented
  thresholds, validation precedence, unsupported-method handling, and exit
  codes.

The previous `0.3.0` release established the initial cleaned-up alpha surface.
The `0.4.0` release established the focused public API and package surface.
The latest PyPI package version is `0.5.0`; `v0.5.1` is published and
smoke-tested on TestPyPI while its PyPI publication remains pending. The 0.5
milestone remains released.

## 0.5.0 Released Milestone

### Theme: Trustworthy Inspection for Automation

The 0.5 goal was to make the existing inspector easier to integrate and harder
to misunderstand. The release improves confidence in the report and policy
surfaces without expanding Pagonic into a general archive manager.

### Workstream A: Stable Inspection and Policy Contracts

- Document the inspection schema as a compatibility contract.
- Define deterministic ordering for risk flags, warnings, errors, and entries.
- Make policy decisions and exit-code behavior explicit for CI users.
- Review configurable resource limits without weakening secure defaults.
- Keep typed Python result contracts synchronized with runtime mappings.

The policy and exit-code baseline is implemented in `Pagonic.cli.policy`,
covered by focused CLI and policy tests, and documented in the [inspection
policy contract](inspection-policy.md). The release audit reviewed the existing
resource-limit defaults and retained them without weakening secure behavior.
The schema compatibility and deterministic ordering contract is documented in
the [Inspection JSON Schema Contract](inspection-schema.md) and locked by
schema regression tests.

### Workstream B: Security Regression Corpus

- Add small synthetic fixtures for traversal and mixed separators.
- Cover duplicate names, normalized path collisions, case collisions, and
  Unicode normalization collisions.
- Cover symlink metadata, encrypted entries, unsupported methods, long names,
  nested archives, corrupt structures, and resource limits.
- Run the relevant fixture set on Windows and Linux.
- Keep malicious or sensitive samples out of the public repository.

The generated corpus in `tests/security/corpus.py` and its focused tests in
`tests/security/test_corpus.py` cover these documented input classes and the
corresponding `safe-extract` allow/refuse boundaries. The CI matrix runs the
corpus on Windows and Linux for the supported Python versions. Future cases
should be added when new security rules or concrete regression reports appear.

### Workstream C: Automation and Reporting

- Keep Markdown output useful as a saved human report.
- Keep SARIF output as a separate decision; it is deferred beyond 0.5 until a
  concrete consumer and a stable archive-entry location strategy exist. See
  the [SARIF evaluation](sarif-evaluation.md).

The copyable [CI integration guide](ci-integration.md) now covers
`verify --max-risk`, `safe-extract --dry-run`, and the final extraction step for
GitHub Actions, Bash, and PowerShell. It relies on exit codes and uses a pinned
published package for consumer workflows; source-checkout installation remains
available as an explicit development option.

### Workstream D: Public Packaging and Onboarding

- Audit the source distribution and wheel contents before any package publish.
- Decide whether a TestPyPI or PyPI alpha release is appropriate.
- Keep the base dependency set small and GUI optional.
- Improve examples, contribution guidance, security reporting, and issue
  triage so outside contributors can make focused changes.

The [package surface audit](package-audit.md) reviewed the 0.4.0 historical
snapshot. The [0.5.0 release audit](release-audit-0.5.md) records the original
pre-publication review of the current wheel and source distribution, metadata,
entry points, optional GUI behavior, and clean install paths. The initial
release decision selected GitHub Release artifacts; the later publication
follow-up is recorded in the [package publishing guide](package-publishing.md).

The `v0.5.0` package is now published on [PyPI](https://pypi.org/project/pagonic/)
and [TestPyPI](https://test.pypi.org/project/pagonic/). The tag-verified manual
workflow remains in place, and the `testpypi` and `pypi` GitHub environments are
restricted to the `main` workflow ref. Both publication workflows completed
successfully with Trusted Publishing and digital attestations.

## 0.5 Release Gates (completed for v0.5.0)

The following gates were checked for `v0.5.0` and are recorded in the
[release audit](release-audit-0.5.md):

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

## 0.5 Issue Backlog (completed)

These seven focused issues formed the 0.5 milestone scope. Their implementation
and review evidence is recorded in the linked commits and release audit; the
GitHub issues are closed after the release is verified.

1. [Define and test the 0.5 inspection policy contract.](https://github.com/SetraTheXX/pagonic/issues/1)
2. [Expand the synthetic ZIP security regression corpus.](https://github.com/SetraTheXX/pagonic/issues/2)
3. [Document JSON schema compatibility and deterministic ordering.](https://github.com/SetraTheXX/pagonic/issues/3)
4. [Add a CI integration example for `verify --max-risk`.](https://github.com/SetraTheXX/pagonic/issues/4)
5. [Audit wheel and source distribution contents for a future alpha publish.](https://github.com/SetraTheXX/pagonic/issues/5)
6. [Evaluate SARIF output without changing the current report schema.](https://github.com/SetraTheXX/pagonic/issues/6)
7. [Decide the compatibility and deprecation path for `ZipHandler`.](https://github.com/SetraTheXX/pagonic/issues/7)

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
- A separately announced breaking-release compatibility and deprecation path
  for `ZipHandler`, subject to migration evidence. The 0.5 policy is recorded
  in the [ZipHandler Compatibility Policy](zip-handler-compatibility.md).

### Packaging follow-up

The first adoption follow-up was operational rather than a runtime feature and
is now complete:

1. Registered the pending GitHub Actions trusted publishers on TestPyPI and
   PyPI for `SetraTheXX/pagonic`, `publish.yml`, and the matching environments.
2. Published the existing `v0.5.0` source tag to TestPyPI and verified clean
   Windows and Linux installation plus the CLI smoke flow.
3. Published the same verified `v0.5.0` distributions to PyPI behind the
   required environment review.
4. Updated the public install instructions to use PyPI, with `uv` and `pipx`
   alternatives.

The immutable `v0.5.0` package description retains the pre-publication README
snapshot; this is a documentation freshness issue, not an installation or
runtime blocker. The prepared `v0.5.1` patch release refreshes the embedded
README and project URLs.

### v0.5.1 public release preparation

The patch release carries no runtime feature. Repository preparation is
complete; the remaining steps require the maintainer's package-index and GitHub
release actions:

- [x] Align package, import, and compatibility-facade versions at `0.5.1`.
- [x] Refresh the embedded README and public install path.
- [x] Update the CI integration example and publishing checklist.
- [x] Regenerate the inspect-first README demo for the current CLI version.
- [x] Publish and smoke-test `v0.5.1` on TestPyPI ([workflow run](https://github.com/SetraTheXX/pagonic/actions/runs/33726198587)).
- [ ] Publish and verify the same artifacts on PyPI.
- [ ] Create the normal GitHub release and begin the public campaign.

No new issue is required for this bounded release-operations sequence; the
existing seven 0.5 issues remain closed.

## How to Contribute to the Roadmap

Open a focused issue using the repository templates. Include the user problem,
the affected command or API, compatibility impact, and measurable acceptance
criteria. Read [CONTRIBUTING.md](../CONTRIBUTING.md) before opening a pull
request and use [SECURITY.md](../SECURITY.md) for vulnerabilities.
