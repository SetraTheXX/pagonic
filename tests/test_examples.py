"""Smoke tests for the runnable public examples."""

import os
import subprocess
import sys
from pathlib import Path


def test_basic_usage_runs_as_a_direct_script():
    repository_root = Path(__file__).resolve().parents[1]
    example = repository_root / "examples" / "basic_usage.py"
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)

    result = subprocess.run(
        [sys.executable, str(example)],
        cwd=repository_root,
        capture_output=True,
        text=True,
        env=environment,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Archive risk level: ok" in result.stdout
    assert "Hello from Pagonic!" in result.stdout
