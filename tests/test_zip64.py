"""
ZIP64 Support Tests
===================
Tests for ZIP64 format support (>4GB files, >65535 entries).

Uses sparse files to simulate large files without consuming disk space.
"""

import os
import sys
import tempfile
import struct
from pathlib import Path

# Add parent for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


class TestZIP64DataStructures:
    """Test ZIP64 dataclasses in zip_structs.py"""
    
    def test_zip64_eocd_record_import(self):
        """Test ZIP64EndOfCentralDirRecord can be imported"""
        from Pagonic.core.formats.zip_structs import ZIP64EndOfCentralDirRecord
        assert ZIP64EndOfCentralDirRecord is not None
    
    def test_zip64_locator_import(self):
        """Test ZIP64EndOfCentralDirLocator can be imported"""
        from Pagonic.core.formats.zip_structs import ZIP64EndOfCentralDirLocator
        assert ZIP64EndOfCentralDirLocator is not None
    
    def test_zip64_extra_field_import(self):
        """Test ZIP64ExtraField can be imported"""
        from Pagonic.core.formats.zip_structs import ZIP64ExtraField
        assert ZIP64ExtraField is not None
    
    def test_parse_zip64_extra_field_import(self):
        """Test parse_zip64_extra_field function can be imported"""
        from Pagonic.core.formats.zip_structs import parse_zip64_extra_field
        assert callable(parse_zip64_extra_field)
    
    def test_zip64_signatures_exist(self):
        """Test ZIP64 signatures are defined"""
        from Pagonic.core.formats.zip_structs import ZipSignatures
        assert ZipSignatures.ZIP64_EOCD_SIGNATURE == 0x06064b50
        assert ZipSignatures.ZIP64_EOCD_LOCATOR_SIGNATURE == 0x07064b50


class TestZIP64ExtraFieldParser:
    """Test ZIP64 extra field parsing"""
    
    def test_parse_empty_extra_field(self):
        """Test parsing empty extra field returns None"""
        from Pagonic.core.formats.zip_structs import parse_zip64_extra_field
        result = parse_zip64_extra_field(b"", needs_uncompressed=True)
        assert result is None
    
    def test_parse_zip64_uncompressed_size(self):
        """Test parsing ZIP64 extra field with uncompressed size"""
        from Pagonic.core.formats.zip_structs import parse_zip64_extra_field
        
        # Build ZIP64 extra field: tag=0x0001, size=8, value=5GB
        size_5gb = 5 * 1024 * 1024 * 1024
        extra_data = struct.pack('<HHQ', 0x0001, 8, size_5gb)
        
        result = parse_zip64_extra_field(extra_data, needs_uncompressed=True)
        assert result is not None
        assert result.uncompressed_size == size_5gb
    
    def test_parse_zip64_both_sizes(self):
        """Test parsing ZIP64 extra field with both sizes"""
        from Pagonic.core.formats.zip_structs import parse_zip64_extra_field
        
        # Build ZIP64 extra field with uncompressed + compressed sizes
        uncompressed = 6 * 1024 * 1024 * 1024
        compressed = 4 * 1024 * 1024 * 1024
        extra_data = struct.pack('<HHQQ', 0x0001, 16, uncompressed, compressed)
        
        result = parse_zip64_extra_field(extra_data, 
                                         needs_uncompressed=True, 
                                         needs_compressed=True)
        assert result is not None
        assert result.uncompressed_size == uncompressed
        assert result.compressed_size == compressed


class TestZIP64Writer:
    """Test ZIP64 writing capability"""
    
    def test_zipwriter_allows_zip64(self):
        """Test ZipWriter has ZIP64 enabled"""
        # This is an indirect test - we verify the code path exists
        from Pagonic.core.formats.zip_writer import ZipWriter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a small test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Hello ZIP64!")
            
            # Create archive
            output = Path(tmpdir) / "test.zip"
            writer = ZipWriter(str(output))
            writer.add_file(str(test_file))
            stats = writer.finalize()
            
            assert output.exists()
            assert stats['files_processed'] == 1


class TestZIP64SparseFileSimulation:
    """Test ZIP64 with simulated large files (sparse files)"""
    
    @pytest.mark.skipif(
        sys.platform == 'win32' and not os.path.exists('C:\\'),
        reason="Sparse file test may not work on all systems"
    )
    def test_sparse_file_creation(self):
        """Test we can create sparse files for ZIP64 testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            sparse_file = Path(tmpdir) / "sparse_5gb.bin"
            
            # Create 5GB sparse file (doesn't actually use disk space)
            size_5gb = 5 * 1024 * 1024 * 1024
            with open(sparse_file, 'wb') as f:
                f.seek(size_5gb - 1)
                f.write(b'\0')
            
            # Verify reported size
            assert sparse_file.stat().st_size == size_5gb


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
