# Architecture

Pagonic is organized around a security-aware ZIP core with small public entry
points for CLI and GUI usage. The preferred flow for untrusted archives is
inspection first, extraction second.

## Package Map

- `Pagonic.core.formats.zip_writer.ZipWriter` writes archives and normalizes compression levels.
- `Pagonic.core.formats.zip_reader.ZipReader` reads archive entries and extracts files.
- `Pagonic.core.formats.results` defines typed contracts for stable reader/writer result mappings.
- `Pagonic.core.formats.inspection.inspect_archive` produces structured risk reports without extraction.
- `Pagonic.core.formats.handlers.zip_handler.ZipHandler` is a thin compatibility facade for older tests and workflows; it is not the center of new development.
- `Pagonic.core.formats.security` validates archive safety and sanitizes archive paths.
- `Pagonic.core.config_manager.ConfigManager` stores user configuration with isolated mutable defaults.
- `Pagonic.cli` exposes the `pagonic` command.
- `Pagonic.gui` exposes the optional PyQt6 interface through lazy imports.

## Compression Flow

1. The caller creates a `ZipWriter`.
2. Files or raw bytes are queued with archive-safe names.
3. `finalize()` selects the backend and writes the archive.
4. Optional callbacks report item progress.

Small and regular archives use Python's `zipfile` backend. Large-file paths can use the internal minimal writer path where supported by the current code.

## Extraction Flow

1. The caller inspects the archive with `inspect_archive()` or `ZipReader.inspect()`.
2. The caller decides whether the reported risk level is acceptable.
3. `ZipReader.extract_all()` writes entries through secure extraction paths.
4. Optional callbacks report item progress.

The CLI `safe-extract` command applies this gate automatically. It refuses
`high` or `critical` risk archives by default and refuses unsupported ZIP
compression methods before extraction.

The shared threshold and validation precedence is defined in the
[inspection policy contract](inspection-policy.md) and implemented by
`Pagonic.cli.policy`.

## Inspection Flow

1. `inspect_archive()` reads ZIP metadata without extracting files.
2. Each entry receives a normalized safe path, size data, CRC metadata, and risk flags.
3. Archive-level totals and the highest risk level are summarized.
4. Reports can be rendered in the terminal or emitted as JSON or Markdown.

## Security Model

The public ZIP paths are treated as untrusted input. Extraction and archive
naming code must prevent traversal outside the selected target directory,
analyze absolute paths and Windows drive paths consistently across platforms,
reject unsafe filenames where required, and keep ZIP bomb checks explicit.

## Compatibility

The import package remains `Pagonic` in this release. A future lowercase `pagonic` package rename would need a compatibility bridge and migration notes.

`ZipHandler` remains available for older callers, but new code should use
`ZipReader`, `ZipWriter`, and `inspect_archive` directly. The handler now
delegates archive creation and extraction to the public reader/writer APIs and
keeps only compatibility metadata, result shaping, and small legacy wrappers.
It is intentionally kept outside the inspector's normal import path.
