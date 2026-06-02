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
pagonic verify release.zip
pagonic safe-extract upload.zip output/
pagonic compress path/to/file.txt -o archive.zip
pagonic list archive.zip
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
flags include path traversal, absolute paths, Windows drive paths, hidden files,
high compression ratios, unsupported compression methods, suspicious extensions,
and CRC or structure errors.

## Status

The current public target is `0.3.0`: a cleaned alpha with security-aware ZIP
inspection, gated safe extraction, core ZIP behavior, CLI support, optional GUI
packaging, MIT license, and CI-ready tests. The next work is stabilization, API
polish, and documentation tightening before a broader release.
