# Security Policy

Pagonic handles ZIP files that may come from untrusted sources. The project is
an alpha-stage toolkit, so security reports and reproducible test cases are
especially valuable.

## Reporting a Vulnerability

Please do not open a public issue for a vulnerability or attach a malicious
archive to a public pull request.

Use GitHub's private vulnerability reporting flow:

<https://github.com/SetraTheXX/pagonic/security/advisories/new>

If private reporting is unavailable, contact the repository maintainer through
their GitHub profile and include the word `Pagonic security report` in the
subject. Please avoid sharing a working exploit publicly until a fix or clear
mitigation has been discussed.

Useful report details include:

- A concise description of the impact.
- The affected command or Python API.
- Python version and operating system.
- A minimal, non-sensitive reproducer when it can be shared privately.
- Whether the issue involves path traversal, resource exhaustion, metadata,
  CRC validation, unsupported methods, or another boundary.

## Scope

The primary security scope is the ZIP inspection and safe extraction workflow:

- `pagonic inspect`
- `pagonic verify`
- `pagonic safe-extract`
- `ZipReader.inspect()` and secure extraction APIs
- Path normalization and archive metadata validation

The optional GUI and experimental performance helpers are secondary surfaces,
but reports affecting them are still welcome.

## Supported Baseline

The current public baseline is the `0.4.x` alpha line and the `main` branch.
Pagonic is not presented as production-ready. Users should validate the tool
against their own threat model and keep extraction targets isolated.

## Disclosure

The maintainer will acknowledge a report when practical, reproduce it, and
coordinate a fix or mitigation before public disclosure where possible. Please
do not make release or performance claims from an unreviewed security fix.
