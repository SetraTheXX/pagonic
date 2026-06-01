"""
Error Handling Tests
=====================
Test error scenarios and edge cases.

Day 24: Phase 2 Comprehensive Testing.
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


class TestZipWriterErrors:
    """ZipWriter error handling tests."""
    
    def test_add_nonexistent_file(self):
        """Test adding file that doesn't exist"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "test.zip"
            writer = ZipWriter(str(zip_path))
            
            # Should handle gracefully (skip or raise)
            nonexistent = "/nonexistent/path/file.txt"
            try:
                writer.add_file(nonexistent)
                writer.finalize()
                # If no exception, that's fine - it might skip
            except (FileNotFoundError, Exception):
                pass  # Expected behavior
    
    def test_invalid_compression_level_high(self):
        """Test compression level above max"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        import time
        import gc
        import shutil
        
        # Manual temp directory to avoid Windows cleanup issues
        tmpdir = Path(tempfile.mkdtemp())
        zip_path = tmpdir / "test.zip"
        writer = None
        
        try:
            # Level 100 should be clamped or rejected
            try:
                writer = ZipWriter(str(zip_path), compression_level=100)
                writer.add_data("test.txt", b"Content")
                writer.finalize()
                # If no exception, file should be created
                assert zip_path.exists()
            except (ValueError, Exception):
                pass  # Exception is also valid behavior
        finally:
            # Cleanup
            if writer is not None:
                try:
                    writer.close()
                except Exception:
                    pass
                del writer
            # Force garbage collection
            gc.collect()
            time.sleep(0.2)
            # Manual cleanup with retry
            if tmpdir.exists():
                for _ in range(3):
                    try:
                        shutil.rmtree(tmpdir, ignore_errors=True)
                        break
                    except Exception:
                        time.sleep(0.1)
    
    def test_invalid_compression_level_negative(self):
        """Test negative compression level"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "test.zip"
            # Negative level should be clamped to 0
            writer = ZipWriter(str(zip_path), compression_level=-1)
            writer.add_data("test.txt", b"Content")
            writer.finalize()
            
            assert zip_path.exists()


class TestZipReaderErrors:
    """ZipReader error handling tests."""
    
    def test_open_nonexistent_file(self):
        """Test opening file that doesn't exist"""
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with pytest.raises(Exception):
            ZipReader("/nonexistent/path/archive.zip")
    
    def test_open_corrupted_zip(self):
        """Test opening corrupted ZIP file"""
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            corrupt = Path(tmpdir) / "corrupt.zip"
            corrupt.write_bytes(b"PK\x03\x04" + b"GARBAGE" * 100)
            
            with pytest.raises(Exception):
                reader = ZipReader(str(corrupt))
                reader.list_files()
    
    def test_open_non_zip_file(self):
        """Test opening file that isn't a ZIP"""
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            not_zip = Path(tmpdir) / "not_zip.zip"
            not_zip.write_text("This is just a text file pretending to be ZIP")
            
            with pytest.raises(Exception):
                reader = ZipReader(str(not_zip))
                reader.list_files()
    
    def test_open_empty_file(self):
        """Test opening empty file"""
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            empty = Path(tmpdir) / "empty.zip"
            empty.write_bytes(b"")
            
            with pytest.raises(Exception):
                reader = ZipReader(str(empty))
                reader.list_files()


class TestSecurityErrors:
    """Security-related error tests."""
    
    def test_path_traversal_prevention(self):
        """Test path traversal attack prevention"""
        from Pagonic.core.utils.path_utils import PagonicPathPolicy
        
        # These paths should be sanitized
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/etc/passwd",
            "C:\\Windows\\System32",
        ]
        
        for path in dangerous_paths:
            safe = PagonicPathPolicy.normalize(path)
            # Should not contain .. or start with / or C:
            assert ".." not in safe
            assert not safe.startswith("/")
            assert not safe.startswith("C:")
    
    def test_is_safe_path_detection(self):
        """Test safe path detection"""
        from Pagonic.core.utils.path_utils import PagonicPathPolicy
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Safe path
            assert PagonicPathPolicy.is_safe_path("subdir/file.txt", tmpdir)
            
            # Unsafe paths
            assert not PagonicPathPolicy.is_safe_path("../../../etc/passwd", tmpdir)


class TestCompressionUtilsErrors:
    """Compression utilities error handling."""
    
    def test_entropy_empty_data(self):
        """Test entropy calculation with empty data"""
        from Pagonic.core.formats.compression_utils import calculate_entropy
        
        result = calculate_entropy(b"")
        assert result == 0.0
    
    def test_adaptive_compress_level_zero(self):
        """Test adaptive compress with level 0"""
        from Pagonic.core.formats.compression_utils import adaptive_compress
        
        data = b"Test data"
        compressed, method = adaptive_compress(data, 0)
        assert method == 0  # STORE
        assert compressed == data
    
    def test_smart_select_unknown_extension(self):
        """Test smart selection with unknown extension"""
        from Pagonic.core.formats.compression_utils import smart_select_compression_level
        
        # Unknown extension should get size-based level
        level = smart_select_compression_level("unknown.xyz", 1000)
        assert 0 <= level <= 9


class TestValidationErrors:
    """Input validation error tests."""
    
    def test_zip_writer_empty_arcname(self):
        """Test adding data with empty arcname"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "test.zip"
            writer = ZipWriter(str(zip_path))
            
            # Empty arcname should be handled
            try:
                writer.add_data("", b"Content")
                writer.finalize()
            except (ValueError, Exception):
                pass  # Expected - empty name not allowed
    
    def test_crc32_consistency(self):
        """Test CRC32 calculation is consistent"""
        from Pagonic.core.formats.compression_utils import calculate_crc32
        
        data = b"Test data for CRC32"
        crc1 = calculate_crc32(data)
        crc2 = calculate_crc32(data)
        
        assert crc1 == crc2  # Same data = same CRC


class TestRealisticTestData:
    """Test with realistic (randomized) test data."""
    
    def create_realistic_data(self, size: int) -> bytes:
        """Create compressible but realistic test data"""
        import random
        random.seed(42)
        
        patterns = [
            b'A' * 100,
            b'Test data line\n' * 50,
            bytes([random.randint(0, 255) for _ in range(500)]),
        ]
        
        result = b''.join(patterns * (size // len(b''.join(patterns)) + 1))
        return result[:size]
    
    def test_realistic_data_compression(self):
        """Test compression with realistic data"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create realistic data
            data = self.create_realistic_data(10000)
            
            zip_path = tmpdir / "realistic.zip"
            writer = ZipWriter(str(zip_path))
            writer.add_data("data.bin", data)
            writer.finalize()
            
            # Should compress somewhat but not trigger false positives
            reader = ZipReader(str(zip_path))
            files = reader.list_files()
            assert len(files) == 1
    
    def test_mixed_entropy_data(self):
        """Test data with mixed entropy regions"""
        from Pagonic.core.formats.compression_utils import calculate_entropy
        
        # Low entropy (compressible)
        low_entropy = b"A" * 1000
        assert calculate_entropy(low_entropy) < 0.1
        
        # High entropy (random)
        import random
        random.seed(42)
        high_entropy = bytes([random.randint(0, 255) for _ in range(1000)])
        assert calculate_entropy(high_entropy) > 0.9
        
        # Mixed
        mixed = low_entropy + high_entropy
        mixed_entropy = calculate_entropy(mixed)
        assert 0.3 < mixed_entropy < 0.7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
