# User Guide

## CLI

Inspect an archive before extraction:

```bash
pagonic inspect archive.zip
pagonic inspect archive.zip --json
pagonic inspect archive.zip --markdown
```

Verify an archive in automation:

```bash
pagonic verify archive.zip
pagonic verify archive.zip --max-risk medium
```

`verify` exits with `0` when the archive risk is at or below `--max-risk` and
there are no validation errors. The default maximum is `low`, so `medium`,
`high`, `critical`, or invalid archives fail unless a higher threshold is
explicitly selected.

Inspect and extract with a risk gate:

```bash
pagonic safe-extract archive.zip output/
pagonic safe-extract archive.zip output/ --dry-run
pagonic safe-extract archive.zip output/ --allow-risk high
```

By default, `safe-extract` refuses `high` and `critical` risk archives before
writing files. Even when risk is explicitly allowed, extraction still uses
Pagonic's secure path handling. Use `--dry-run` to see whether extraction would
be allowed without creating the output directory or writing files.

## Inspection Reports

`pagonic inspect --json` is intended for automation. The current alpha report
shape includes:

```json
{
  "archive_path": "archive.zip",
  "file_count": 1,
  "total_compressed_size": 120,
  "total_uncompressed_size": 200,
  "global_compression_ratio": 1.67,
  "risk_level": "ok",
  "risk_flags": [],
  "warnings": [],
  "errors": [],
  "recommended_action": "No inspection risks were detected. Safe extraction is acceptable under normal trust assumptions.",
  "entries": [
    {
      "original_name": "docs/readme.txt",
      "normalized_name": "docs/readme.txt",
      "safe_name": "docs/readme.txt",
      "compressed_size": 120,
      "uncompressed_size": 200,
      "compression_method": 8,
      "compression_ratio": 1.67,
      "crc32": "00000000",
      "risk_flags": []
    }
  ]
}
```

The exact numeric values depend on the archive. The field names above are the
stable alpha surface for report consumers. `pagonic inspect --markdown` renders
the same report as a saved Markdown document with an archive summary, risk flag
table, entry table, and warnings/errors sections.

## Risk Levels

| Level | Meaning |
| --- | --- |
| `ok` | No inspection risks were detected. |
| `low` | Low-risk signal that should be reviewed but usually does not block automation. |
| `medium` | Review before extraction or automation. |
| `high` | Do not extract automatically without an explicit policy decision. |
| `critical` | Reject for automation; the archive is invalid or structurally unsafe. |

## Risk Flags

| Flag | Severity |
| --- | --- |
| `path_traversal` | `high` |
| `absolute_path` | `high` |
| `windows_drive_path` | `high` |
| `hidden_file` | `low` |
| `empty_filename` | `medium` |
| `too_many_files` | `high` |
| `large_uncompressed_size` | `high` |
| `high_compression_ratio` | `high` |
| `unsupported_compression_method` | `medium` |
| `crc_or_structure_error` | `critical` |
| `suspicious_extension` | `medium` |

Compress files:

```bash
pagonic compress file1.txt file2.txt -o archive.zip
```

Compress a directory:

```bash
pagonic compress docs/ -o docs.zip -l 9
```

List archive contents:

```bash
pagonic list archive.zip
pagonic list archive.zip --long
pagonic list archive.zip --tree
```

Extract an archive:

```bash
pagonic extract archive.zip -o output/
```

Use `safe-extract` for untrusted archives.

Inspect configuration:

```bash
pagonic config list
pagonic config get compression_level
```

## GUI

Install with the GUI extra:

```bash
python -m pip install -e .[gui]
```

Launch:

```bash
pagonic-gui
```

The GUI is optional, depends on PyQt6, and is not the primary alpha surface for
safe ZIP inspection. Prefer the CLI for inspect, verify, report, and
safe-extract workflows.

## Python API

Write an archive:

```python
from Pagonic.core.formats.zip_writer import ZipWriter

writer = ZipWriter("archive.zip", compression_level=6)
writer.add_file("report.txt")
writer.finalize()
```

Extract an archive:

```python
from Pagonic.core.formats.zip_reader import ZipReader

reader = ZipReader("archive.zip")
report = reader.inspect()

if report.risk_level in {"ok", "low"}:
    reader.extract_all("output")
```

Use progress callbacks:

```python
def progress(current, total):
    print(f"{current}/{total}")

writer.finalize(progress_callback=progress)
```

## Limits

Pagonic is still an alpha project. Prefer tested ZIP workflows, keep backups for important archives, and treat performance claims as workload-specific until the benchmark suite is refreshed.
