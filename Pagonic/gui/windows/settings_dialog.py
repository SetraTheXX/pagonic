"""
Pagonic Settings Dialog
=======================
Settings dialog connected to ConfigManager.

Features:
- Compression level
- Smart compression
- ZIP64 support
- Memory-mapped extraction
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QSlider, QCheckBox, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class SettingsDialog(QDialog):
    """Settings dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("⚙️ Pagonic Ayarları")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        self.setMaximumSize(600, 500)
        
        # Load config
        from Pagonic.core.config_manager import ConfigManager
        self.config = ConfigManager()
        
        # Apply theme
        self.apply_dark_theme()
        
        # Setup UI
        self.setup_ui()
        
        # Load current settings
        self.load_settings()
    
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
            QSlider::groove:horizontal {
                background: #16213e;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #e94560;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e94560, stop:1 #f39422);
                border-radius: 4px;
            }
            QCheckBox {
                color: #eaeaea;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                background-color: #16213e;
                border: 2px solid #0f3460;
            }
            QCheckBox::indicator:checked {
                background-color: #e94560;
                border-color: #e94560;
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
            QPushButton#saveBtn {
                background-color: #e94560;
            }
            QPushButton#saveBtn:hover {
                background-color: #f39422;
            }
        ''')
    
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Header
        header = QLabel("⚙️ Pagonic Ayarları")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #e94560;")
        layout.addWidget(header)
        
        # Compression group
        comp_group = QGroupBox("🗜️ Sıkıştırma")
        comp_layout = QFormLayout(comp_group)
        
        # Compression level
        level_layout = QHBoxLayout()
        self.level_slider = QSlider(Qt.Orientation.Horizontal)
        self.level_slider.setRange(0, 9)
        self.level_slider.setValue(6)
        self.level_slider.valueChanged.connect(self.update_level_label)
        level_layout.addWidget(self.level_slider)
        
        self.level_label = QLabel("6")
        self.level_label.setMinimumWidth(30)
        self.level_label.setStyleSheet("color: #e94560; font-weight: bold;")
        level_layout.addWidget(self.level_label)
        
        comp_layout.addRow("Seviye:", level_layout)
        
        # Smart compression
        self.smart_compress = QCheckBox("Akıllı Sıkıştırma (dosya türüne göre)")
        comp_layout.addRow(self.smart_compress)
        
        # ZIP64
        self.zip64_check = QCheckBox("ZIP64 Desteği (>4GB dosyalar)")
        comp_layout.addRow(self.zip64_check)
        
        layout.addWidget(comp_group)
        
        # Extraction group
        ext_group = QGroupBox("📤 Çıkartma")
        ext_layout = QFormLayout(ext_group)
        
        # Memory-mapped
        self.mmap_check = QCheckBox("Memory-mapped Okuma (hızlı)")
        ext_layout.addRow(self.mmap_check)
        
        layout.addWidget(ext_group)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        reset_btn = QPushButton("🔄 Varsayılana Sıfırla")
        reset_btn.clicked.connect(self.reset_defaults)
        btn_layout.addWidget(reset_btn)
        
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("❌ İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("✅ Kaydet")
        save_btn.setObjectName("saveBtn")
        save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def update_level_label(self, value):
        """Update level label."""
        self.level_label.setText(str(value))
    
    def load_settings(self):
        """Load settings from config."""
        self.level_slider.setValue(self.config.get('compression_level', 6))
        self.smart_compress.setChecked(self.config.get('smart_compression', True))
        self.zip64_check.setChecked(self.config.get('use_zip64', True))
        self.mmap_check.setChecked(self.config.get('use_mmap', True))
    
    def save_settings(self):
        """Save settings to config."""
        self.config.set('compression_level', self.level_slider.value())
        self.config.set('smart_compression', self.smart_compress.isChecked())
        self.config.set('use_zip64', self.zip64_check.isChecked())
        self.config.set('use_mmap', self.mmap_check.isChecked())
        
        QMessageBox.information(
            self,
            "Başarılı",
            "✅ Ayarlar kaydedildi!"
        )
        self.accept()
    
    def reset_defaults(self):
        """Reset to defaults."""
        self.config.reset()
        self.config.save()
        self.load_settings()
        QMessageBox.information(
            self,
            "Sıfırlandı",
            "🔄 Ayarlar varsayılan değerlere sıfırlandı."
        )
