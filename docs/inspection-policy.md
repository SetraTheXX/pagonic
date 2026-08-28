# Inspection Policy Contract

This document defines the policy used by the automation-facing CLI workflows
in the current alpha surface. It separates inspection findings from the
decision to verify or extract an archive.

## Risk order

Risk levels are ordered from least to most severe:

```text
ok < low < medium < high < critical
```

Thresholds are inclusive. A report at the selected threshold is accepted when
the report has no validation errors and no workflow-specific hard stop.

`critical` is reserved for invalid or structurally unsafe input. A report with
one or more validation errors is invalid for automation even when a caller
selects `--max-risk critical` or `--allow-risk critical`.

## Defaults

| Workflow | Option | Default | Meaning |
| --- | --- | --- | --- |
| `verify` | `--max-risk` | `low` | Exit `0` only for reports at or below `low` with no validation errors. |
| `safe-extract` | `--allow-risk` | `medium` | Write files only for reports at or below `medium` with no validation errors and no unsupported methods. |

## Decision table

The policy compares the report's overall risk level with the workflow's
threshold. `safe-extract` adds one extraction-specific rule for compression
methods it cannot write.

| Report state | `verify` | `safe-extract` |
| --- | --- | --- |
| Clean: `ok`, no errors | Accept, exit `0` | Extract, or dry-run accept, exit `0` |
| Reviewable: risk is within the selected threshold, no errors | Accept, exit `0` | Extract, or dry-run accept, exit `0` |
| Risk is above the selected threshold | Reject, exit `1` | Refuse before creating the output path, exit `1` |
| Invalid: `errors` is not empty | Reject, exit `1` | Refuse before creating the output path, exit `1` |
| `unsupported_compression_method` with no errors | Apply the selected risk threshold; it is normally `medium` | Always refuse because Pagonic cannot safely write that method, even with `--allow-risk critical` |

The `unsupported_compression_method` rule does not make `verify` extract an
archive. Therefore, `verify --max-risk medium` may accept a report containing
that medium-severity flag, while `safe-extract` still refuses it.

## Command boundaries and exit codes

| Command | Exit `0` | Exit `1` | Exit `2` |
| --- | --- | --- | --- |
| `inspect` | The report was generated and emitted. Findings, including an invalid archive, remain in the report. | Conflicting output options or an inspection/runtime failure. | Click input/usage error, such as a missing archive path. |
| `verify` | The report passes the selected risk threshold and has no validation errors. | The report is risky, invalid, or otherwise fails the verification policy. | Click input/usage error. |
| `safe-extract` | Policy allows extraction; with `--dry-run`, no files are written. | Policy refuses the archive or extraction reports failed files. | Click input/usage error. |
| `extract` | Compatibility extraction succeeds. | Extraction failure. | Click input/usage error. |

`inspect` is a reporting command, not a gate: an invalid archive is emitted as
a `critical` report so a caller can inspect the reason. Automation that needs a
pass/fail decision should use `verify` or `safe-extract` and rely on exit codes,
not human-readable message text.

Policy rejection happens before `safe-extract` creates its output directory or
writes a file. Secure path handling remains active after a report is accepted.
The older `extract` command is retained for trusted, compatibility-oriented
workflows and does not apply this inspection policy.

## Compatibility notes

The policy evaluates the existing inspection report fields and does not change
the JSON report shape. Risk flags, warnings, errors, and archive entries remain
inspection data; the policy only decides whether an automation-facing command
may continue. Human-readable output may evolve, so integrations should use
the documented exit codes and `inspect --json` for structured data.
