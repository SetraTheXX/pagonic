"""
ZipWriter - ZIP Archive Compression Module
==========================================
Modular ZIP file writer with hybrid backend selection.

Day 9: Extracted from zip_handler.py as part of Phase 1 modularization.

Features:
- Auto backend selection (zipfile vs MinimalZipWriter) based on 2GB threshold
- Path traversal prevention
- Configurable compression level
- Progress tracking support
- Multi-file and directory support
"""

import os
import zipfile
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)

# Import dependencies with fallback
try:
    from .minimal_zip_writer import MinimalZipWriter
    from .security import sanitize_path
    from .errors import CompressionError, ValidationError
    from .constants import ZipConstants
    from .compression_utils import calculate_crc32
except ImportError:
    try:
        from Pagonic.core.formats.minimal_zip_writer import MinimalZipWriter
        from Pagonic.core.formats.security import sanitize_path
        from Pagonic.core.formats.errors import CompressionError, ValidationError
        from Pagonic.core.formats.constants import ZipConstants
        from Pagonic.core.formats.compression_utils import calculate_crc32
    except ImportError:
        from minimal_zip_writer import MinimalZipWriter
        from security import sanitize_path
        from errors import CompressionError, ValidationError
        from constants import ZipConstants
        from compression_utils import calculate_crc32


# Constants
GB_THRESHOLD_2GB = 2 * 1024 * 1024 * 1024  # 2GB


class ZipWriter:
    """
    ZIP archive writer with hybrid backend (zipfile vs MinimalZipWriter).

    Features:
    - Auto backend selection (2GB threshold)
    - Path traversal prevention
    - Configurable compression level
    - Progress tracking support

    Example:
        writer = ZipWriter("archive.zip", compression_level=6)
        writer.add_file("document.txt")
        writer.add_directory("photos/")
        writer.finalize()
    """

    def __init__(self, output_path: str, compression_level: int = 6):
        """
        Initialize ZIP writer with backend selection.
        
        Args:
            output_path: Path for output ZIP file
            compression_level: Compression level (1-9, default 6)
        """
        self.output = Path(output_path)
        self.level = self._normalize_compression_level(compression_level)
        self.files_to_add: List[tuple] = []  # (file_path, arcname, size)
        self._data_to_add: List[tuple] = []  # (arcname, data)
        self._backend = None
        self._finalized = False

    @staticmethod
    def _normalize_compression_level(level: int) -> int:
        """Normalize compression level to the zlib-supported 0-9 range."""
        try:
            normalized = int(level)
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"Invalid compression level: {level}") from exc

        return max(0, min(9, normalized))
        
    def add_file(self, file_path: str, arcname: Optional[str] = None) -> None:
        """
        Add file with path sanitization.
        
        Args:
            file_path: Path to file to add
            arcname: Archive name (optional, defaults to basename)
            
        Raises:
            FileNotFoundError: If file does not exist
            ValidationError: If already finalized
        """
        if self._finalized:
            raise ValidationError("Cannot add files after finalization")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Security: sanitize arcname
        safe_arcname = sanitize_path(arcname or os.path.basename(file_path))
        file_size = os.path.getsize(file_path)
        
        self.files_to_add.append((file_path, safe_arcname, file_size))
        logger.debug("Queued file: %s as %s (%d bytes)", file_path, safe_arcname, file_size)

    def add_directory(self, dir_path: str, arcname_prefix: str = "") -> None:
        """
        Add directory recursively.
        
        Args:
            dir_path: Path to directory to add
            arcname_prefix: Prefix for archive names
            
        Raises:
            FileNotFoundError: If directory does not exist
        """
        if not os.path.exists(dir_path):
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        
        if not os.path.isdir(dir_path):
            raise ValidationError(f"Not a directory: {dir_path}")
        
        for root, dirs, files in os.walk(dir_path):
            # Calculate relative path
            rel_root = os.path.relpath(root, dir_path)
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Build archive name with prefix
                if rel_root == ".":
                    arcname = file
                else:
                    arcname = os.path.join(rel_root, file)
                
                if arcname_prefix:
                    arcname = os.path.join(arcname_prefix, arcname)
                
                # Normalize path separators
                arcname = arcname.replace("\\", "/")
                
                self.add_file(file_path, arcname)

    def add_data(self, arcname: str, data: bytes) -> None:
        """
        Add raw data as file.
        
        Args:
            arcname: Filename in archive
            data: Raw bytes to add
        """
        if self._finalized:
            raise ValidationError("Cannot add data after finalization")
        
        safe_arcname = sanitize_path(arcname)
        self._data_to_add.append((safe_arcname, data))
        logger.debug("Queued data: %s (%d bytes)", safe_arcname, len(data))

    def finalize(self, progress_callback: Optional[Callable[[int, int], None]] = None) -> Dict[str, Any]:
        """
        Finalize archive and select backend.
        
        Args:
            progress_callback: Optional callback(current, total) for progress
            
        Returns:
            Dict with compression statistics
        """
        if self._finalized:
            raise ValidationError("Archive already finalized")
        
        # Calculate total size
        total_file_size = sum(size for _, _, size in self.files_to_add)
        total_data_size = sum(len(data) for _, data in self._data_to_add)
        total_size = total_file_size + total_data_size
        
        logger.info("Finalizing archive: %d files, %.2f MB total",
                   len(self.files_to_add) + len(self._data_to_add),
                   total_size / (1024 * 1024))
        
        # Select and use backend
        stats = self._write_with_backend(total_size, progress_callback)
        
        self._finalized = True
        return stats

    def _write_with_backend(self, total_size: int, 
                            progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Write files using appropriate backend.
        
        For files >= 2GB, uses MinimalZipWriter.
        For smaller files, uses standard zipfile.
        """
        # Check for large files
        has_large_files = any(size >= GB_THRESHOLD_2GB for _, _, size in self.files_to_add)
        
        stats = {
            'backend': 'unknown',
            'files_processed': 0,
            'total_compressed_size': 0,
            'total_uncompressed_size': total_size,
            'compression_ratio': 0.0
        }
        
        processed = 0
        total_items = len(self.files_to_add) + len(self._data_to_add)
        
        try:
            if has_large_files and len(self.files_to_add) == 1:
                # Single large file - use MinimalZipWriter
                stats['backend'] = 'MinimalZipWriter'
                file_path, arcname, _ = self.files_to_add[0]
                
                writer = MinimalZipWriter(compression_level=self.level)
                result = writer.compress_file_streaming(file_path, str(self.output))
                
                stats['files_processed'] = 1
                stats['total_compressed_size'] = result.get('compressed_size', 0)
                
            else:
                # Standard zipfile for all other cases
                stats['backend'] = 'zipfile'
                
                # Separate large and small files
                large_files = [(p, a, s) for p, a, s in self.files_to_add if s >= GB_THRESHOLD_2GB]
                small_files = [(p, a, s) for p, a, s in self.files_to_add if s < GB_THRESHOLD_2GB]
                
                # Process large files first with MinimalZipWriter if any
                for file_path, arcname, size in large_files:
                    logger.info("Processing large file with MinimalZipWriter: %s", arcname)
                    writer = MinimalZipWriter(compression_level=self.level)
                    writer.compress_file_streaming(file_path, str(self.output))
                    processed += 1
                    if progress_callback:
                        progress_callback(processed, total_items)
                
                # Process small files with zipfile
                if small_files or self._data_to_add:
                    mode = 'a' if large_files else 'w'
                    with zipfile.ZipFile(str(self.output), mode, 
                                        zipfile.ZIP_DEFLATED, 
                                        allowZip64=True,  # Enable ZIP64 for >4GB files
                                        compresslevel=self.level) as zipf:
                        
                        # Add files
                        for file_path, arcname, size in small_files:
                            zipf.write(file_path, arcname)
                            processed += 1
                            if progress_callback:
                                progress_callback(processed, total_items)
                            logger.debug("Added to archive: %s", arcname)
                        
                        # Add raw data
                        for arcname, data in self._data_to_add:
                            zipf.writestr(arcname, data)
                            processed += 1
                            if progress_callback:
                                progress_callback(processed, total_items)
                
                stats['files_processed'] = processed
            
            # Get final compressed size
            if self.output.exists():
                stats['total_compressed_size'] = self.output.stat().st_size
                if stats['total_uncompressed_size'] > 0:
                    stats['compression_ratio'] = (
                        stats['total_compressed_size'] / stats['total_uncompressed_size']
                    )
            
            logger.info("Archive created: %s (%.2f MB, ratio: %.2f)",
                       self.output, 
                       stats['total_compressed_size'] / (1024 * 1024),
                       stats['compression_ratio'])
            
            return stats
            
        except Exception as e:
            raise CompressionError(f"Failed to create archive: {e}")

    def close(self) -> None:
        """Close writer and finalize if not already done."""
        if not self._finalized and (self.files_to_add or self._data_to_add):
            self.finalize()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if not self._finalized and not exc_type:
            self.finalize()
        return False
