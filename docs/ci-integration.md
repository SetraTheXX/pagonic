# CI Integration: Verify Before Extraction

Pagonic is designed to inspect an archive before a build or upload pipeline
extracts it. The examples below use exit codes as the automation contract; they
do not parse human-readable terminal output.

The examples use `low` as the explicit policy threshold. Change the threshold
only when the pipeline has a documented reason to allow higher-risk input, and
change it consistently for both `verify --max-risk` and `safe-extract
--allow-risk`.

## GitHub Actions

This minimal, runnable job creates a small demo archive from `README.md`.
Replace the demo-archive step with the build or upload-artifact step that
produces the archive in your own pipeline.

```yaml
name: Inspect archive before extraction

on:
  workflow_dispatch:

jobs:
  inspect-before-extract:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    env:
      ARCHIVE: artifacts/upload.zip
      OUTPUT: extracted
    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install Pagonic from this checkout
        run: |
          python -m pip install --upgrade pip
          python -m pip install .

      - name: Create demo archive
        run: |
          mkdir -p artifacts
          python - <<'PY'
          from zipfile import ZIP_DEFLATED, ZipFile

          with ZipFile("artifacts/upload.zip", "w", ZIP_DEFLATED) as archive:
              archive.write("README.md", "README.md")
          PY

      - name: Verify archive policy
        run: pagonic verify "$ARCHIVE" --max-risk low

      - name: Preview safe extraction
        run: pagonic safe-extract "$ARCHIVE" "$OUTPUT" --allow-risk low --dry-run

      - name: Extract after both gates pass
        run: pagonic safe-extract "$ARCHIVE" "$OUTPUT" --allow-risk low
```

GitHub Actions stops the job when a `run` step returns a non-zero exit code, so
the real extraction step is not reached when `verify` or the dry run refuses
the archive. `safe-extract --dry-run` also does not create the output directory
or write files.

The example installs from the repository checkout because Pagonic `0.5.0` is
distributed through GitHub Release and is not published to PyPI or TestPyPI.
A future published-package workflow can replace `python -m pip install .` with
its reviewed package installation command.

## Bash

The repository includes a directly reusable script:

```bash
./examples/ci/verify-and-extract.sh artifacts/upload.zip extracted low
```

Its defaults are `extracted` for the output directory and `low` for the maximum
risk. The script uses `set -euo pipefail`, so a failed verification or dry run
ends the script before the real extraction command.

Equivalent inline commands are:

```bash
set -euo pipefail
pagonic verify "$ARCHIVE" --max-risk low
pagonic safe-extract "$ARCHIVE" "$OUTPUT" --allow-risk low --dry-run
pagonic safe-extract "$ARCHIVE" "$OUTPUT" --allow-risk low
```

## PowerShell

Windows pipelines can use the PowerShell equivalent:

```powershell
.\examples\ci\verify-and-extract.ps1 `
  -Archive artifacts\upload.zip `
  -Output extracted `
  -MaxRisk low
```

The script checks `$LASTEXITCODE` after every Pagonic command. This explicit
check is important for native commands because a non-zero process exit does
not necessarily become a terminating PowerShell exception.

## Policy boundaries

`verify --max-risk low` returns exit `0` only when the inspection risk is at or
below `low` and there are no validation errors. `safe-extract --allow-risk low
--dry-run` repeats the extraction policy without writing files, and the final
`safe-extract` performs the real extraction only after both earlier commands
have passed.

Invalid archives, high-risk entries, and unsupported compression methods stop
the workflow. The complete decision table is in the [inspection policy
contract](inspection-policy.md).
