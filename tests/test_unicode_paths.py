"""
Unicode and Path Handling Tests
================================
Tests for UTF-8 filename encoding and cross-platform path normalization.

"""

import os
import sys
import tempfile
from pathlib import Path

# Add parent for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


class TestFilenameEncoding:
    """Test Unicode filename encoding and decoding functions."""
    
    def test_encode_filename_ascii(self):
        """Test encoding ASCII filename"""
        from Pagonic.core.formats.zip_structs import encode_filename
        
        encoded, flags = encode_filename("test.txt")
        assert encoded == b"test.txt"
        assert flags == 0x800  # Bit 11 set
    
    def test_encode_filename_unicode(self):
        """Test encoding Unicode filename"""
        from Pagonic.core.formats.zip_structs import encode_filename
        
        encoded, flags = encode_filename("文件.txt")
        assert encoded == "文件.txt".encode('utf-8')
        assert flags == 0x800
    
    def test_encode_filename_emoji(self):
        """Test encoding emoji filename"""
        from Pagonic.core.formats.zip_structs import encode_filename
        
        encoded, flags = encode_filename("🎉_party.txt")
        assert encoded == "🎉_party.txt".encode('utf-8')
        assert flags == 0x800
    
    def test_decode_filename_utf8(self):
        """Test decoding UTF-8 with Bit 11 flag"""
        from Pagonic.core.formats.zip_structs import decode_filename
        
        data = "文件.txt".encode('utf-8')
        result = decode_filename(data, 0x800)  # Bit 11 set
        assert result == "文件.txt"
    
    def test_decode_filename_legacy_utf8(self):
        """Test decoding UTF-8 without Bit 11 (fallback)"""
        from Pagonic.core.formats.zip_structs import decode_filename
        
        data = "test.txt".encode('utf-8')
        result = decode_filename(data, 0)  # No Bit 11
        assert result == "test.txt"
    
    def test_decode_filename_cp437(self):
        """Test decoding CP437 (DOS encoding)"""
        from Pagonic.core.formats.zip_structs import decode_filename
        
        # CP437 encoded filename
        data = b"test\x80.txt"  # \x80 = Ç in CP437
        result = decode_filename(data, 0)  # No Bit 11
        # Should fallback to CP437 since UTF-8 fails
        assert "test" in result
        assert ".txt" in result


class TestPagonicPathPolicy:
    """Test path normalization and safety checks."""
    
    def test_normalize_windows_path(self):
        """Test Windows path normalization"""
        from Pagonic.core.utils.path_utils import PagonicPathPolicy
        
        result = PagonicPathPolicy.normalize("C:\\Users\\test\\file.txt")
        assert result == "Users/test/file.txt"
    
    def test_normalize_linux_path(self):
        """Test Linux absolute path normalization"""
        from Pagonic.core.utils.path_utils import PagonicPathPolicy
        
        result = PagonicPathPolicy.normalize("/home/user/file.txt")
        assert result == "home/user/file.txt"
    
    def test_normalize_traversal(self):
        """Test directory traversal removal"""
        from Pagonic.core.utils.path_utils import PagonicPathPolicy
        
        result = PagonicPathPolicy.normalize("../../../etc/passwd")
        assert result == "etc/passwd"
        assert ".." not in result
    
    def test_normalize_mixed(self):
        """Test mixed separators"""
        from Pagonic.core.utils.path_utils import PagonicPathPolicy
        
        result = PagonicPathPolicy.normalize("folder\\subfolder/file.txt")
        assert result == "folder/subfolder/file.txt"
    
    def test_is_safe_path_valid(self):
        """Test safe path detection"""
        from Pagonic.core.utils.path_utils import PagonicPathPolicy
        
        with tempfile.TemporaryDirectory() as tmpdir:
            assert PagonicPathPolicy.is_safe_path("subdir/file.txt", tmpdir)
    
    def test_is_safe_path_traversal(self):
        """Test traversal attack detection"""
        from Pagonic.core.utils.path_utils import PagonicPathPolicy
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # This would escape the target directory
            assert not PagonicPathPolicy.is_safe_path("../../../etc/passwd", tmpdir)
    
    def test_join_archive_path(self):
        """Test archive path joining"""
        from Pagonic.core.utils.path_utils import PagonicPathPolicy
        
        result = PagonicPathPolicy.join_archive_path("folder", "subfolder", "file.txt")
        assert result == "folder/subfolder/file.txt"


class TestUnicodeFilenameEndToEnd:
    """End-to-end tests for Unicode filename support."""
    
    def test_unicode_filename_roundtrip(self):
        """Test writing and reading Unicode filenames"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        from Pagonic.core.formats.zip_reader import ZipReader
        
        filenames = [
            "test_文件.txt",           # Chinese
            "тест_файл.txt",           # Russian
            "テスト.txt",              # Japanese
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for filename in filenames:
                zip_path = Path(tmpdir) / "unicode_test.zip"
                
                # Write
                writer = ZipWriter(str(zip_path))
                writer.add_data(filename, b"test content")
                writer.finalize()
                
                # Read
                reader = ZipReader(str(zip_path))
                files = reader.list_files()
                
                # Verify filename is preserved
                assert filename in files, f"Failed for: {filename}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
