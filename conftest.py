"""Root pytest configuration for the public repo layout."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
PACKAGE_DIR = ROOT / "Pagonic"

for path in (ROOT, PACKAGE_DIR):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)


def pytest_addoption(parser):
    parser.addoption(
        "--comprehensive",
        action="store_true",
        default=False,
        help="Run comprehensive manual tests",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--comprehensive"):
        return

    skip_comprehensive = pytest.mark.skip(reason="need --comprehensive option to run")
    for item in items:
        if "comprehensive" in item.keywords:
            item.add_marker(skip_comprehensive)
