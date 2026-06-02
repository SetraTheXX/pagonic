"""
ZipReader - ZIP Archive Decompression Module
============================================
Modular ZIP file reader with security validations.

Features:
- Secure decompression with ZIP bomb protection
- Path traversal prevention
- Hybrid fast-path decompression
- Memory-efficient streaming
"""

import os
import zlib
import logging
import mmap
from pathlib import Path
from typing import List, Dict, Any, Optional, BinaryIO, Callable

logger = logging.getLogger(__name__)

# Import dependencies with fallback
try:
    from .zip_structs import ZipAyrıştırıcı, ZipParseError, CompressionMethods
    from .security import validate_zip_safety, sanitize_path, secure_extract_path, SecurityError
    from .errors import CompressionError, ValidationError
    from .hybrid_decompressor import HybridFastPathDecompressor
    from .compression_utils import calculate_crc32
except ImportError:
    try:
        from Pagonic.core.formats.zip_structs import ZipAyrıştırıcı, ZipParseError, CompressionMethods
        from Pagonic.core.formats.security import validate_zip_safety, sanitize_path, secure_extract_path, SecurityError
        from Pagonic.core.formats.errors import CompressionError, ValidationError
        from Pagonic.core.formats.hybrid_decompressor import HybridFastPathDecompressor
        from Pagonic.core.formats.compression_utils import calculate_crc32
    except ImportError:
        from zip_structs import ZipAyrıştırıcı, ZipParseError, CompressionMethods
        from security import validate_zip_safety, sanitize_path, secure_extract_path, SecurityError
        from errors import CompressionError, ValidationError
        from hybrid_decompressor import HybridFastPathDecompressor
        from compression_utils import calculate_crc32


class ZipReader:
    """
    ZIP archive reader with security validations.

    Features:
    - Secure decompression with ZIP bomb protection
    - Path traversal prevention  
    - Hybrid fast-path decompression
    - Memory-efficient streaming

    Example:
        reader = ZipReader("archive.zip")
        files = reader.list_files()
        reader.extract_all("output/")
    """

    def __init__(self, zip_path: str):
        """
        Initialize ZIP reader with security checks.
        
        Args:
            zip_path: Path to ZIP archive
            
        Raises:
            FileNotFoundError: If ZIP file does not exist
            SecurityError: If ZIP fails security validation
        """
        self.path = Path(zip_path)
        if not self.path.exists():
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")
        
        # Security validation - ZIP bomb protection
        validate_zip_safety(self.path)
        
        # Initialize hybrid decompressor for fast-path decompression
        self._hybrid_decompressor = HybridFastPathDecompressor()
        
        # Cache for parsed entries
        self._entries_cache = None
        self._eocd_cache = None

    def list_files(self) -> List[str]:
        """
        List all files in archive.
        
        Returns:
            List[str]: List of file paths in archive
        """
        entries = self._get_entries()
        return [entry.filename for entry in entries]

    def inspect(self):
        """Return a structured safety inspection report for this archive."""
        try:
            from .inspection import inspect_archive
        except ImportError:
            from Pagonic.core.formats.inspection import inspect_archive

        return inspect_archive(self.path)

    def get_file_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific file.
        
        Args:
            filename: Name of file in archive
            
        Returns:
            Dict with file metadata or None if not found
        """
        entries = self._get_entries()
        for entry in entries:
            if entry.filename == filename:
                return {
                    'filename': entry.filename,
                    'compressed_size': entry.compressed_size,
                    'uncompressed_size': entry.uncompressed_size,
                    'compression_method': entry.compression_method,
                    'crc32': entry.crc32
                }
        return None

    def extract_file(self, filename: str, output_dir: str) -> str:
        """
        Extract single file with path sanitization.
        
        Args:
            filename: Name of file to extract
            output_dir: Directory to extract to
            
        Returns:
            str: Path to extracted file
            
        Raises:
            FileNotFoundError: If file not in archive
            CompressionError: If extraction fails
        """
        entries = self._get_entries()
        target_entry = None
        
        for entry in entries:
            if entry.filename == filename:
                target_entry = entry
                break
        
        if target_entry is None:
            raise FileNotFoundError(f"File not found in archive: {filename}")
        
        # Security: sanitize output path
        safe_filename = sanitize_path(filename)
        output_path = os.path.join(output_dir, safe_filename)
        
        # Create output directory
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Extract the file
        with open(str(self.path), 'rb') as zip_file:
            parser = ZipAyrıştırıcı(zip_file)
            local_header = parser.parse_local_file_header(target_entry)
            self._decompress_entry(zip_file, target_entry, local_header, output_dir)
        
        return output_path

    def extract_all(self, output_dir: str, use_mmap: bool = False,
                    progress_callback: Optional[Callable[[int, int, str], None]] = None) -> Dict[str, Any]:
        """
        Extract all files with security checks and progress tracking.
        
        Args:
            output_dir: Directory to extract to
            use_mmap: Use memory-mapped extraction for large files
            progress_callback: Optional callback(current, total, filename) for progress tracking.
                              Called after each file is extracted.
            
        Returns:
            Dict with extraction results
            
        Example:
            def on_progress(current, total, filename):
                print(f"Extracting {current}/{total}: {filename}")
            
            reader.extract_all("output/", progress_callback=on_progress)
        """
        results = {
            "total_entries": 0,
            "success": [],
            "failed": []
        }
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        with open(str(self.path), 'rb') as zip_file:
            file_size = os.fstat(zip_file.fileno()).st_size
            parser = ZipAyrıştırıcı(zip_file)
            entries = self._get_entries()
            results["total_entries"] = len(entries)
            total_entries = len(entries)
            
            mm = None
            try:
                # Use mmap for large files (>100MB)
                if use_mmap or file_size > 100 * 1024 * 1024:
                    try:
                        mm = mmap.mmap(zip_file.fileno(), 0, access=mmap.ACCESS_READ)
                    except Exception as e:
                        logger.warning("Failed to create mmap, falling back to standard IO: %s", e)
                
                for i, entry in enumerate(entries):
                    try:
                        local_header = parser.parse_local_file_header(entry)
                        
                        if mm is not None:
                            self._decompress_entry_mmap(mm, entry, local_header, output_dir)
                        else:
                            self._decompress_entry(zip_file, entry, local_header, output_dir)
                        
                        results["success"].append(entry.filename)
                        
                        # Progress callback - called after successful extraction
                        if progress_callback:
                            progress_callback(i + 1, total_entries, entry.filename)
                        
                    except Exception as e:
                        results["failed"].append({
                            "filename": entry.filename,
                            "error": str(e)
                        })
                        logger.error("Failed to extract %s: %s", entry.filename, e)
                        
                        # Progress callback - still advance even on failure
                        if progress_callback:
                            progress_callback(i + 1, total_entries, entry.filename)
                        
            finally:
                if mm:
                    try:
                        mm.close()
                    except Exception:
                        pass
        
        return results

    def read_file(self, filename: str) -> bytes:
        """
        Read file content without extraction to disk.
        
        Args:
            filename: Name of file in archive
            
        Returns:
            bytes: Decompressed file content
            
        Raises:
            FileNotFoundError: If file not in archive
        """
        entries = self._get_entries()
        target_entry = None
        
        for entry in entries:
            if entry.filename == filename:
                target_entry = entry
                break
        
        if target_entry is None:
            raise FileNotFoundError(f"File not found in archive: {filename}")
        
        with open(str(self.path), 'rb') as zip_file:
            parser = ZipAyrıştırıcı(zip_file)
            local_header = parser.parse_local_file_header(target_entry)
            
            # Read compressed data
            zip_file.seek(local_header.data_offset)
            compressed_data = zip_file.read(target_entry.compressed_size)
            
            # Decompress
            return self._decompress_data(compressed_data, target_entry)

    def _get_entries(self) -> List:
        """Get or cache CD entries."""
        if self._entries_cache is not None:
            return self._entries_cache
        
        with open(str(self.path), 'rb') as zip_file:
            parser = ZipAyrıştırıcı(zip_file)
            eocd = parser.find_eocd()
            self._eocd_cache = eocd
            self._entries_cache = parser.parse_cd_entries(eocd)
        
        return self._entries_cache

    def _decompress_entry(self, zip_file: BinaryIO, cd_entry, local_header, target_dir: str) -> None:
        """Decompress single entry to disk."""
        # Skip unsupported methods
        if not CompressionMethods.is_supported(cd_entry.compression_method):
            logger.warning("Skipping %s: unsupported compression method %d", 
                          cd_entry.filename, cd_entry.compression_method)
            return
        
        # Security: use secure path extraction to prevent Zip Slip
        try:
            output_path = secure_extract_path(cd_entry.filename, target_dir)
        except SecurityError as e:
            logger.warning("Blocked path traversal attempt: %s", e)
            return
        
        # Handle directories
        if cd_entry.filename.endswith('/'):
            os.makedirs(output_path, exist_ok=True)
            return
        
        # Create parent directories
        parent_dir = os.path.dirname(output_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        
        # Read compressed data
        zip_file.seek(local_header.data_offset)
        compressed_data = zip_file.read(cd_entry.compressed_size)
        
        # Decompress
        decompressed_data = self._decompress_data(compressed_data, cd_entry)
        
        # Write to file
        with open(output_path, 'wb') as f:
            f.write(decompressed_data)
        
        logger.debug("Extracted: %s (%d -> %d bytes)", 
                    cd_entry.filename, cd_entry.compressed_size, cd_entry.uncompressed_size)

    def _decompress_entry_mmap(self, mm, cd_entry, local_header, target_dir: str) -> None:
        """Decompress entry using memory-mapped file."""
        # Skip unsupported methods
        if not CompressionMethods.is_supported(cd_entry.compression_method):
            logger.warning("Skipping %s: unsupported compression method %d", 
                          cd_entry.filename, cd_entry.compression_method)
            return
        
        # Security: use secure path extraction to prevent Zip Slip
        try:
            output_path = secure_extract_path(cd_entry.filename, target_dir)
        except SecurityError as e:
            logger.warning("Blocked path traversal attempt: %s", e)
            return
        
        # Handle directories
        if cd_entry.filename.endswith('/'):
            os.makedirs(output_path, exist_ok=True)
            return
        
        # Create parent directories
        parent_dir = os.path.dirname(output_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        
        # Read compressed data from mmap
        compressed_data = mm[local_header.data_offset:local_header.data_offset + cd_entry.compressed_size]
        
        # Decompress
        decompressed_data = self._decompress_data(compressed_data, cd_entry)
        
        # Write to file
        with open(output_path, 'wb') as f:
            f.write(decompressed_data)

    def _decompress_data(self, compressed_data: bytes, entry) -> bytes:
        """Decompress data based on compression method."""
        if entry.compression_method == CompressionMethods.STORE:
            decompressed_data = compressed_data
            
        elif entry.compression_method == CompressionMethods.DEFLATE:
            try:
                # Use hybrid decompressor for fast-path
                decompressed_data = self._hybrid_decompressor.decompress_data(
                    compressed_data=compressed_data,
                    filename=entry.filename,
                    uncompressed_size=entry.uncompressed_size
                )
            except Exception as e:
                # Fallback to standard zlib
                logger.debug("Hybrid failed, using zlib fallback: %s", e)
                decompressor = zlib.decompressobj(-15)
                decompressed_data = decompressor.decompress(compressed_data)
                decompressed_data += decompressor.flush()
        else:
            raise CompressionError(f"Unsupported compression method: {entry.compression_method}")
        
        # Validate size
        if len(decompressed_data) != entry.uncompressed_size:
            raise CompressionError(
                f"Size mismatch for {entry.filename}: "
                f"expected {entry.uncompressed_size}, got {len(decompressed_data)}"
            )
        
        # Validate CRC32
        calculated_crc = calculate_crc32(decompressed_data) & 0xffffffff
        if calculated_crc != entry.crc32:
            raise CompressionError(
                f"CRC32 mismatch for {entry.filename}: "
                f"expected 0x{entry.crc32:08x}, got 0x{calculated_crc:08x}"
            )
        
        return decompressed_data

    def get_archive_info(self) -> Dict[str, Any]:
        """Get archive metadata summary."""
        entries = self._get_entries()
        total_compressed = sum(e.compressed_size for e in entries)
        total_uncompressed = sum(e.uncompressed_size for e in entries)
        
        return {
            'path': str(self.path),
            'file_count': len(entries),
            'total_compressed_size': total_compressed,
            'total_uncompressed_size': total_uncompressed,
            'compression_ratio': total_compressed / total_uncompressed if total_uncompressed > 0 else 0
        }
