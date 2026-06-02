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
```

`verify` exits with `0` for `ok` or `low` risk archives and `1` for
`medium`, `high`, `critical`, or invalid archives.

Inspect and extract with a risk gate:

```bash
pagonic safe-extract archive.zip output/
pagonic safe-extract archive.zip output/ --allow-risk high
```

By default, `safe-extract` refuses `high` and `critical` risk archives before
writing files. Even when risk is explicitly allowed, extraction still uses
Pagonic's secure path handling.

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

The GUI supports drag-and-drop compression and extraction workflows. It is optional and depends on PyQt6.

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
