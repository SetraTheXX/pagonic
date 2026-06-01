# User Guide

## CLI

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
