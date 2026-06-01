"""
Pagonic GUI Windows Package
===========================
Window classes for the WinRAR-like interface.
"""

from .main_window import MainWindow
from .archive_window import ArchiveWindow
from .compress_dialog import CompressDialog
from .settings_dialog import SettingsDialog

__all__ = ['MainWindow', 'ArchiveWindow', 'CompressDialog', 'SettingsDialog']
