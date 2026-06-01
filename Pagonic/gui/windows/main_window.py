"""
Pagonic Main Window - Drop Zone
================================
Modern drop zone interface for drag & drop operations.

Features:
- Drag ZIP file → Extract dialog
- Drag folder/files → Compress dialog
- Clean, modern dark theme
"""

import os
import sys
from pathlib import Path
from typing import List, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QStatusBar, QApplication, QFileDialog
)
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent, QPalette, QColor

from Pagonic import __version__

class DropZone(QFrame):
    """Drop zone widget for drag & drop operations."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setAcceptDrops(True)
        self.setMinimumSize(500, 300)
        self.setup_ui()
        self.set_normal_style()
    
    def setup_ui(self):
        """Setup drop zone UI."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        # Icon
        self.icon_label = QLabel("📥")
        self.icon_label.setFont(QFont("Segoe UI", 64))
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)
        
        # Title
        self.title_label = QLabel("ZIP veya Klasör Sürükleyin")
        self.title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("color: #eaeaea;")
        layout.addWidget(self.title_label)
        
        # Subtitle
        self.subtitle_label = QLabel(
            "📦 ZIP dosyası → Çıkart\n"
            "📁 Klasör/Dosya → Sıkıştır"
        )
        self.subtitle_label.setFont(QFont("Segoe UI", 12))
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setStyleSheet("color: #888;")
        layout.addWidget(self.subtitle_label)
    
    def set_normal_style(self):
        """Set normal style."""
        self.setStyleSheet('''
            DropZone {
                background-color: #16213e;
                border: 3px dashed #0f3460;
                border-radius: 20px;
            }
        ''')
    
    def set_hover_style(self):
        """Set hover style when dragging over."""
        self.setStyleSheet('''
            DropZone {
                background-color: #1a2744;
                border: 3px dashed #e94560;
                border-radius: 20px;
            }
        ''')
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.set_hover_style()
            self.icon_label.setText("📂")
            self.title_label.setText("Bırakın...")
    
    def dragLeaveEvent(self, event):
        """Handle drag leave."""
        self.set_normal_style()
        self.icon_label.setText("📥")
        self.title_label.setText("ZIP veya Klasör Sürükleyin")
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event."""
        self.set_normal_style()
        self.icon_label.setText("📥")
        self.title_label.setText("ZIP veya Klasör Sürükleyin")
        
        urls = event.mimeData().urls()
        if not urls:
            return
        
        paths = [url.toLocalFile() for url in urls]
        self.parent_window.handle_dropped_files(paths)


class MainWindow(QMainWindow):
    """
    Main application window with drop zone.
    
    Features:
    - Drag & drop zone for ZIP/folders
    - Buttons for manual file selection
    - Modern dark theme
    """
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("🗜️ Pagonic ZIP Manager")
        self.setMinimumSize(700, 500)
        self.setGeometry(200, 200, 700, 500)
        
        # Apply dark theme
        self.apply_dark_theme()
        
        # Setup UI
        self.setup_ui()
    
    def apply_dark_theme(self):
        """Apply modern dark theme."""
        self.setStyleSheet('''
            QMainWindow {
                background-color: #1a1a2e;
            }
            QPushButton {
                background-color: #0f3460;
                color: #eaeaea;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e94560;
            }
            QPushButton:pressed {
                background-color: #c73e54;
            }
            QStatusBar {
                background-color: #16213e;
                color: #eaeaea;
                font-size: 12px;
                padding: 5px;
            }
            QLabel {
                color: #eaeaea;
            }
        ''')
    
    def setup_ui(self):
        """Setup main UI."""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("🗜️ Pagonic ZIP Manager")
        header.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #e94560;")
        layout.addWidget(header)
        
        # Drop zone
        self.drop_zone = DropZone(self)
        layout.addWidget(self.drop_zone, 1)
        
        # Buttons row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        # Open ZIP button
        self.open_zip_btn = QPushButton("📦 ZIP Aç")
        self.open_zip_btn.clicked.connect(self.open_zip_file)
        btn_layout.addWidget(self.open_zip_btn)
        
        # Create archive button
        self.create_btn = QPushButton("📁 Klasör Sıkıştır")
        self.create_btn.clicked.connect(self.select_folder_to_compress)
        btn_layout.addWidget(self.create_btn)
        
        # Settings button
        self.settings_btn = QPushButton("⚙️ Ayarlar")
        self.settings_btn.clicked.connect(self.show_settings)
        btn_layout.addWidget(self.settings_btn)
        
        layout.addLayout(btn_layout)
        
        # Status bar
        self.statusBar().showMessage("🚀 Hazır - ZIP veya klasör sürükleyin")
    
    def handle_dropped_files(self, paths: List[str]):
        """Handle dropped files/folders."""
        if not paths:
            return
        
        first_path = paths[0]
        
        # Check if it's a ZIP file
        if first_path.lower().endswith('.zip'):
            self.open_archive(first_path)
        else:
            # It's a folder or file(s) - compress
            self.compress_files(paths)
    
    def open_zip_file(self):
        """Open ZIP file dialog."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "ZIP Dosyası Seç",
            "",
            "ZIP Dosyaları (*.zip);;Tüm Dosyalar (*.*)"
        )
        if path:
            self.open_archive(path)
    
    def select_folder_to_compress(self):
        """Select folder to compress."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Sıkıştırılacak Klasör Seç",
            ""
        )
        if path:
            self.compress_files([path])
    
    def open_archive(self, path: str):
        """Open archive in viewer window."""
        from Pagonic.gui.windows.archive_window import ArchiveWindow
        
        self.statusBar().showMessage(f"📦 Arşiv açılıyor: {path}")
        
        archive_window = ArchiveWindow(path, self)
        archive_window.show()
    
    def compress_files(self, paths: List[str]):
        """Open compress dialog."""
        from Pagonic.gui.windows.compress_dialog import CompressDialog
        
        self.statusBar().showMessage(f"🗜️ Sıkıştırma: {len(paths)} öğe")
        
        dialog = CompressDialog(paths, self)
        dialog.exec()
    
    def show_settings(self):
        """Show settings dialog."""
        from Pagonic.gui.windows.settings_dialog import SettingsDialog
        
        dialog = SettingsDialog(self)
        dialog.exec()


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Pagonic")
    app.setOrganizationName("Pagonic Team")
    app.setApplicationVersion(__version__)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
