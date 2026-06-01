"""
Compression Worker
==================
QThread worker for non-blocking compression operations.

Phase 3, Week 6: GUI Development
"""

import os
import time
from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import QThread, pyqtSignal

class CompressionWorker(QThread):
    """
    Threaded compression worker for non-blocking UI.
    
    Signals:
        progress(int, str): Emitted with (percent, current_file)
        finished(dict): Emitted when compression completes with stats
        error(str): Emitted when an error occurs
    """
    
    progress = pyqtSignal(int, str)  # percent, current_file
    finished = pyqtSignal(dict)       # stats dict
    error = pyqtSignal(str)           # error message
    
    def __init__(self, files: List[str], archive_path: str, level: int = 6):
        """
        Initialize compression worker.
        
        Args:
            files: List of file paths to compress
            archive_path: Output archive path
            level: Compression level (0-9)
        """
        super().__init__()
        self.files = files
        self.archive_path = archive_path
        self.level = level
        self._cancelled = False
    
    def cancel(self):
        """Request cancellation of compression."""
        self._cancelled = True
    
    def run(self):
        """Execute compression in background thread."""
        try:
            from Pagonic.core.formats.zip_writer import ZipWriter
            
            # Collect all files (expand directories)
            all_files = []
            for f in self.files:
                path = Path(f)
                if path.is_dir():
                    for child in path.rglob('*'):
                        if child.is_file():
                            all_files.append(str(child))
                else:
                    all_files.append(str(path))
            
            if not all_files:
                self.error.emit("Sıkıştırılacak dosya bulunamadı!")
                return
            
            total = len(all_files)
            total_size = 0
            start_time = time.time()
            
            # Create writer
            writer = ZipWriter(self.archive_path, compression_level=self.level)
            
            # Callback for progress
            def on_progress(current: int, total_count: int):
                if self._cancelled:
                    raise InterruptedError("Kullanıcı tarafından iptal edildi")
                percent = int(current / total_count * 100)
                self.progress.emit(percent, f"Sıkıştırılıyor... {current}/{total_count}")
            
            # Add files
            for i, file_path in enumerate(all_files):
                if self._cancelled:
                    self.error.emit("İptal edildi")
                    return
                
                file_size = os.path.getsize(file_path)
                total_size += file_size
                
                writer.add_file(file_path)
                
                percent = int((i + 1) / total * 100)
                filename = os.path.basename(file_path)
                self.progress.emit(percent, filename)
            
            # Finalize
            stats = writer.finalize()
            
            duration = time.time() - start_time
            archive_size = os.path.getsize(self.archive_path)
            
            result = {
                'archive': self.archive_path,
                'files': total,
                'original_size': total_size,
                'compressed_size': archive_size,
                'ratio': (1 - archive_size / total_size) * 100 if total_size > 0 else 0,
                'duration': duration,
                'speed': total_size / duration / 1024 / 1024 if duration > 0 else 0
            }
            
            self.finished.emit(result)
            
        except InterruptedError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"Hata: {str(e)}")
