# Contributing to Pagonic

Thank you for considering a contribution. Pagonic is an alpha-stage Python
ZIP inspection and safe extraction toolkit. The project is intentionally small
in scope: contributions should make archive inspection, reporting, validation,
or safe extraction more trustworthy and easier to use.

## Product Boundaries

The current product direction is:

> Inspect before you extract.

Pagonic is not a general multi-format desktop archive manager. Before opening
a large change, please check [the roadmap](docs/roadmap.md) and search existing
issues.

The following are out of scope for the current 0.5 direction unless a roadmap
decision changes:

- New archive formats.
- A GUI redesign or a WinRAR-style desktop application.
- Universal performance claims or benchmark-driven marketing.
- A native rewrite or runtime AI feature.
- Reintroducing the old monolithic `ZipHandler` design.

## Development Setup

Pagonic supports Python 3.10 through 3.13.

```bash
python -m venv .venv
```

On Windows:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

On Unix-like systems:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Install the optional GUI only when working on its existing compatibility
surface:

```bash
python -m pip install -e ".[dev,gui]"
```

## Validation Before a Pull Request

Run the focused tests while developing, then run the complete local gate:

```bash
python -m pytest -q
python -m pytest -q --comprehensive
python -m build
python -m pip check
python examples/basic_usage.py
git diff --check
```

Build output (`build/`, `dist/`, and `*.egg-info/`) and test output must not be
committed. The CI workflow also checks the wheel installation and representative
CLI commands.

## What Good Contributions Look Like

- Start with a focused issue or explain the problem clearly in the pull request.
- Add regression tests for behavior changes, especially security-sensitive ones.
- Keep public JSON and CLI behavior deterministic and document schema changes.
- Preserve cross-platform behavior for Windows and POSIX path inputs.
- Keep optional dependencies optional; the base inspection path must not require
  PyQt6, NumPy, or the experimental performance stack.
- Update user or developer documentation when a command, API, or policy changes.
- Keep public wording factual. Do not add claims that Pagonic is production-ready,
  faster than another archive tool, AI-powered, or a replacement for 7-Zip or
  WinRAR.

## Security-Sensitive Changes

Path handling, ZIP metadata validation, CRC checks, ZIP bomb limits, extraction
policy, and unsupported compression methods are security-sensitive areas. A
change in these areas should include:

- A minimal reproducer or fixture.
- Tests for both the safe and rejected paths.
- An explanation of the extraction target and failure behavior.
- Cross-platform reasoning when path syntax is involved.

Do not include real malicious archives, credentials, private paths, or generated
reports in a pull request. See [SECURITY.md](SECURITY.md) for vulnerability
reports.

## Pull Requests

Keep pull requests narrow enough to review. The description should state the
user problem, the selected solution, compatibility impact, and commands run.
Documentation-only changes are welcome when they remove ambiguity or improve
the contributor experience.

Maintainers may ask for an issue split when a pull request combines unrelated
engine, CLI, documentation, and packaging work.

## Commit and Review Style

Use a short imperative commit subject when possible, for example:

```text
fix: reject unsafe archive metadata
docs: clarify inspect-first workflow
test: cover Windows drive paths on POSIX
```

Reviews prioritize security regressions, compatibility, deterministic output,
test coverage, and truthful product claims.

By contributing, you agree to follow the project's [Code of Conduct](CODE_OF_CONDUCT.md).
