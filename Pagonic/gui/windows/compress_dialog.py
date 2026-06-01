"""
Pagonic Compress Dialog
=======================
Dialog for compressing files/folders into ZIP archive.

Features:
- Source/destination selection
- Compression level options
- Progress bar
"""

import os
import time
from pathlib import Path
from typing import List, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QFrame, QLineEdit, QRadioButton,
    QButtonGroup, QProgressBar, QFileDialog, QMessageBox,
    QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

def format_size(size_bytes: int) -> str:
    """Format byte size."""
    if size_bytes <= 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.1f} {units[unit_index]}"


class CompressionWorker(QThread):
    """Worker for compression."""
    
    progress = pyqtSignal(int, str)  # percent, filename
    finished = pyqtSignal(dict)       # stats
    error = pyqtSignal(str)           # error
    
    def __init__(self, sources: List[str], output_path: str, level: int = 6):
        super().__init__()
        self.sources = sources
        self.output_path = output_path
        self.level = level
    
    def run(self):
        try:
            from Pagonic.core.formats.zip_writer import ZipWriter
            
            # Collect all files
            all_files = []
            for source in self.sources:
                path = Path(source)
                if path.is_dir():
                    for child in path.rglob('*'):
                        if child.is_file():
                            all_files.append((str(child), str(child.relative_to(path.parent))))
                else:
                    all_files.append((str(path), path.name))
            
            if not all_files:
                self.error.emit("Sıkıştırılacak dosya bulunamadı!")
                return
            
            total = len(all_files)
            total_size = sum(os.path.getsize(f[0]) for f in all_files)
            start_time = time.time()
            
            writer = ZipWriter(self.output_path, compression_level=self.level)
            
            for i, (file_path, arc_name) in enumerate(all_files):
                writer.add_file(file_path, arc_name)
                percent = int((i + 1) / total * 100)
                self.progress.emit(percent, os.path.basename(file_path))
                # Small delay for progress visibility
                if i < total - 1:  # Don't delay on last file
                    time.sleep(0.05)  # 50ms delay
            
            writer.finalize()
            
            duration = time.time() - start_time
            archive_size = os.path.getsize(self.output_path)
            
            self.finished.emit({
                'archive': self.output_path,
                'files': total,
                'original_size': total_size,
                'compressed_size': archive_size,
                'ratio': (1 - archive_size / total_size) * 100 if total_size > 0 else 0,
                'duration': duration,
                'speed': total_size / duration / 1024 / 1024 if duration > 0 else 0
            })
            
        except Exception as e:
            self.error.emit(str(e))


class CompressDialog(QDialog):
    """
    Compression dialog.
    
    Features:
    - Source display
    - Destination selection
    - Compression level (fast/normal/max)
    - Progress bar
    """
    
    def __init__(self, sources: List[str], parent=None):
        super().__init__(parent)
        
        self.sources = sources
        self.worker: Optional[CompressionWorker] = None
        
        self.setWindowTitle("🗜️ Arşiv Oluştur - Pagonic")
        self.setModal(True)
        self.setMinimumSize(550, 350)
        self.setMaximumSize(700, 450)
        
        # Default output path
        if len(sources) == 1:
            source_path = Path(sources[0])
            self.default_output = str(source_path.parent / f"{source_path.name}.zip")
        else:
            first_path = Path(sources[0])
            self.default_output = str(first_path.parent / "archive.zip")
        
        # Apply theme
        self.apply_dark_theme()
        
        # Setup UI
        self.setup_ui()
    
    def apply_dark_theme(self):
        """Apply dark theme."""
        self.setStyleSheet('''
            QDialog {
                background-color: #1a1a2e;
            }
            QLabel {
                color: #eaeaea;
                font-size: 13px;
            }
            QLineEdit {
                background-color: #16213e;
                color: #eaeaea;
                border: 2px solid #0f3460;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #e94560;
            }
            QGroupBox {
                color: #eaeaea;
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #0f3460;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
            }
            QRadioButton {
                color: #eaeaea;
                font-size: 13px;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:checked {
                background-color: #e94560;
                border-radius: 9px;
            }
            QRadioButton::indicator:unchecked {
                background-color: #16213e;
                border: 2px solid #0f3460;
                border-radius: 9px;
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
            QPushButton:disabled {
                background-color: #2a2a4e;
                color: #666;
            }
            QPushButton#compressBtn {
                background-color: #e94560;
            }
            QPushButton#compressBtn:hover {
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
        ''')
    
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Header
        header = QLabel("🗜️ Arşiv Oluştur")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #e94560;")
        layout.addWidget(header)
        
        # Source info
        source_label = QLabel(f"📁 Kaynak: {len(self.sources)} öğe")
        source_label.setStyleSheet("color: #888;")
        layout.addWidget(source_label)
        
        # First source name
        first_source = Path(self.sources[0]).name
        if len(self.sources) == 1:
            source_name = QLabel(f"    {first_source}")
        else:
            source_name = QLabel(f"    {first_source} ve {len(self.sources) - 1} diğer...")
        source_name.setStyleSheet("color: #aaa; font-size: 12px;")
        layout.addWidget(source_name)
        
        # Destination
        dest_layout = QHBoxLayout()
        
        dest_label = QLabel("📦 Hedef:")
        dest_layout.addWidget(dest_label)
        
        self.dest_input = QLineEdit(self.default_output)
        dest_layout.addWidget(self.dest_input, 1)
        
        browse_btn = QPushButton("...")
        browse_btn.setMaximumWidth(40)
        browse_btn.clicked.connect(self.browse_output)
        dest_layout.addWidget(browse_btn)
        
        layout.addLayout(dest_layout)
        
        # Compression level
        level_group = QGroupBox("🔧 Sıkıştırma Seviyesi")
        level_layout = QHBoxLayout(level_group)
        
        self.level_group = QButtonGroup(self)
        
        self.fast_radio = QRadioButton("⚡ Hızlı (1)")
        self.fast_radio.setToolTip("En hızlı, düşük sıkıştırma")
        self.level_group.addButton(self.fast_radio, 1)
        level_layout.addWidget(self.fast_radio)
        
        self.normal_radio = QRadioButton("⚖️ Normal (6)")
        self.normal_radio.setToolTip("Dengeli hız ve sıkıştırma")
        self.normal_radio.setChecked(True)
        self.level_group.addButton(self.normal_radio, 6)
        level_layout.addWidget(self.normal_radio)
        
        self.max_radio = QRadioButton("📉 Maksimum (9)")
        self.max_radio.setToolTip("En yüksek sıkıştırma, yavaş")
        self.level_group.addButton(self.max_radio, 9)
        level_layout.addWidget(self.max_radio)
        
        layout.addWidget(level_group)
        
        # Progress bar (hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: #888;")
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("❌ İptal")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        btn_layout.addStretch()
        
        self.compress_btn = QPushButton("✅ Sıkıştır")
        self.compress_btn.setObjectName("compressBtn")
        self.compress_btn.clicked.connect(self.start_compression)
        btn_layout.addWidget(self.compress_btn)
        
        layout.addLayout(btn_layout)
    
    def browse_output(self):
        """Browse for output path."""
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Arşiv Kaydet",
            self.dest_input.text(),
            "ZIP Dosyaları (*.zip)"
        )
        if path:
            if not path.lower().endswith('.zip'):
                path += '.zip'
            self.dest_input.setText(path)
    
    def start_compression(self):
        """Start compression."""
        output_path = self.dest_input.text().strip()
        if not output_path:
            QMessageBox.warning(self, "Uyarı", "Lütfen hedef dosya seçin!")
            return
        
        if not output_path.lower().endswith('.zip'):
            output_path += '.zip'
        
        level = self.level_group.checkedId()
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setVisible(True)
        self.progress_label.setText("Sıkıştırma hazırlanıyor...")
        
        self.compress_btn.setEnabled(False)
        self.cancel_btn.setText("Bekleyin...")
        self.cancel_btn.setEnabled(False)
        
        self.worker = CompressionWorker(self.sources, output_path, level)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def on_progress(self, percent: int, filename: str):
        """Handle progress."""
        self.progress_bar.setValue(percent)
        self.progress_label.setText(f"🗜️ Sıkıştırılıyor: {filename}")
    
    def on_finished(self, stats: dict):
        """Handle completion."""
        QMessageBox.information(
            self,
            "Başarılı",
            f"✅ Sıkıştırma tamamlandı!\n\n"
            f"📦 Arşiv: {Path(stats['archive']).name}\n"
            f"📁 Dosya: {stats['files']}\n"
            f"💾 Boyut: {format_size(stats['original_size'])} → {format_size(stats['compressed_size'])}\n"
            f"📉 Oran: %{stats['ratio']:.1f}\n"
            f"⏱️ Süre: {stats['duration']:.2f}s\n"
            f"⚡ Hız: {stats['speed']:.1f} MB/s"
        )
        self.accept()
    
    def on_error(self, error_msg: str):
        """Handle error."""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.compress_btn.setEnabled(True)
        self.cancel_btn.setText("❌ İptal")
        self.cancel_btn.setEnabled(True)
        
        QMessageBox.critical(self, "Hata", f"Sıkıştırma hatası:\n{error_msg}")
