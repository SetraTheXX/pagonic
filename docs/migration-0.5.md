# Pagonic 0.5 Migration Notes

This document describes the transition from the `0.4.x` alpha line to the
`0.5.0` release. The release keeps the focused ZIP APIs and the existing report
schema compatible while making automation and security expectations explicit.

## What changed

- `pagonic verify` and `safe-extract` have a documented risk-threshold and
  exit-code contract.
- The synthetic security corpus covers traversal, collisions, archive
  metadata, structural errors, unsupported methods, and resource limits.
- Inspection JSON field names, aliases, risk severities, and deterministic
  ordering are documented in the [schema contract](inspection-schema.md).
- Bash, PowerShell, and GitHub Actions integration examples are available in
  the [CI integration guide](ci-integration.md).
- `ZipHandler` remains available without a new deprecation warning throughout
  the 0.5 line. New code should use `ZipReader`, `ZipWriter`, and
  `inspect_archive`; see the [compatibility policy](zip-handler-compatibility.md).
- SARIF was evaluated but is not part of the 0.5 implementation surface. It
  will be revisited only when a concrete consumer and archive-entry location
  strategy exist.

## Compatibility

There is no intended breaking runtime API change in 0.5. Existing imports,
legacy `ZipHandler` result shapes, inspection schema version `"1"`, and CLI
exit-code behavior remain supported. The 0.5.x package line uses the import
package `Pagonic` and the distribution name `pagonic`.

## Installation

The 0.5.x package line is available from [PyPI](https://pypi.org/project/pagonic/)
and the matching publication checks are available on
[TestPyPI](https://test.pypi.org/project/pagonic/). The source and release
artifacts remain available through the [GitHub release page](https://github.com/SetraTheXX/pagonic/releases/latest).

Install the current public package with:

```bash
python -m pip install pagonic
```

For untrusted archives, keep the workflow explicit:

```bash
pagonic inspect archive.zip --json
pagonic verify archive.zip --max-risk low
pagonic safe-extract archive.zip output/ --allow-risk low
```

## Validation

The release audit records the local and Windows/Linux CI evidence for the
version, package artifacts, security corpus, clean installation, CLI smoke
checks, and public documentation claims. See [0.5.0 Release Audit](release-audit-0.5.md).
