# Pagonic 0.4 Migration Notes

This document describes the migration from the 0.3.0 alpha surface to the
0.4.0 API direction. The migration is now part of the current GitHub release;
the notes remain useful for callers moving from the older compatibility surface.

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

`ZipHandler` remains available through the 0.5 line as a thin compatibility
facade. It delegates archive creation and extraction to `ZipWriter` and
`ZipReader`. Existing callers can keep using it while new code moves to the
focused APIs.

The 0.5 policy keeps the facade's public exports and legacy result shapes
unchanged and does not add a new `DeprecationWarning`. Do not add new product
behavior to `ZipHandler`; future deprecation or removal requires a separate
breaking-release decision and migration path. See the [ZipHandler
Compatibility Policy](zip-handler-compatibility.md) for the inventory,
replacement table, and validation rules.

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
serialized for compatibility. New consumers should not build new logic around
those aliases.

See the [Inspection JSON Schema Contract](inspection-schema.md) for the full
versioning policy, deterministic array ordering, migration example, and clean,
risky, and invalid report shapes.

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

The 0.4.0 release gate included:

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
