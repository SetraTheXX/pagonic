"""
Extraction Worker
=================
QThread worker for non-blocking extraction operations.

"""

import os
import time
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal

class ExtractionWorker(QThread):
    """
    Threaded extraction worker for non-blocking UI.
    
    Signals:
        progress(int, str): Emitted with (percent, current_file)
        finished(dict): Emitted when extraction completes with stats
        error(str): Emitted when an error occurs
    """
    
    progress = pyqtSignal(int, str)  # percent, current_file
    finished = pyqtSignal(dict)       # stats dict
    error = pyqtSignal(str)           # error message
    
    def __init__(self, archive_path: str, output_dir: str, use_mmap: bool = False):
        """
        Initialize extraction worker.
        
        Args:
            archive_path: Path to ZIP archive
            output_dir: Output directory path
            use_mmap: Use memory-mapped extraction for large files
        """
        super().__init__()
        self.archive_path = archive_path
        self.output_dir = output_dir
        self.use_mmap = use_mmap
        self._cancelled = False
    
    def cancel(self):
        """Request cancellation of extraction."""
        self._cancelled = True
    
    def run(self):
        """Execute extraction in background thread."""
        try:
            from Pagonic.core.formats.zip_reader import ZipReader
            
            # Ensure output directory exists
            output_path = Path(self.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Create reader
            reader = ZipReader(self.archive_path)
            entries = reader._get_entries()
            total = len(entries)
            
            if total == 0:
                self.error.emit("Arşiv boş!")
                return
            
            start_time = time.time()
            extracted_size = 0
            
            # Callback for progress
            def on_progress(current: int, total_count: int, filename: str):
                if self._cancelled:
                    raise InterruptedError("Kullanıcı tarafından iptal edildi")
                percent = int(current / total_count * 100)
                self.progress.emit(percent, filename)
            
            # Extract with progress callback
            result = reader.extract_all(
                str(output_path), 
                use_mmap=self.use_mmap,
                progress_callback=on_progress
            )
            
            duration = time.time() - start_time
            
            # Calculate extracted size
            for f in result.get('success', []):
                file_path = output_path / f
                if file_path.exists():
                    extracted_size += file_path.stat().st_size
            
            stats = {
                'archive': self.archive_path,
                'output_dir': str(output_path),
                'files': len(result.get('success', [])),
                'errors': len(result.get('errors', [])),
                'extracted_size': extracted_size,
                'duration': duration,
                'speed': extracted_size / duration / 1024 / 1024 if duration > 0 else 0
            }
            
            if result.get('errors'):
                stats['error_list'] = result['errors'][:5]  # First 5 errors
            
            self.finished.emit(stats)
            
        except InterruptedError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"Hata: {str(e)}")
