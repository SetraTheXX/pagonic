# ZipHandler Compatibility Policy

This document defines the compatibility policy for the historical
`ZipHandler` facade. The facade is not the center of new development; it is a
small bridge for callers that have not migrated to the focused APIs.

## Decision for 0.5

`ZipHandler` stays available and behaviorally unchanged throughout the 0.5
line.

- Keep the `Pagonic.ZipHandler` root export.
- Keep the `Pagonic.core.formats.handlers.ZipHandler` lazy export.
- Keep `register_zip_handler()` and the documented legacy result shapes.
- Do not add a new `DeprecationWarning` in 0.5.
- Do not add new product behavior to the facade. New work belongs in
  `ZipReader`, `ZipWriter`, `inspect_archive`, or the explicit CLI policy
  layer.

This is a compatibility choice, not a promise that the historical facade will
remain forever. A future breaking release may introduce a separately reviewed
deprecation and removal path after migration notes, release communication, and
replacement examples are ready.

## Verified facade inventory

The current class metadata and public methods are:

| Surface | Current behavior |
| --- | --- |
| `name`, `extensions`, `can_compress`, `can_decompress` | Identifies the ZIP handler and its basic capabilities. |
| `compress(files, output, options=None, progress_callback=None)` | Creates a `ZipWriter`, adds existing files/directories, and finalizes it. The optional callback is adapted to the writer callback shape. |
| `decompress(archive, target_dir, options=None, use_parallel=False)` | Validates the basic inputs, creates a `ZipReader`, and delegates to `extract_all()`. The retired `use_parallel` hint logs a warning and does not start worker threads. Success results keep the historical `total_entries`/`success`/`failed` keys; failure results also include `error`. |
| `validate(file_path)` | Performs the historical shallow `PK` signature check. It is not a replacement for inspection or policy verification. |
| `get_metadata(archive)` | Returns compatibility metadata, including the handler version, delegation targets, and copied optimization settings. It does not replace an inspection report. |
| `get_compression_ratio(archive=None)` | Reads the ratio from `ZipReader.get_archive_info()` and returns `0.0` for missing or unreadable input. |
| `compress_file(input_file_path, output_file_path, optimization_level="balanced", enable_optimization=True)` | Single-file compatibility wrapper over `compress()`, with legacy success/duration/method fields. |
| `compress_file_with_threading(input_file_path, output_file_path, thread_count=4, chunk_size=None)` | Compatibility wrapper over `compress_file()`; it explicitly reports threading as disabled. |
| `compress_file_adaptive_memory(...)` and `compress_file_adaptive_memory_enhanced(...)` | Compatibility wrappers over `compress_file()`; they do not restore the removed optimization stack. |
| `register_zip_handler()` | Creates a facade instance and registers it with the existing `FormatRegistry`. |

The underscored tuning helpers and compatibility settings are retained because
historical tests and callers inspect some of them, but they are not a new
product contract. They must not become a reason to rebuild the old monolithic
handler or its retired performance stack.

## Current callers and tests

The repository-wide reference inventory found no current CLI or focused reader/
writer workflow that uses `ZipHandler` as its primary implementation. The
remaining references are compatibility exports, documentation, and legacy or
security tests:

| Reference | What it protects |
| --- | --- |
| `Pagonic/__init__.py` and `handlers/__init__.py` | Root and lazy import compatibility. |
| `tests/test_zip_handler_compatibility.py` | Public facade attributes, round-trip behavior, registration, and reader interoperability. |
| `tests/test_import_boundaries.py` | Lazy loading and the absence of optional performance dependencies on import. |
| `tests/formats/test_zip.py` | Historical methods, metadata, tuning helpers, and comprehensive compatibility checks. |
| `tests/security/test_handler_integration.py` | Traversal, size, ZIP bomb, and safe extraction behavior through the facade. |
| `tests/smoke_test.py` and `tests/test_hybrid_multiple_large_files.py` | Older direct smoke/regression callers. |
| `docs/architecture.md`, `docs/developer-guide.md`, and migration notes | Guidance that new code must use the focused APIs. |

The public methods and exports above are the compatibility surface to protect
in 0.5. Private helper names are inventory evidence, not a reason to add more
legacy surface.

## Migration path for new code

Prefer the focused APIs for all new work:

| Legacy usage | Preferred replacement |
| --- | --- |
| `ZipHandler.compress(...)` | `ZipWriter.add_file()`/`add_directory()` followed by `finalize()`. |
| `ZipHandler.decompress(...)` | `ZipReader.extract_all()` for trusted compatibility work; use `inspect`/`verify`/`safe-extract` for untrusted archives. |
| `ZipHandler.validate(...)` | `inspect_archive()` for findings or `pagonic verify` for an automation gate. The old method only checks a signature. |
| `ZipHandler.get_metadata(...)` | `ZipReader.get_archive_info()` plus `ZipReader.inspect()` when risk data is needed. |
| `ZipHandler.get_compression_ratio(...)` | `ZipReader.get_archive_info()` or the canonical inspection ratio fields. |
| `compress_file*` wrappers | Build the operation explicitly with `ZipWriter`; do not rely on retired threading/adaptive-memory claims. |

Example:

```python
from Pagonic import ZipReader, ZipWriter, inspect_archive

writer = ZipWriter("archive.zip")
writer.add_file("payload.txt")
writer.finalize()

report = inspect_archive("archive.zip")
if report.risk_level in {"ok", "low"}:
    ZipReader("archive.zip").extract_all("output")
```

## Future breaking-release policy

No exact release number is promised for deprecation or removal. If usage
evidence justifies it, a separate issue must define all of the following before
the policy changes:

1. The first release that emits a deprecation warning and the exact trigger.
2. The replacement API and migration examples for every public method above.
3. The release interval during which the facade remains available.
4. Whether the root export, module export, and registration helper change
   together or in staged steps.
5. Tests for warnings, imports, legacy result keys, security behavior, and
   warning-as-error environments.
6. The first release allowed to remove the facade, with changelog and migration
   notes.

The warning policy must be deliberate. A warning added only to signal intent
can break consumers that run Python with deprecations treated as errors, while
removal without a warning breaks imports immediately. Neither change belongs
in 0.5.

## Compatibility premortem

| Failure mode | Early warning signal | Mitigation in the selected policy | Residual risk |
| --- | --- | --- | --- |
| A new warning breaks downstream `-Werror` or warnings-as-errors CI. | User reports show failures during handler construction or import. | Add no deprecation warning in 0.5; test that the selected release emits none. | Unknown external callers cannot be measured from this repository. |
| Removing a root or module export breaks imports. | Import-boundary tests or migration reports fail. | Preserve both exports and `register_zip_handler()` in 0.5; require a separate breaking-release plan. | A future removal still requires users to migrate. |
| Legacy result keys or error behavior drift. | Compatibility round-trip/security tests disagree with old callers. | Keep the facade's result shaping and delegate extraction to the already-tested reader; add explicit key assertions. | Some undocumented edge behavior may remain outside the inventory. |
| Security fixes land in the facade and focused APIs differently. | A traversal, size-limit, or unsupported-method test passes through one path but not the other. | Keep archive work delegated to `ZipReader`/`ZipWriter`; new security fixes land in the shared focused layer first. | Legacy private helpers can still confuse contributors if edited. |
| The facade becomes a second product implementation. | New features or optimization claims are proposed directly in `zip_handler.py`. | State an ownership rule: facade wrappers only; focused APIs own new behavior. | Long-term maintenance cost remains until a future decision removes it. |

## Validation for the 0.5 policy

The compatibility suite must continue to cover:

- root and module imports;
- facade metadata and public methods;
- no new `DeprecationWarning` under the 0.5 policy;
- compression/decompression round trips through the focused writer/reader;
- legacy result keys and registration;
- traversal, ZIP bomb, size, and other security boundaries through the facade;
- no accidental loading of optional performance dependencies.

The facade remains available for existing callers, but the supported direction
for new code is explicit: inspect first, then use the focused reader/writer and
policy APIs.
