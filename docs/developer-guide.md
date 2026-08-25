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

## Security-Aware ZIP Workflow

Prefer the inspection service for untrusted archives:

```python
from Pagonic import ZipReader, ZipWriter, inspect_archive

report = inspect_archive("archive.zip")
reader = ZipReader("archive.zip")
```

The report is JSON-serializable through `to_dict()` and includes archive-level
size totals, per-entry metadata, risk flags, warnings, errors, and a summary
risk level. `ZipWriter` remains the public creation API. CLI commands such as
`inspect`, `verify`, and `safe-extract` should reuse this service instead of
duplicating path or ZIP bomb checks.

`ZipHandler` is retained only as a compatibility facade. Its `compress()` and
`decompress()` methods delegate to `ZipWriter` and `ZipReader`; new features
must be added to those public APIs first rather than to the facade.

The serialized report declares `schema_version: "1"`. The canonical report
keys are:

- Archive report: `archive_path`, `file_count`, `total_compressed_size`,
  `total_uncompressed_size`, `global_compression_ratio`, `risk_level`,
  `risk_flags`, `warnings`, `errors`, `recommended_action`, `entries`.
- Entry report: `original_name`, `normalized_name`, `safe_name`,
  `compressed_size`, `uncompressed_size`, `compression_method`,
  `compression_ratio`, `crc32`, `risk_flags`.

The early-alpha aliases `compression_ratio` at archive level and `filename`,
`safe_path` in entries remain serialized for compatibility. New consumers
should use `global_compression_ratio`, `original_name`, `normalized_name`, and
`safe_name`.

Risk flag metadata lives in `RISK_CATALOG`. Each catalog entry has an `id`,
`title`, `severity`, `explanation`, and `recommended_action`. Keep new report
renderers and CLI commands attached to that catalog instead of hardcoding
parallel risk descriptions.

CLI policy defaults:

- `verify` passes only archives at or below `--max-risk low` and without
  validation errors.
- `safe-extract` allows up to `--allow-risk medium` by default, refuses
  validation errors, and supports `--dry-run` for decision checks without
  writing files.
- `safe-extract` also refuses `unsupported_compression_method` archives before
  extraction, even when the selected risk threshold would otherwise allow
  `medium`, because unsupported methods cannot be extracted safely by Pagonic.

## Development Notes

- Keep the import package name `Pagonic` until a planned migration introduces lowercase compatibility.
- Keep PyQt6 behind the `gui` optional dependency.
- Keep `numpy` and the optional performance stack behind the `performance` extra; the inspector and safe-extract paths must not require it.
- Prefer focused tests for behavior changes and run the full suite before publishing changes.
- Avoid adding claims about acceleration or automation unless the code and tests support them.
- Keep the public product direction focused on ZIP inspection, verification, reporting, and safe extraction rather than general archive-manager competition.
