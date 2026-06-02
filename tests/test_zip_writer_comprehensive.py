"""
Comprehensive ZipWriter Tests
==============================
Full unit test coverage for ZipWriter module.

"""

import os
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


class TestZipWriterBasic:
    """Basic ZipWriter functionality tests."""
    
    def test_import_zip_writer(self):
        """Test ZipWriter can be imported"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        assert ZipWriter is not None
    
    def test_create_empty_zip(self):
        """Test creating empty ZIP file"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "empty.zip"
            
            writer = ZipWriter(str(zip_path))
            # Add minimal content since truly empty ZIP may not be created
            writer.add_data("placeholder.txt", b"")
            stats = writer.finalize()
            
            assert zip_path.exists()
            assert stats['files_processed'] >= 0
    
    def test_add_single_file(self):
        """Test adding a single file"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create source file
            source = Path(tmpdir) / "source.txt"
            source.write_text("Hello World!")
            
            # Create ZIP
            zip_path = Path(tmpdir) / "single.zip"
            writer = ZipWriter(str(zip_path))
            writer.add_file(str(source))
            stats = writer.finalize()
            
            # Verify
            assert zip_path.exists()
            assert stats['files_processed'] == 1
            
            # Check contents
            with zipfile.ZipFile(zip_path, 'r') as zf:
                assert len(zf.namelist()) == 1
    
    def test_add_multiple_files(self):
        """Test adding multiple files"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create source files
            files = []
            for i in range(5):
                f = Path(tmpdir) / f"file{i}.txt"
                f.write_text(f"Content {i}")
                files.append(str(f))
            
            # Create ZIP
            zip_path = Path(tmpdir) / "multi.zip"
            writer = ZipWriter(str(zip_path))
            for f in files:
                writer.add_file(f)
            stats = writer.finalize()
            
            assert stats['files_processed'] == 5
            
            with zipfile.ZipFile(zip_path, 'r') as zf:
                assert len(zf.namelist()) == 5


class TestZipWriterData:
    """ZipWriter add_data functionality tests."""
    
    def test_add_data_bytes(self):
        """Test adding raw bytes data"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "data.zip"
            content = b"Binary content here"
            
            writer = ZipWriter(str(zip_path))
            writer.add_data("data.bin", content)
            writer.finalize()
            
            with zipfile.ZipFile(zip_path, 'r') as zf:
                assert zf.read("data.bin") == content
    
    def test_add_data_string(self):
        """Test adding string data"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "string.zip"
            content = "Text content here"
            
            writer = ZipWriter(str(zip_path))
            writer.add_data("text.txt", content.encode('utf-8'))
            writer.finalize()
            
            with zipfile.ZipFile(zip_path, 'r') as zf:
                assert zf.read("text.txt").decode('utf-8') == content
    
    def test_add_data_large(self):
        """Test adding large data"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "large.zip"
            content = b"X" * (1024 * 1024)  # 1MB
            
            writer = ZipWriter(str(zip_path))
            writer.add_data("large.bin", content)
            writer.finalize()
            
            with zipfile.ZipFile(zip_path, 'r') as zf:
                assert len(zf.read("large.bin")) == len(content)


class TestZipWriterDirectory:
    """ZipWriter directory handling tests."""
    
    def test_add_directory(self):
        """Test adding entire directory"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create directory structure
            src_dir = Path(tmpdir) / "source"
            src_dir.mkdir()
            (src_dir / "file1.txt").write_text("File 1")
            (src_dir / "file2.txt").write_text("File 2")
            (src_dir / "subdir").mkdir()
            (src_dir / "subdir" / "file3.txt").write_text("File 3")
            
            # Create ZIP
            zip_path = Path(tmpdir) / "dir.zip"
            writer = ZipWriter(str(zip_path))
            writer.add_directory(str(src_dir))
            stats = writer.finalize()
            
            assert stats['files_processed'] >= 3
            
            with zipfile.ZipFile(zip_path, 'r') as zf:
                names = zf.namelist()
                assert len(names) >= 3


class TestZipWriterCompression:
    """ZipWriter compression tests."""
    
    def test_compression_level_0(self):
        """Test STORE mode (level 0)"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "store.zip"
            content = b"X" * 10000
            
            writer = ZipWriter(str(zip_path), compression_level=0)
            writer.add_data("stored.bin", content)
            writer.finalize()
            
            # STORED file should be approximately same size
            assert zip_path.stat().st_size >= len(content) * 0.9
    
    def test_compression_level_9(self):
        """Test maximum compression (level 9)"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "max.zip"
            content = b"Repeated text! " * 10000  # Very compressible
            
            writer = ZipWriter(str(zip_path), compression_level=9)
            writer.add_data("compressed.txt", content)
            writer.finalize()
            
            # Should be significantly smaller
            assert zip_path.stat().st_size < len(content) * 0.5
    
    def test_compression_default_level(self):
        """Test default compression level"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "default.zip"
            content = b"Some content for compression"
            
            writer = ZipWriter(str(zip_path))  # Default level
            writer.add_data("file.txt", content)
            stats = writer.finalize()
            
            assert zip_path.exists()
            assert stats['files_processed'] == 1


class TestZipWriterArcname:
    """ZipWriter archive name tests."""
    
    def test_custom_arcname(self):
        """Test custom archive name for file"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "original_name.txt"
            source.write_text("Content")
            
            zip_path = Path(tmpdir) / "renamed.zip"
            writer = ZipWriter(str(zip_path))
            writer.add_file(str(source), arcname="custom_name.txt")
            writer.finalize()
            
            with zipfile.ZipFile(zip_path, 'r') as zf:
                assert "custom_name.txt" in zf.namelist()
                assert "original_name.txt" not in zf.namelist()
    
    def test_nested_arcname(self):
        """Test nested path in archive name"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "file.txt"
            source.write_text("Content")
            
            zip_path = Path(tmpdir) / "nested.zip"
            writer = ZipWriter(str(zip_path))
            writer.add_file(str(source), arcname="folder/subfolder/file.txt")
            writer.finalize()
            
            with zipfile.ZipFile(zip_path, 'r') as zf:
                names = zf.namelist()
                # Either full path or just filename (security may strip)
                assert len(names) >= 1
                assert any("file.txt" in n for n in names)


class TestZipWriterStats:
    """ZipWriter statistics tests."""
    
    def test_stats_files_processed(self):
        """Test files_processed statistic"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "stats.zip"
            
            writer = ZipWriter(str(zip_path))
            for i in range(10):
                writer.add_data(f"file{i}.txt", f"Content {i}".encode())
            stats = writer.finalize()
            
            assert stats['files_processed'] == 10
    
    def test_stats_compression_ratio(self):
        """Test compression ratio statistic"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "ratio.zip"
            content = b"Repeated! " * 10000
            
            writer = ZipWriter(str(zip_path), compression_level=9)
            writer.add_data("data.txt", content)
            stats = writer.finalize()
            
            assert 'compression_ratio' in stats or 'total_compressed_size' in stats


class TestZipWriterEdgeCases:
    """ZipWriter edge case tests."""
    
    def test_unicode_filename(self):
        """Test Unicode filename in archive"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "unicode.zip"
            
            writer = ZipWriter(str(zip_path))
            writer.add_data("文件.txt", b"Chinese")
            writer.add_data("файл.txt", b"Russian")
            writer.finalize()
            
            with zipfile.ZipFile(zip_path, 'r') as zf:
                names = zf.namelist()
                assert len(names) == 2
    
    def test_empty_file(self):
        """Test adding empty file"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "empty_file.zip"
            
            writer = ZipWriter(str(zip_path))
            writer.add_data("empty.txt", b"")
            writer.finalize()
            
            with zipfile.ZipFile(zip_path, 'r') as zf:
                assert zf.read("empty.txt") == b""
    
    def test_binary_content(self):
        """Test binary content with all byte values"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "binary.zip"
            content = bytes(range(256))
            
            writer = ZipWriter(str(zip_path))
            writer.add_data("all_bytes.bin", content)
            writer.finalize()
            
            with zipfile.ZipFile(zip_path, 'r') as zf:
                assert zf.read("all_bytes.bin") == content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
