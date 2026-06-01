"""Optional PyQt6 graphical interface for Pagonic."""

from Pagonic import __version__

__all__ = ["MainWindow", "ArchiveWindow", "CompressDialog", "SettingsDialog"]


def __getattr__(name):
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    try:
        from .windows import ArchiveWindow, CompressDialog, MainWindow, SettingsDialog
    except ModuleNotFoundError as exc:
        if exc.name == "PyQt6":
            raise RuntimeError(
                "Pagonic GUI requires PyQt6. Install it with 'pip install pagonic[gui]'."
            ) from exc
        raise

    exports = {
        "ArchiveWindow": ArchiveWindow,
        "CompressDialog": CompressDialog,
        "MainWindow": MainWindow,
        "SettingsDialog": SettingsDialog,
    }
    globals().update(exports)
    return exports[name]
