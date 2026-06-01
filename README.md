# Pagonic

Pagonic is a Python ZIP compression toolkit with three public surfaces:

- A core library for writing, reading, and validating ZIP archives.
- A `pagonic` command-line interface.
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
pagonic compress path/to/file.txt -o archive.zip
pagonic list archive.zip
pagonic extract archive.zip -o output/
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

## Status

The current public target is `0.3.0`: a cleaned repository with core ZIP behavior, CLI support, optional GUI packaging, MIT license, and CI-ready tests. The next work is stabilization, API polish, and documentation tightening before a broader release.
