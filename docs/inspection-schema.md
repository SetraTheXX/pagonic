# Inspection JSON Schema Contract

This document defines the current alpha compatibility contract for
`pagonic inspect --json` and `inspect_archive(...).to_dict()`.

The contract is intentionally focused on inspection data. It does not make
`warnings` or `errors` suitable as machine-readable policy identifiers; use
`risk_flags`, `risk_level`, and the documented command exit codes for
automation decisions.

## Versioning policy

Every serialized report contains `schema_version` as a string. The current
version is `"1"`.

Within schema version 1, consumers can rely on the canonical fields, their
types, the compatibility aliases listed below, and the array ordering rules in
this document. Removing or renaming a canonical field, changing its type or
meaning, or changing the meaning of an ordered array requires a new schema
version and migration notes.

Consumers should ignore unknown object fields so additive metadata can be
introduced without breaking a reader. Consumers should reject or explicitly
handle an unknown `schema_version` instead of assuming that it is compatible
with version 1.

Schema versioning is independent from the package version. A package release
may keep schema version 1, and a future schema change may require a schema
version bump without changing the archive format.

## Canonical archive fields

The archive report contains these canonical fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | string | Serialized inspection contract version; currently `"1"`. |
| `archive_path` | string | The archive path supplied to the inspection call. |
| `file_count` | integer | Number of report entries. |
| `total_compressed_size` | integer | Sum of entry compressed sizes in bytes. |
| `total_uncompressed_size` | integer | Sum of entry uncompressed sizes in bytes. |
| `global_compression_ratio` | number | Total uncompressed size divided by total compressed size. |
| `risk_level` | string | One of `ok`, `low`, `medium`, `high`, or `critical`. |
| `risk_flags` | array of strings | De-duplicated archive-level risk IDs. |
| `warnings` | array of strings | Human-readable non-fatal inspection diagnostics. |
| `errors` | array of strings | Human-readable validation or structure diagnostics. |
| `recommended_action` | string | Human-readable summary of the current risk decision. |
| `entries` | array of objects | One report object for each ZIP central-directory entry. |

The early-alpha archive alias `compression_ratio` is also serialized. It has
the same numeric value as `global_compression_ratio`; new consumers should use
the canonical field.

## Canonical entry fields

Each object in `entries` contains these canonical fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `original_name` | string | The member name recorded in the ZIP archive. |
| `normalized_name` | string | Pagonic's canonical normalized extraction name; currently the same value as `safe_name`. |
| `safe_name` | string | Sanitized extraction path using `/` separators. |
| `compressed_size` | integer | Compressed member size in bytes. |
| `uncompressed_size` | integer | Declared uncompressed member size in bytes. |
| `compression_method` | integer | ZIP compression method code. |
| `crc32` | string | Lowercase eight-character hexadecimal CRC value. |
| `compression_ratio` | number | Entry uncompressed size divided by compressed size. |
| `risk_flags` | array of strings | De-duplicated risk IDs for this entry. |

Two early-alpha entry aliases remain serialized:

| Alias | Canonical field | Migration |
| --- | --- | --- |
| `filename` | `original_name` | Read `original_name` in new integrations. |
| `safe_path` | `safe_name` | Read `safe_name` in new integrations. |

The aliases are value-compatible in schema version 1. They are retained for
callers migrating from the early report shape and should not be used as the
primary field names in new code.

## Ordering guarantees

JSON object member order is not a semantic JSON guarantee. For callers using
the Python API, `to_dict()` inserts archive and entry fields in the canonical
order exposed by `ARCHIVE_REPORT_FIELDS` and `ARCHIVE_ENTRY_FIELDS`. The CLI
uses sorted JSON object keys for reproducible text output, so the textual
`--json` key order is lexical rather than the `to_dict()` insertion order.

The following array ordering is part of the schema version 1 contract:

### Entries

`entries` preserves the ZIP central-directory order returned by
`ZipFile.infolist()`. Entries are not alphabetically sorted. Duplicate member
names remain separate entries and retain their original order because that
order is relevant when reviewing ambiguous extraction behavior.

### Risk flags

`risk_flags` is de-duplicated and ordered by the declaration order of
Pagonic's `RISK_CATALOG`, not by the order in which individual checks happen to
run. The current order is:

```text
path_traversal
absolute_path
windows_drive_path
hidden_file
empty_filename
too_many_files
large_uncompressed_size
high_compression_ratio
unsupported_compression_method
crc_or_structure_error
suspicious_extension
duplicate_filename
normalized_path_collision
case_insensitive_collision
unicode_normalization_collision
symlink_entry
encrypted_entry
nested_archive
long_filename
long_archive_comment
```

The same ordering rule applies to archive-level and per-entry risk flag
arrays.

### Warnings

Warnings are emitted in the current diagnostic category order below. When a
warning names members, those names use the corresponding central-directory
entry order; at most the first five names are included in a single message.

1. Too many files.
2. Long archive comment.
3. CRC validation skipped for encrypted entries.
4. CRC validation skipped for unsupported compression methods.
5. Total uncompressed size above the configured limit.

Absent conditions do not add empty warning strings.

### Errors

Errors are emitted in validation detection order. The current inspector emits
at most one structure/CRC error for a readable archive: the first supported,
unencrypted entry that fails validation in central-directory order. An archive
that cannot be opened produces one archive-level invalid/unreadable error and
no entries. Error text is diagnostic prose and may vary with the Python ZIP
implementation; consumers should use the non-empty `errors` array and the
`crc_or_structure_error` risk flag rather than matching the prose.

## Compatibility example

Read the version and canonical fields first. Only use aliases when supporting
older callers or archived reports:

```python
version = payload.get("schema_version")
if version != "1":
    raise ValueError(f"Unsupported inspection schema: {version!r}")

ratio = payload["global_compression_ratio"]
for entry in payload["entries"]:
    original_name = entry["original_name"]
    safe_name = entry["safe_name"]
```

## Report examples

The numeric values below are illustrative. Diagnostic prose can include the
archive's actual path or Python's ZIP error text.

### Clean archive

```json
{
  "schema_version": "1",
  "archive_path": "clean.zip",
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
      "crc32": "00000000",
      "compression_ratio": 1.67,
      "risk_flags": [],
      "filename": "docs/readme.txt",
      "safe_path": "docs/readme.txt"
    }
  ],
  "compression_ratio": 1.67
}
```

### Risky archive

```json
{
  "schema_version": "1",
  "archive_path": "suspicious.zip",
  "file_count": 1,
  "total_compressed_size": 20,
  "total_uncompressed_size": 32,
  "global_compression_ratio": 1.6,
  "risk_level": "high",
  "risk_flags": ["path_traversal", "suspicious_extension"],
  "warnings": [],
  "errors": [],
  "recommended_action": "Do not extract automatically. Review the archive and use safe extraction only in a controlled location.",
  "entries": [
    {
      "original_name": "../payload.exe",
      "normalized_name": "payload.exe",
      "safe_name": "payload.exe",
      "compressed_size": 20,
      "uncompressed_size": 32,
      "compression_method": 8,
      "crc32": "1234abcd",
      "compression_ratio": 1.6,
      "risk_flags": ["path_traversal", "suspicious_extension"],
      "filename": "../payload.exe",
      "safe_path": "payload.exe"
    }
  ],
  "compression_ratio": 1.6
}
```

### Invalid archive

```json
{
  "schema_version": "1",
  "archive_path": "broken.zip",
  "file_count": 0,
  "total_compressed_size": 0,
  "total_uncompressed_size": 0,
  "global_compression_ratio": 0.0,
  "risk_level": "critical",
  "risk_flags": ["crc_or_structure_error"],
  "warnings": [],
  "errors": ["Invalid or unreadable ZIP archive: ..."],
  "recommended_action": "Reject this archive for automation and request a fresh copy from a trusted source.",
  "entries": [],
  "compression_ratio": 0.0
}
```

`inspect` reports invalid input as data and therefore can exit `0` after
emitting this report. Automation that needs a pass/fail decision should use
`verify` or `safe-extract`; both return exit `1` for invalid reports. See the
[inspection policy contract](inspection-policy.md) for the complete decision
table.
