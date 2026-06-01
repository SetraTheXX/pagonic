# Developer Guide

## Setup

```bash
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .[dev,gui]
```

On Unix-like shells, activate with `source .venv/bin/activate`.

## Tests

Run the default suite:

```bash
python -m pytest -q
```

Run comprehensive tests:

```bash
python -m pytest -q --comprehensive
```

Run coverage:

```bash
python -m pytest --cov=Pagonic --cov-report=term-missing
```

## Package Checks

```bash
python -m build
python -m pip check
```

## Repository Hygiene

Do not commit bytecode, coverage files, local archives, editor settings, virtual environments, or old planning logs. Public documentation should live in `README.md`, `CHANGELOG.md`, and `docs/`.

## Development Notes

- Keep the import package name `Pagonic` until a planned migration introduces lowercase compatibility.
- Keep PyQt6 behind the `gui` optional dependency.
- Prefer focused tests for behavior changes and run the full suite before publishing changes.
- Avoid adding claims about acceleration or automation unless the code and tests support them.
