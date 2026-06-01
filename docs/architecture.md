# Architecture

Pagonic is organized around a ZIP core with small public entry points for CLI and GUI usage.

## Package Map

- `Pagonic.core.formats.zip_writer.ZipWriter` writes archives and normalizes compression levels.
- `Pagonic.core.formats.zip_reader.ZipReader` reads archive entries and extracts files.
- `Pagonic.core.formats.handlers.zip_handler.ZipHandler` is the compatibility facade used by older tests and workflows.
- `Pagonic.core.formats.security` validates archive safety and sanitizes archive paths.
- `Pagonic.cli` exposes the `pagonic` command.
- `Pagonic.gui` exposes the optional PyQt6 interface through lazy imports.

## Compression Flow

1. The caller creates a `ZipWriter`.
2. Files or raw bytes are queued with archive-safe names.
3. `finalize()` selects the backend and writes the archive.
4. Optional callbacks report item progress.

Small and regular archives use Python's `zipfile` backend. Large-file paths can use the internal minimal writer path where supported by the current code.

## Extraction Flow

1. The caller creates a `ZipReader`.
2. Archive metadata is parsed and validated.
3. Extraction paths are sanitized before writing to disk.
4. Optional callbacks report item progress.

## Security Model

The public ZIP paths are treated as untrusted input. Extraction and archive naming code must prevent traversal outside the selected target directory, reject unsafe filenames, and keep ZIP bomb checks explicit.

## Compatibility

The import package remains `Pagonic` in this release. A future lowercase `pagonic` package rename would need a compatibility bridge and migration notes.
