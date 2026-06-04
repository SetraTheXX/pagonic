# Pagonic

Pagonic is an alpha Python ZIP toolkit focused on safe archive inspection,
secure extraction, and repeatable local benchmarking. Its main idea is simple:
inspect before you extract.

- A core library for inspecting, writing, reading, and validating ZIP archives.
- A `pagonic` command-line interface for inspect, verify, safe extract, and ZIP utilities.
- An optional PyQt6 GUI launched with `pagonic-gui`.

This repository is currently prepared as an alpha-quality public cleanup release. The import package remains `Pagonic` for compatibility; the distribution name is `pagonic`.

## Install

For local development:

```bash
python -m pip install -e .[dev,gui]
```

For CLI-only development:

```bash
python -m pip install -e .[dev]
```

The GUI is optional. If PyQt6 is not installed, `pagonic-gui` exits with a clear install message.

## CLI Quick Start

```bash
pagonic --help
pagonic inspect suspicious.zip
pagonic inspect suspicious.zip --json
pagonic inspect suspicious.zip --markdown
pagonic verify release.zip
pagonic verify release.zip --max-risk medium
pagonic safe-extract upload.zip output/
pagonic safe-extract upload.zip output/ --dry-run
pagonic list archive.zip --tree
pagonic compress path/to/file.txt -o archive.zip
pagonic config list
```

## Python API Quick Start

```python
from Pagonic.core.formats.zip_writer import ZipWriter
from Pagonic.core.formats.zip_reader import ZipReader

writer = ZipWriter("archive.zip", compression_level=6)
writer.add_file("file.txt")
writer.finalize()

reader = ZipReader("archive.zip")
report = reader.inspect()

if report.risk_level in {"ok", "low"}:
    reader.extract_all("output")
```

## Project Layout

```text
Pagonic/          Python package
tests/            pytest suite
docs/             public documentation
examples/         small runnable examples
pyproject.toml    package metadata and tool config
```

## Documentation

- [Architecture](docs/architecture.md)
- [User Guide](docs/user-guide.md)
- [Developer Guide](docs/developer-guide.md)
- [Roadmap](docs/roadmap.md)
- [Changelog](CHANGELOG.md)

## Risk Signals

Inspection reports are deterministic and do not use runtime AI. Current risk
flags include:

| Flag | Severity | Meaning |
| --- | --- | --- |
| `path_traversal` | `high` | Entry contains `..` path segments. |
| `absolute_path` | `high` | Entry uses a POSIX absolute path. |
| `windows_drive_path` | `high` | Entry looks like a Windows drive path. |
| `hidden_file` | `low` | Entry basename starts with `.`. |
| `empty_filename` | `medium` | Entry cannot be mapped to a useful safe path. |
| `too_many_files` | `high` | Archive exceeds the configured file-count limit. |
| `large_uncompressed_size` | `high` | Archive exceeds the configured uncompressed-size limit. |
| `high_compression_ratio` | `high` | Entry expands much more than its compressed size. |
| `unsupported_compression_method` | `medium` | Entry uses a ZIP method Pagonic does not currently support. |
| `crc_or_structure_error` | `critical` | ZIP structure or CRC validation failed. |
| `suspicious_extension` | `medium` | Entry has an executable or script-like extension. |

`pagonic inspect --json` emits a stable alpha report with archive totals,
overall `risk_level`, top-level `risk_flags`, `recommended_action`, and per-entry
metadata. `pagonic inspect --markdown` renders the same inspection as a saved
human-readable report.

## Status

The current public target is `0.3.0`: a cleaned alpha with security-aware ZIP
inspection, gated safe extraction, core ZIP behavior, CLI support, optional GUI
packaging, MIT license, and CI-ready tests. The next work is stabilization, API
polish, and documentation tightening before a broader release.
