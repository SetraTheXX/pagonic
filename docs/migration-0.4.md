# Pagonic 0.4 Migration Notes

This document describes the intended migration path from the current 0.3.0
alpha surface toward the 0.4 API direction. It is guidance for development;
it does not publish a package or change the current version.

## Product Flow

The primary workflow is now inspection before extraction:

```text
inspect -> decide from the report -> safe-extract
```

For untrusted ZIP files, prefer:

```bash
pagonic inspect archive.zip --json
pagonic verify archive.zip --max-risk low
pagonic safe-extract archive.zip output/
```

`pagonic extract` remains a compatibility command for trusted archives. It
still uses secure path handling, but it does not apply the inspection risk
gate. New automation should use `verify` and `safe-extract` instead.

## Python API

New code should use the focused public APIs:

```python
from Pagonic import ZipReader, ZipWriter, inspect_archive

report = inspect_archive("archive.zip")
reader = ZipReader("archive.zip")

if report.risk_level in {"ok", "low"}:
    reader.extract_all("output")
```

Use `ZipWriter` for archive creation. `ZipReader.inspect()` is equivalent to
calling `inspect_archive()` for the reader's archive.

## ZipHandler Compatibility

`ZipHandler` remains available in the 0.3 alpha and the 0.4 transition. It is
now a thin compatibility facade that delegates archive creation and extraction
to `ZipWriter` and `ZipReader`. Existing callers can keep using it while new
code moves to the focused APIs.

Do not add new product behavior to `ZipHandler`. A future breaking release may
introduce an explicit deprecation policy, but 0.4 migration work does not
silently remove the class or add a deprecation warning by itself.

## Inspection Report Contract

The serialized report currently declares `schema_version: "1"`. Consumers
should prefer these canonical fields:

- Archive: `archive_path`, `file_count`, `total_compressed_size`,
  `total_uncompressed_size`, `global_compression_ratio`, `risk_level`,
  `risk_flags`, `warnings`, `errors`, `recommended_action`, `entries`.
- Entry: `original_name`, `normalized_name`, `safe_name`, `compressed_size`,
  `uncompressed_size`, `compression_method`, `compression_ratio`, `crc32`,
  `risk_flags`.

The early-alpha aliases `compression_ratio`, `filename`, and `safe_path` remain
for compatibility. New consumers should not build new logic around those
aliases.

### Typed Operation Results

The core operations continue to return ordinary dictionaries, but their stable
keys are exported as `TypedDict` contracts for editors and type checkers:

```python
from Pagonic import ArchiveInfo, ExtractionResult

archive: ArchiveInfo = reader.get_archive_info()
extracted: ExtractionResult = reader.extract_all("output")
```

`ZipWriter.finalize()` returns `CompressionStats`, and
`ZipReader.get_file_info()` returns `FileInfo | None`. These annotations make
the existing compatibility surface explicit without introducing a breaking
runtime wrapper.

### Configuration State

`ConfigManager` remains compatible with the current JSON configuration format.
Its default values are now copied per instance, and `get_recent_files()` plus
`to_dict()` return defensive copies. Callers may safely inspect or modify
returned values without changing another manager instance or the stored
configuration until `set()`/`save()` is used explicitly.

## Dependencies

The base package is intentionally small. Inspection, verification, and safe
extraction require the core dependencies only:

```bash
python -m pip install .
```

Optional surfaces are installed explicitly:

```bash
python -m pip install .[gui]
python -m pip install .[performance]
```

PyQt6 stays optional. NumPy and psutil stay outside the base runtime path and
are not required for the security-aware inspection workflow.

## Validation Checklist

Before treating a 0.4 candidate as ready, run:

```bash
python -m pytest -q
python -m pytest -q --comprehensive
python -m build
python -m pip check
```

Then install the wheel in a clean environment and smoke-test `pagonic --help`,
`inspect`, `verify`, and `safe-extract --dry-run`.

Pagonic remains an alpha-stage, ZIP-focused toolkit. Benchmark output is for
local regression tracking, not a universal performance claim, and this
migration does not position Pagonic as a general desktop archive manager.
