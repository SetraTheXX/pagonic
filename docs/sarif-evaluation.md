# SARIF Evaluation

Status: **defer implementation beyond 0.5**. This issue records the design
boundary and decision; it does not add a SARIF command, dependency, or upload
workflow.

## Decision

SARIF is useful when a downstream security system already consumes SARIF, but
there is not enough evidence to make it part of the 0.5 implementation scope.
Pagonic's current audience needs an archive policy gate first: `verify` and
`safe-extract` already expose the required exit-code behavior, while JSON is
the primary structured report.

The current repository has no concrete Code Scanning upload workflow, and
Pagonic findings describe ZIP entries and archive metadata rather than source
code lines. Adding a second output contract now would create compatibility and
privacy surface before a real consumer has asked for it. The decision is
therefore **defer**, not reject: revisit it after a concrete CI or code-scanning
use case appears.

This evaluation uses the [OASIS SARIF 2.1.0
specification](https://docs.oasis-open.org/sarif/sarif/v2.1.0/os/sarif-v2.1.0-os.html)
and GitHub's [SARIF code-scanning
guidance](https://docs.github.com/en/code-security/concepts/code-scanning/sarif-files).

## Target consumers and fit

| Consumer or workflow | Fit today | Assessment |
| --- | --- | --- |
| Pagonic CI gate | High | Keep using `verify --max-risk` and `safe-extract --allow-risk`; exit codes are the gate contract. |
| Saved machine-readable report | High | Keep using `inspect --json`; schema version 1 is already documented and tested. |
| GitHub Code Scanning | Conditional | SARIF can surface third-party findings, but ZIP entry locations are not naturally source-code locations and the repository has no configured upload workflow. |
| Generic SARIF viewer or security aggregator | Conditional | Standard ingestion could be valuable, but no downstream viewer or user workflow is currently in scope. |
| Package installation or archive extraction | Low | SARIF does not replace the inspection policy, secure path handling, or extraction result. |

GitHub documents SARIF 2.1.0 support and the `upload-sarif` action for results
generated outside GitHub. A future workflow would also need the appropriate
`security-events: write` permission and, when multiple analyses share a
commit, a distinct category. See GitHub's [uploading a SARIF
file](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/integrate-with-existing-tools/upload-sarif-file)
documentation. This is a future integration sketch, not a change to the
current CI workflow.

## Mapping the current inspection model

The existing JSON report remains authoritative. A future SARIF adapter would
translate it without renaming or changing any JSON field:

| Pagonic data | SARIF location | Preservation rule |
| --- | --- | --- |
| `RISK_CATALOG` entry | `runs[0].tool.driver.rules[]` | Use the exact risk ID as `ruleId`, keep the title and explanation as rule descriptions, and preserve catalog order. |
| Archive-level risk flag | `runs[0].results[]` | Emit one result with archive scope and no fabricated source line. |
| Entry-level risk flag | `runs[0].results[]` | Emit one result for each entry/risk pair in central-directory order, then risk-catalog order. |
| `risk_level` | `run.properties.pagonic.risk_level` and result properties | Keep the five-level Pagonic value; do not collapse it into SARIF severity. |
| Risk definition `severity` | `result.level` | Map `low` to `note`, `medium` to `warning`, and `high`/`critical` to `error`; preserve the original severity in `properties`. |
| Entry metadata | `result.properties.pagonic` | Preserve original/normalized/safe names, sizes, compression method, CRC, ratio, and the inspection schema version. |
| Warnings and errors | `invocations[].toolExecutionNotifications` plus run properties | Preserve current diagnostic order and text; an error notification does not replace the corresponding critical finding. |
| Archive totals and action | `run.properties.pagonic` | Preserve counts, sizes, ratio, `recommended_action`, and the source report schema version. |

The complete current risk-to-SARIF severity mapping is:

| Pagonic severity | SARIF `level` | Current risk IDs |
| --- | --- | --- |
| `critical` | `error` | `crc_or_structure_error` |
| `high` | `error` | `path_traversal`, `absolute_path`, `windows_drive_path`, `too_many_files`, `large_uncompressed_size`, `high_compression_ratio`, `duplicate_filename`, `normalized_path_collision`, `case_insensitive_collision`, `unicode_normalization_collision`, `symlink_entry`, `encrypted_entry` |
| `medium` | `warning` | `empty_filename`, `unsupported_compression_method`, `suspicious_extension`, `long_filename` |
| `low` | `note` | `hidden_file`, `nested_archive`, `long_archive_comment` |

The `error` bucket intentionally contains both `high` and `critical`; SARIF
has a three-level result vocabulary, so the exact Pagonic severity must remain
in a namespaced property. `unsupported_compression_method` also remains a
medium warning in SARIF even though `safe-extract` treats it as an extraction
hard stop. Policy behavior is not inferred from SARIF `level`.

## Location and privacy rules

SARIF locations are the main uncertainty for this product. A ZIP member is
not a source file with a line and column, and the archive may be an external
CI artifact rather than a repository file.

If implementation is revisited:

- Use a stable logical location such as an archive/member identity when no
  repository-relative physical location exists.
- Add a `physicalLocation` only when the archive is a repository-relative
  artifact and the target consumer can navigate to it.
- Omit a fabricated line number; preserve the member name in a structured
  property instead.
- Never copy a machine-local absolute `archive_path` into a URI, message, or
  fingerprint. Use a sanitized relative name or basename for external output.
- JSON escaping must handle malicious or control characters in archive entry
  names without turning them into markup or executable content.

This keeps SARIF from leaking local paths and avoids promising navigation that
the consumer cannot actually provide.

## Stability and exit-code contract

A future exporter should have its own small mapping contract while leaving the
existing JSON inspection schema untouched:

- Emit SARIF `version` `"2.1.0"` and the official `$schema` URL.
- Include a Pagonic mapping version, initially `"1"`, in a namespaced run
  property. This is separate from the existing inspection `schema_version`.
- Keep rule IDs equal to the current `RISK_CATALOG` IDs. Do not use localized
  titles or human-readable prose as identifiers.
- Order rules by catalog declaration order. Order results by archive entry
  order and then catalog order. Keep warnings and notifications in the
  documented diagnostic order.
- Treat SARIF as an additive output format. Unknown SARIF properties may be
  ignored by consumers, but the existing JSON aliases and fields must not be
  removed because SARIF was added.
- Use deterministic text serialization for CLI output, while treating JSON
  object member order as non-semantic.

The output format must not change the policy contract:

| Future command shape | Exit behavior |
| --- | --- |
| `inspect --sarif` | Same as `inspect`: emit a report for an invalid archive and return `0`; usage/conflict/runtime failures retain their existing non-zero codes. |
| `verify --sarif` (only if later justified) | Same as `verify`: `0` only when the selected threshold passes with no validation errors; policy refusal remains `1`, usage remains `2`. |
| `safe-extract --sarif` | Not proposed for the first implementation. Extraction remains a gated action, not another report producer. |

Consumers must continue to use `verify` or `safe-extract` for pass/fail
automation. A SARIF `warning` or `error` is a display/interchange mapping, not
a replacement for Pagonic policy evaluation.

## Minimal future implementation boundary

If a concrete consumer justifies the work, the smallest first slice would be:

1. Add `pagonic inspect ARCHIVE --sarif` as a mutually exclusive reporting
   option alongside `--json` and `--markdown`.
2. Use the standard-library JSON writer; do not add a runtime dependency or
   network access.
3. Generate one SARIF run with the mapping above and write it to stdout so
   shells and CI can redirect it to an artifact.
4. Add fixture coverage for every current risk severity, archive-level and
   entry-level findings, deterministic ordering, invalid archives, path
   redaction, and unchanged exit codes.
5. Add a separately reviewed CI example only after the repository has an
   actual SARIF consumer and the required repository permissions are known.

No part of this slice is accepted or implemented by Issue #6.

## Revisit triggers

Reopen the implementation decision when at least one of these is concrete:

- A user needs Pagonic findings in GitHub Code Scanning or another named SARIF
  consumer.
- A CI workflow needs to aggregate archive inspection with other security
  analyzers.
- A stable location/fingerprint strategy for external ZIP entries has been
  tested with the target consumer.

Until then, the supported integration path remains JSON plus the existing
policy exit codes and CI examples.
