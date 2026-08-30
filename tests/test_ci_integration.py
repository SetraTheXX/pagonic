import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


def _run_pagonic(repository_root, *arguments):
    pagonic = shutil.which("pagonic")
    command = [pagonic] if pagonic else [sys.executable, "-m", "Pagonic.cli.main"]
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    return subprocess.run(
        command + list(arguments),
        cwd=repository_root,
        capture_output=True,
        text=True,
        env=environment,
        check=False,
    )


def test_ci_shell_example_is_a_fail_closed_verify_then_extract_gate():
    repository_root = Path(__file__).resolve().parents[1]
    example = repository_root / "examples" / "ci" / "verify-and-extract.sh"

    script = example.read_text(encoding="utf-8")

    assert "set -euo pipefail" in script
    assert 'pagonic verify "$archive" --max-risk "$max_risk"' in script
    assert 'pagonic safe-extract "$archive" "$output" --allow-risk "$max_risk" --dry-run' in script
    assert 'pagonic safe-extract "$archive" "$output" --allow-risk "$max_risk"' in script


def test_ci_powershell_example_propagates_native_exit_codes():
    repository_root = Path(__file__).resolve().parents[1]
    example = repository_root / "examples" / "ci" / "verify-and-extract.ps1"

    script = example.read_text(encoding="utf-8")

    assert 'ValidateSet("ok", "low", "medium", "high", "critical")' in script
    assert "& pagonic @Arguments" in script
    assert "$LASTEXITCODE -ne 0" in script
    assert '"--dry-run"' in script


def test_ci_documentation_explains_both_gates_and_failure_behavior():
    repository_root = Path(__file__).resolve().parents[1]
    documentation = (repository_root / "docs" / "ci-integration.md").read_text(
        encoding="utf-8"
    )

    assert 'pagonic verify "$ARCHIVE" --max-risk low' in documentation
    assert 'pagonic safe-extract "$ARCHIVE" "$OUTPUT" --allow-risk low --dry-run' in documentation
    assert "real extraction step is not reached" in documentation
    assert "Create demo archive" in documentation
    assert "Replace the demo-archive step" in documentation
    assert "Pagonic is not yet" in documentation
    assert "published to PyPI" in documentation


def test_ci_commands_pass_clean_archive_without_writing_during_dry_run(tmp_path):
    repository_root = Path(__file__).resolve().parents[1]
    archive = tmp_path / "upload.zip"
    output = tmp_path / "extracted"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("payload.txt", b"clean payload")

    verified = _run_pagonic(repository_root, "verify", str(archive), "--max-risk", "low")
    assert verified.returncode == 0, verified.stderr

    preview = _run_pagonic(
        repository_root,
        "safe-extract",
        str(archive),
        str(output),
        "--allow-risk",
        "low",
        "--dry-run",
    )
    assert preview.returncode == 0, preview.stderr
    assert not output.exists()

    extracted = _run_pagonic(
        repository_root,
        "safe-extract",
        str(archive),
        str(output),
        "--allow-risk",
        "low",
    )
    assert extracted.returncode == 0, extracted.stderr
    assert (output / "payload.txt").read_text(encoding="utf-8") == "clean payload"


def test_ci_verify_nonzero_stops_high_risk_archive_before_output(tmp_path):
    repository_root = Path(__file__).resolve().parents[1]
    archive = tmp_path / "risky.zip"
    output = tmp_path / "extracted"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("../outside.txt", b"blocked payload")

    result = _run_pagonic(repository_root, "verify", str(archive), "--max-risk", "low")

    assert result.returncode == 1
    assert not output.exists()
