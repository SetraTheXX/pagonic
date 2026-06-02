"""
Integration Tests
==================
End-to-end scenarios testing full compression and extraction workflows.

"""

import os
import sys
import tempfile
import hashlib
import random
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


def create_test_file(path: Path, size: int, pattern: str = "random") -> bytes:
    """Create a test file with specific size and pattern."""
    if pattern == "random":
        random.seed(42)
        content = bytes([random.randint(0, 255) for _ in range(size)])
    elif pattern == "text":
        content = ("Hello World! This is test content.\n" * (size // 36 + 1))[:size].encode()
    elif pattern == "zeros":
        content = b'\x00' * size
    elif pattern == "binary":
        content = bytes(range(256)) * (size // 256 + 1)
        content = content[:size]
    else:
        content = pattern.encode() * (size // len(pattern) + 1)
        content = content[:size]
    
    path.write_bytes(content)
    return content


def get_file_hash(path: Path) -> str:
    """Get MD5 hash of a file."""
    return hashlib.md5(path.read_bytes()).hexdigest()


class TestCompressExtractCycle:
    """Test full compression and extraction cycles."""
    
    def test_single_file_roundtrip(self):
        """Test single file compress and extract"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create source
            source = tmpdir / "source.txt"
            content = create_test_file(source, 1024, "text")
            original_hash = get_file_hash(source)
            
            # Compress
            zip_path = tmpdir / "archive.zip"
            writer = ZipWriter(str(zip_path))
            writer.add_file(str(source))
            writer.finalize()
            
            # Extract
            output_dir = tmpdir / "output"
            output_dir.mkdir()
            reader = ZipReader(str(zip_path))
            reader.extract_all(str(output_dir))
            
            # Verify
            extracted = output_dir / "source.txt"
            assert extracted.exists()
            assert get_file_hash(extracted) == original_hash
    
    def test_multiple_files_roundtrip(self):
        """Test multiple files compress and extract"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create multiple source files
            sources = {}
            sizes = [1024, 10240, 102400]  # 1KB, 10KB, 100KB
            
            for i, size in enumerate(sizes):
                source = tmpdir / f"file{i}.bin"
                create_test_file(source, size, "binary")
                sources[source.name] = get_file_hash(source)
            
            # Compress all
            zip_path = tmpdir / "multi.zip"
            writer = ZipWriter(str(zip_path))
            for source in sources:
                writer.add_file(str(tmpdir / source))
            writer.finalize()
            
            # Extract all
            output_dir = tmpdir / "output"
            output_dir.mkdir()
            reader = ZipReader(str(zip_path))
            reader.extract_all(str(output_dir))
            
            # Verify all
            for name, original_hash in sources.items():
                extracted = output_dir / name
                assert extracted.exists(), f"{name} not found"
                assert get_file_hash(extracted) == original_hash, f"{name} hash mismatch"
    
    def test_directory_roundtrip(self):
        """Test directory compress and extract"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create nested directory structure
            src_dir = tmpdir / "source_dir"
            src_dir.mkdir()
            (src_dir / "file1.txt").write_text("Root file")
            (src_dir / "sub1").mkdir()
            (src_dir / "sub1" / "file2.txt").write_text("Sub1 file")
            (src_dir / "sub1" / "sub2").mkdir()
            (src_dir / "sub1" / "sub2" / "file3.txt").write_text("Sub2 file")
            
            hashes = {
                "file1.txt": get_file_hash(src_dir / "file1.txt"),
                "sub1/file2.txt": get_file_hash(src_dir / "sub1" / "file2.txt"),
                "sub1/sub2/file3.txt": get_file_hash(src_dir / "sub1" / "sub2" / "file3.txt"),
            }
            
            # Compress
            zip_path = tmpdir / "dir.zip"
            writer = ZipWriter(str(zip_path))
            writer.add_directory(str(src_dir))
            writer.finalize()
            
            # Extract
            output_dir = tmpdir / "output"
            output_dir.mkdir()
            reader = ZipReader(str(zip_path))
            reader.extract_all(str(output_dir))
            
            # Verify structure exists
            assert (output_dir / "source_dir").exists() or any(
                (output_dir / rel.replace("/", os.sep)).exists() 
                for rel in hashes
            )


class TestCompressionLevels:
    """Test different compression levels."""
    
    def test_compression_level_affects_size(self):
        """Test that higher compression level produces smaller files"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create compressible content
            source = tmpdir / "compressible.txt"
            create_test_file(source, 100000, "text")  # 100KB text
            
            sizes = {}
            for level in [1, 5, 9]:
                zip_path = tmpdir / f"level{level}.zip"
                writer = ZipWriter(str(zip_path), compression_level=level)
                writer.add_file(str(source))
                writer.finalize()
                sizes[level] = zip_path.stat().st_size
            
            # Higher level should produce smaller or equal size
            assert sizes[9] <= sizes[5] <= sizes[1]
    
    def test_all_levels_produce_valid_zip(self):
        """Test all compression levels produce valid ZIP"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            source = tmpdir / "test.txt"
            content = create_test_file(source, 10000, "text")
            
            for level in range(10):
                zip_path = tmpdir / f"level{level}.zip"
                writer = ZipWriter(str(zip_path), compression_level=level)
                writer.add_file(str(source))
                writer.finalize()
                
                # Verify can be read
                reader = ZipReader(str(zip_path))
                files = reader.list_files()
                assert len(files) > 0


class TestLargeFiles:
    """Test large file handling."""
    
    def test_10mb_file(self):
        """Test 10MB file roundtrip"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            source = tmpdir / "large.bin"
            create_test_file(source, 10 * 1024 * 1024, "binary")  # 10MB
            original_hash = get_file_hash(source)
            
            # Compress
            zip_path = tmpdir / "large.zip"
            writer = ZipWriter(str(zip_path))
            writer.add_file(str(source))
            writer.finalize()
            
            # Extract
            output_dir = tmpdir / "output"
            output_dir.mkdir()
            reader = ZipReader(str(zip_path))
            reader.extract_all(str(output_dir))
            
            # Verify
            extracted = output_dir / "large.bin"
            assert get_file_hash(extracted) == original_hash
    
    def test_many_small_files(self):
        """Test archive with many small files"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            file_count = 50
            
            # Create many small files
            for i in range(file_count):
                f = tmpdir / f"small_{i:03d}.txt"
                f.write_text(f"Small file number {i}")
            
            # Compress all
            zip_path = tmpdir / "many.zip"
            writer = ZipWriter(str(zip_path))
            for i in range(file_count):
                writer.add_file(str(tmpdir / f"small_{i:03d}.txt"))
            writer.finalize()
            
            # Verify count
            reader = ZipReader(str(zip_path))
            files = reader.list_files()
            assert len(files) == file_count


class TestCrossPlatformPaths:
    """Test cross-platform path handling."""
    
    def test_forward_slash_paths(self):
        """Test paths with forward slashes work"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            zip_path = tmpdir / "paths.zip"
            writer = ZipWriter(str(zip_path))
            writer.add_data("folder/subfolder/file.txt", b"Content")
            writer.finalize()
            
            reader = ZipReader(str(zip_path))
            files = reader.list_files()
            # Path may be preserved or sanitized to just filename
            assert len(files) >= 1
            assert any("file.txt" in f for f in files)


class TestMixedContent:
    """Test archives with mixed content types."""
    
    def test_text_and_binary(self):
        """Test mixing text and binary files"""
        from Pagonic.core.formats.zip_writer import ZipWriter
        from Pagonic.core.formats.zip_reader import ZipReader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            zip_path = tmpdir / "mixed.zip"
            writer = ZipWriter(str(zip_path))
            
            # Add text
            writer.add_data("readme.txt", b"This is text content")
            
            # Add binary
            writer.add_data("data.bin", bytes(range(256)))
            
            # Add JSON
            writer.add_data("config.json", b'{"key": "value"}')
            
            writer.finalize()
            
            # Verify all present
            reader = ZipReader(str(zip_path))
            files = reader.list_files()
            assert len(files) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
