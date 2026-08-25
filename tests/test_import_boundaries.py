"""Regression tests for the lightweight Safe ZIP Inspector import boundary."""

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _run_import_probe(script: str) -> set[str]:
    """Run an import probe in a fresh interpreter and return its module set."""
    environment = os.environ.copy()
    existing_pythonpath = environment.get("PYTHONPATH")
    paths = [str(ROOT)]
    if existing_pythonpath:
        paths.append(existing_pythonpath)
    environment["PYTHONPATH"] = os.pathsep.join(paths)

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    return set(result.stdout.strip().splitlines()) if result.stdout.strip() else set()


LEGACY_IMPORTS = {
    "numpy",
    "psutil",
    "Pagonic.core.formats.registry",
    "Pagonic.core.formats.handlers.zip_handler",
    "Pagonic.core.formats.simd_memory",
    "Pagonic.core.formats.hybrid_decompressor",
    "Pagonic.core.formats.optimized_decompressor",
    "Pagonic.core.formats.compression_utils",
}


def test_import_pagonic_does_not_load_legacy_chain():
    loaded = _run_import_probe(
        "import sys; import Pagonic; "
        "print('\\n'.join(sorted(sys.modules)))"
    )

    assert not LEGACY_IMPORTS.intersection(loaded)


def test_import_inspection_does_not_load_legacy_chain():
    loaded = _run_import_probe(
        "import sys; from Pagonic.core.formats.inspection import inspect_archive; "
        "print('\\n'.join(sorted(sys.modules)))"
    )

    assert not LEGACY_IMPORTS.intersection(loaded)


def test_import_zip_reader_does_not_load_optional_performance_chain():
    loaded = _run_import_probe(
        "import sys; from Pagonic.core.formats.zip_reader import ZipReader; "
        "print('\\n'.join(sorted(sys.modules)))"
    )

    assert not LEGACY_IMPORTS.intersection(loaded)


def test_legacy_exports_remain_lazy_compatible():
    from Pagonic import ZipHandler
    from Pagonic.core.formats import FormatRegistry
    from Pagonic.core.formats.handlers import (
        ZipHandler as HandlerZipHandler,
        register_zip_handler,
    )

    assert ZipHandler is HandlerZipHandler
    assert FormatRegistry is not None
    assert callable(register_zip_handler)


def test_public_zip_api_exports_resolve_from_package_root():
    from Pagonic import (
        ArchiveEntryReport,
        ArchiveInspectionReport,
        ArchiveRisk,
        ZipReader,
        ZipWriter,
        inspect_archive,
    )

    assert ZipReader.__name__ == "ZipReader"
    assert ZipWriter.__name__ == "ZipWriter"
    assert inspect_archive.__name__ == "inspect_archive"
    assert ArchiveEntryReport.__name__ == "ArchiveEntryReport"
    assert ArchiveInspectionReport.__name__ == "ArchiveInspectionReport"
    assert ArchiveRisk.PATH_TRAVERSAL == "path_traversal"
