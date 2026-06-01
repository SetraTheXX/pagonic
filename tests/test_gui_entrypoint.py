"""Import smoke tests for the optional GUI package."""

import importlib

import pytest

from Pagonic import __version__


def test_gui_package_import_is_lazy():
    gui = importlib.import_module("Pagonic.gui")

    assert gui.__version__ == __version__


def test_gui_entrypoint_imports_without_launching():
    module = importlib.import_module("Pagonic.gui.__main__")

    assert callable(module.main)


def test_gui_window_import_when_pyqt6_available():
    pytest.importorskip("PyQt6")

    module = importlib.import_module("Pagonic.gui.windows.main_window")

    assert callable(module.main)
