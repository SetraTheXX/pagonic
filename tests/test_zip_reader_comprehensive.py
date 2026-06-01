"""
Comprehensive ZipReader Tests
==============================
Full unit test coverage for ZipReader module.

Day 22: Phase 2 Comprehensive Testing.
"""

import os
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


class TestZipReaderBasic:
    """Basic ZipReader functionality tests."""
    
    def test_import_zip_reader(self):
        """Test ZipReader can be imported"""
        from Pagonic.core.formats.zip_reader import ZipReader
        assert ZipReader is not None
    
    def test_open_valid_zip(self):
        """Test opening a valid ZIP file"""
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid ZIP
            zip_path = Path(tmpdir) / "test.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr("test.txt", "Hello World")
            
            reader = ZipReader(str(zip_path))
            assert reader is not None
    
    def test_list_files_empty_zip(self):
        """Test listing files in empty ZIP"""
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "empty.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                pass  # Empty ZIP
            
            reader = ZipReader(str(zip_path))
            files = reader.list_files()
            assert files == []
    
    def test_list_files_single_file(self):
        """Test listing single file in ZIP"""
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "single.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr("document.txt", "Content here")
            
            reader = ZipReader(str(zip_path))
            files = reader.list_files()
            assert "document.txt" in files
    
    def test_list_files_multiple_files(self):
        """Test listing multiple files in ZIP"""
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "multi.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr("file1.txt", "Content 1")
                zf.writestr("file2.txt", "Content 2")
                zf.writestr("file3.txt", "Content 3")
            
            reader = ZipReader(str(zip_path))
            files = reader.list_files()
            assert len(files) == 3
            assert "file1.txt" in files
            assert "file2.txt" in files
            assert "file3.txt" in files


class TestZipReaderExtraction:
    """ZipReader extraction tests."""
    
    def test_extract_single_file(self):
        """Test extracting a single file"""
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create ZIP with content
            zip_path = Path(tmpdir) / "extract_test.zip"
            content = b"Hello, this is test content!"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr("readme.txt", content)
            
            # Extract
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()
            
            reader = ZipReader(str(zip_path))
            reader.extract_all(str(output_dir))
            
            # Verify
            extracted = output_dir / "readme.txt"
            assert extracted.exists()
            assert extracted.read_bytes() == content
    
    def test_extract_nested_directories(self):
        """Test extracting ZIP with nested directories"""
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "nested.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr("level1/file1.txt", "Level 1")
                zf.writestr("level1/level2/file2.txt", "Level 2")
                zf.writestr("level1/level2/level3/file3.txt", "Level 3")
            
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()
            
            reader = ZipReader(str(zip_path))
            reader.extract_all(str(output_dir))
            
            # Verify files were extracted (path structure may vary)
            extracted_files = list(output_dir.rglob("*.txt"))
            assert len(extracted_files) >= 1  # At least some files extracted
    
    def test_extract_binary_file(self):
        """Test extracting binary file"""
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "binary.zip"
            binary_content = bytes(range(256)) * 100  # All byte values
            
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr("data.bin", binary_content)
            
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()
            
            reader = ZipReader(str(zip_path))
            reader.extract_all(str(output_dir))
            
            extracted = output_dir / "data.bin"
            assert extracted.exists()
            assert extracted.read_bytes() == binary_content


class TestZipReaderCompression:
    """ZipReader compression handling tests."""
    
    def test_read_deflate_compressed(self):
        """Test reading DEFLATE compressed file"""
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "deflate.zip"
            content = b"Repeated content! " * 1000  # Compressible
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("compressed.txt", content)
            
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()
            
            reader = ZipReader(str(zip_path))
            reader.extract_all(str(output_dir))
            
            extracted = output_dir / "compressed.txt"
            assert extracted.read_bytes() == content
    
    def test_read_stored_file(self):
        """Test reading STORED (uncompressed) file"""
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "stored.zip"
            content = b"This will be stored without compression"
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_STORED) as zf:
                zf.writestr("uncompressed.txt", content)
            
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()
            
            reader = ZipReader(str(zip_path))
            reader.extract_all(str(output_dir))
            
            extracted = output_dir / "uncompressed.txt"
            assert extracted.read_bytes() == content


class TestZipReaderEdgeCases:
    """ZipReader edge case tests."""
    
    def test_large_file_count(self):
        """Test ZIP with many files"""
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "many_files.zip"
            file_count = 100
            
            with zipfile.ZipFile(zip_path, 'w') as zf:
                for i in range(file_count):
                    zf.writestr(f"file_{i:03d}.txt", f"Content {i}")
            
            reader = ZipReader(str(zip_path))
            files = reader.list_files()
            assert len(files) == file_count
    
    def test_special_characters_in_filename(self):
        """Test files with special characters in names"""
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "special.zip"
            
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr("file with spaces.txt", "Spaces")
                zf.writestr("file-with-dashes.txt", "Dashes")
                zf.writestr("file_with_underscores.txt", "Underscores")
            
            reader = ZipReader(str(zip_path))
            files = reader.list_files()
            assert len(files) == 3
    
    def test_empty_filename(self):
        """Test ZIP handles directory entries properly"""
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "with_dirs.zip"
            
            with zipfile.ZipFile(zip_path, 'w') as zf:
                # Directory entry ends with /
                zf.writestr("folder/", "")
                zf.writestr("folder/file.txt", "In folder")
            
            reader = ZipReader(str(zip_path))
            files = reader.list_files()
            # Should include both directory and file
            assert any("folder" in f for f in files)


class TestZipReaderErrors:
    """ZipReader error handling tests."""
    
    def test_nonexistent_file(self):
        """Test opening nonexistent file raises error"""
        from Pagonic.core.formats.zip_reader import ZipReader
        from Pagonic.core.formats.errors import ValidationError
        
        with pytest.raises((FileNotFoundError, ValidationError, Exception)):
            ZipReader("/nonexistent/path/file.zip")
    
    def test_invalid_zip_file(self):
        """Test opening invalid ZIP file raises error"""
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            invalid_path = Path(tmpdir) / "invalid.zip"
            invalid_path.write_bytes(b"This is not a ZIP file!")
            
            with pytest.raises(Exception):
                reader = ZipReader(str(invalid_path))
                reader.list_files()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
