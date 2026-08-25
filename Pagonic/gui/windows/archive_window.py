"""
Pagonic Archive Window
======================
ZIP archive viewer with table view and extraction options.

Features:
- Table view with columns (Name, Size, Type, Date)
- Extract all / Extract here buttons
- Progress bar for extraction
"""

import os
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QStatusBar, QTableWidget,
    QTableWidgetItem, QHeaderView, QProgressBar, QFileDialog,
    QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

def format_size(size_bytes: int) -> str:
    """Format byte size."""
    if size_bytes < 0:
        return "-"
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} B"
    
    return f"{size:.1f} {units[unit_index]}"


class ExtractionWorker(QThread):
    """Worker thread for extraction."""
    
    progress = pyqtSignal(int, str)  # percent, filename
    finished = pyqtSignal(dict)       # stats
    error = pyqtSignal(str)           # error
    
    def __init__(self, archive_path: str, output_dir: str):
        super().__init__()
        self.archive_path = archive_path
        self.output_dir = output_dir
    
    def run(self):
        try:
            from Pagonic.core.formats.zip_reader import ZipReader
            
            reader = ZipReader(self.archive_path)
            entries = reader.get_entries()
            total = len(entries)
            
            def on_progress(current: int, total_count: int, filename: str):
                percent = int(current / total_count * 100)
                self.progress.emit(percent, filename)
            
            result = reader.extract_all(self.output_dir, progress_callback=on_progress)
            
            self.finished.emit({
                'success': len(result.get('success', [])),
                'errors': len(result.get('errors', [])),
                'output_dir': self.output_dir
            })
            
        except Exception as e:
            self.error.emit(str(e))


class ArchiveWindow(QMainWindow):
    """
    Archive viewer window.
    
    Features:
    - Table with file list
    - Extract all / Extract here
    - Progress bar
    """
    
    def __init__(self, archive_path: str, parent=None):
        super().__init__(parent)
        
        self.archive_path = archive_path
        self.archive_name = Path(archive_path).name
        self.entries: List[Dict] = []
        self.worker: Optional[ExtractionWorker] = None
        
        self.setWindowTitle(f"📦 {self.archive_name} - Pagonic")
        self.setMinimumSize(800, 500)
        self.setGeometry(150, 150, 900, 600)
        
        # Apply dark theme
        self.apply_dark_theme()
        
        # Setup UI
        self.setup_ui()
        
        # Load archive
        self.load_archive()
    
    def apply_dark_theme(self):
        """Apply modern dark theme."""
        self.setStyleSheet('''
            QMainWindow {
                background-color: #1a1a2e;
            }
            QTableWidget {
                background-color: #16213e;
                color: #eaeaea;
                border: 2px solid #0f3460;
                border-radius: 8px;
                gridline-color: #0f3460;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #0f3460;
            }
            QTableWidget::item:selected {
                background-color: #e94560;
            }
            QTableWidget::item:hover {
                background-color: #0f3460;
            }
            QTableWidget::item:alternate {
                background-color: #1a2744;
            }
            QHeaderView {
                background-color: #0f3460;
            }
            QHeaderView::section {
                background-color: #0f3460;
                color: #eaeaea;
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 13px;
            }
            QHeaderView::section:vertical {
                background-color: #16213e;
                color: #eaeaea;
                border: none;
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
            QPushButton#extractAllBtn {
                background-color: #e94560;
            }
            QPushButton#extractAllBtn:hover {
                background-color: #f39422;
            }
            QProgressBar {
                background-color: #16213e;
                border: 2px solid #0f3460;
                border-radius: 8px;
                height: 25px;
                text-align: center;
                color: #eaeaea;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e94560, stop:1 #f39422);
                border-radius: 6px;
            }
            QStatusBar {
                background-color: #16213e;
                color: #eaeaea;
                font-size: 12px;
            }
            QLabel {
                color: #eaeaea;
            }
            QFrame#pathFrame {
                background-color: #16213e;
                border-radius: 6px;
                padding: 8px;
            }
        ''')
    
    def setup_ui(self):
        """Setup UI."""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Path bar
        path_frame = QFrame()
        path_frame.setObjectName("pathFrame")
        path_layout = QHBoxLayout(path_frame)
        path_layout.setContentsMargins(10, 5, 10, 5)
        
        path_icon = QLabel("📍")
        path_icon.setFont(QFont("Segoe UI", 14))
        path_layout.addWidget(path_icon)
        
        self.path_label = QLabel(self.archive_path)
        self.path_label.setFont(QFont("Segoe UI", 11))
        self.path_label.setStyleSheet("color: #888;")
        path_layout.addWidget(self.path_label, 1)
        
        layout.addWidget(path_frame)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["📄 İsim", "📦 Boyut", "📁 Tür", "📅 Tarih"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 120)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        # Hide vertical header (row numbers) to avoid white corner
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, 1)
        
        # Progress bar (hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: #888;")
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        # Extract button (user chooses folder)
        self.extract_btn = QPushButton("📤 Çıkart")
        self.extract_btn.setObjectName("extractAllBtn")
        self.extract_btn.clicked.connect(self.extract_files)
        btn_layout.addWidget(self.extract_btn)
        
        btn_layout.addStretch()
        
        # Close button
        self.close_btn = QPushButton("❌ Kapat")
        self.close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
        
        # Status bar
        self.statusBar().showMessage("📦 Arşiv yükleniyor...")
    
    def load_archive(self):
        """Load archive contents."""
        try:
            from Pagonic.core.formats.zip_reader import ZipReader
            
            reader = ZipReader(self.archive_path)
            entries = reader.get_entries()
            
            self.entries = []
            self.table.setRowCount(len(entries))
            
            total_size = 0
            total_compressed = 0
            
            for i, entry in enumerate(entries):
                self.entries.append({
                    'filename': entry.filename,
                    'size': entry.uncompressed_size,
                    'compressed': entry.compressed_size
                })
                
                total_size += entry.uncompressed_size
                total_compressed += entry.compressed_size
                
                # Name
                is_dir = entry.filename.endswith('/')
                icon = "📁" if is_dir else "📄"
                name_item = QTableWidgetItem(f"{icon} {entry.filename}")
                name_item.setData(Qt.ItemDataRole.UserRole, entry.filename)
                self.table.setItem(i, 0, name_item)
                
                # Size
                size_text = "-" if is_dir else format_size(entry.uncompressed_size)
                size_item = QTableWidgetItem(size_text)
                size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(i, 1, size_item)
                
                # Type
                if is_dir:
                    file_type = "Klasör"
                else:
                    ext = Path(entry.filename).suffix.upper()
                    file_type = ext[1:] if ext else "Dosya"
                type_item = QTableWidgetItem(file_type)
                type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, 2, type_item)
                
                # Date (placeholder - would need to parse from entry)
                date_item = QTableWidgetItem("-")
                date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, 3, date_item)
            
            # Update status
            ratio = (1 - total_compressed / total_size) * 100 if total_size > 0 else 0
            self.statusBar().showMessage(
                f"🗂️ {len(entries)} dosya | "
                f"💾 {format_size(total_size)} → {format_size(total_compressed)} | "
                f"📉 %{ratio:.1f} sıkıştırma"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Arşiv yüklenemedi:\n{str(e)}")
            self.close()
    
    def extract_files(self):
        """Extract files - user selects output folder."""
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Dosyaların Çıkartılacağı Klasörü Seçin",
            str(Path(self.archive_path).parent)
        )
        if output_dir:
            self.start_extraction(output_dir)
    
    def start_extraction(self, output_dir: str):
        """Start extraction process."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setVisible(True)
        self.progress_label.setText("Çıkartma hazırlanıyor...")
        
        self.extract_btn.setEnabled(False)
        
        self.worker = ExtractionWorker(self.archive_path, output_dir)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def on_progress(self, percent: int, filename: str):
        """Handle progress update."""
        self.progress_bar.setValue(percent)
        self.progress_label.setText(f"📤 Çıkartılıyor: {filename}")
    
    def on_finished(self, stats: dict):
        """Handle extraction complete."""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        self.extract_btn.setEnabled(True)
        
        QMessageBox.information(
            self,
            "Başarılı",
            f"✅ Çıkartma tamamlandı!\n\n"
            f"📁 {stats['success']} dosya çıkartıldı\n"
            f"📂 Konum: {stats['output_dir']}"
        )
        
        self.statusBar().showMessage("✅ Çıkartma tamamlandı")
    
    def on_error(self, error_msg: str):
        """Handle extraction error."""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        self.extract_btn.setEnabled(True)
        
        QMessageBox.critical(self, "Hata", f"Çıkartma hatası:\n{error_msg}")
