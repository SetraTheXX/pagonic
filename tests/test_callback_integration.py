"""
Test Callback Integration
=========================
Tests for progress callback functionality in ZipWriter and ZipReader.

"""

import os
import tempfile
import pytest
from pathlib import Path

# Import with fallback
try:
    from Pagonic.core.formats.zip_writer import ZipWriter
    from Pagonic.core.formats.zip_reader import ZipReader
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from Pagonic.core.formats.zip_writer import ZipWriter
    from Pagonic.core.formats.zip_reader import ZipReader


class TestZipWriterCallback:
    """Test ZipWriter progress_callback functionality."""
    
    def test_callback_is_called(self, tmp_path):
        """Test that callback is called during finalize."""
        # Create test files
        test_file1 = tmp_path / "file1.txt"
        test_file2 = tmp_path / "file2.txt"
        test_file1.write_text("Hello World 1")
        test_file2.write_text("Hello World 2")
        
        output_zip = tmp_path / "test.zip"
        
        # Track callback calls
        callback_log = []
        
        def progress_callback(current, total):
            callback_log.append((current, total))
        
        # Compress with callback
        writer = ZipWriter(str(output_zip))
        writer.add_file(str(test_file1))
        writer.add_file(str(test_file2))
        writer.finalize(progress_callback=progress_callback)
        
        # Verify callback was called
        assert len(callback_log) >= 2, "Callback should be called for each file"
        assert callback_log[-1][0] == callback_log[-1][1], "Final call should show complete"
    
    def test_callback_with_data(self, tmp_path):
        """Test callback with add_data."""
        output_zip = tmp_path / "test.zip"
        
        callback_log = []
        
        def progress_callback(current, total):
            callback_log.append((current, total))
        
        writer = ZipWriter(str(output_zip))
        writer.add_data("data1.txt", b"Data 1 content")
        writer.add_data("data2.txt", b"Data 2 content")
        writer.add_data("data3.txt", b"Data 3 content")
        writer.finalize(progress_callback=progress_callback)
        
        assert len(callback_log) >= 3
    
    def test_callback_none(self, tmp_path):
        """Test that None callback doesn't cause errors."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("Test content")
        output_zip = tmp_path / "test.zip"
        
        writer = ZipWriter(str(output_zip))
        writer.add_file(str(test_file))
        
        # Should not raise
        stats = writer.finalize(progress_callback=None)
        assert stats is not None


class TestZipReaderCallback:
    """Test ZipReader progress_callback functionality."""
    
    @pytest.fixture
    def sample_zip(self, tmp_path):
        """Create a sample ZIP file for testing."""
        # Create test files
        files_dir = tmp_path / "source"
        files_dir.mkdir()
        
        for i in range(5):
            (files_dir / f"file{i}.txt").write_text(f"Content of file {i}")
        
        # Create ZIP
        output_zip = tmp_path / "sample.zip"
        writer = ZipWriter(str(output_zip))
        for f in files_dir.iterdir():
            writer.add_file(str(f))
        writer.finalize()
        
        return output_zip
    
    def test_extract_callback_is_called(self, sample_zip, tmp_path):
        """Test that callback is called during extract_all."""
        extract_dir = tmp_path / "extracted"
        
        callback_log = []
        
        def progress_callback(current, total, filename):
            callback_log.append({
                "current": current,
                "total": total,
                "filename": filename
            })
        
        reader = ZipReader(str(sample_zip))
        result = reader.extract_all(str(extract_dir), progress_callback=progress_callback)
        
        # Verify callbacks
        assert len(callback_log) == 5, "Should be called once per file"
        
        # Verify progress values
        for i, log in enumerate(callback_log):
            assert log["current"] == i + 1
            assert log["total"] == 5
            assert log["filename"] is not None
    
    def test_extract_callback_order(self, sample_zip, tmp_path):
        """Test that callback is called in order."""
        extract_dir = tmp_path / "extracted"
        
        current_values = []
        
        def progress_callback(current, total, filename):
            current_values.append(current)
        
        reader = ZipReader(str(sample_zip))
        reader.extract_all(str(extract_dir), progress_callback=progress_callback)
        
        # Verify ascending order
        assert current_values == sorted(current_values)
        assert current_values[-1] == max(current_values)
    
    def test_extract_callback_none(self, sample_zip, tmp_path):
        """Test that None callback doesn't cause errors."""
        extract_dir = tmp_path / "extracted"
        
        reader = ZipReader(str(sample_zip))
        
        # Should not raise
        result = reader.extract_all(str(extract_dir), progress_callback=None)
        assert result is not None
        assert len(result["success"]) == 5
    
    def test_extract_callback_percentage(self, sample_zip, tmp_path):
        """Test calculating percentage from callback values."""
        extract_dir = tmp_path / "extracted"
        
        percentages = []
        
        def progress_callback(current, total, filename):
            percent = (current / total) * 100
            percentages.append(percent)
        
        reader = ZipReader(str(sample_zip))
        reader.extract_all(str(extract_dir), progress_callback=progress_callback)
        
        # Verify percentages
        assert percentages[0] == 20.0   # 1/5
        assert percentages[-1] == 100.0  # 5/5


class TestConfigManagerIntegration:
    """Test ConfigManager integration."""
    
    def test_config_manager_exists(self, tmp_path):
        """Test that ConfigManager can be imported."""
        from Pagonic.core.config_manager import ConfigManager
        
        config = ConfigManager(str(tmp_path / "config.json"))
        assert config.get("compression_level") == 6
        assert config.get("theme") == "dark"
    
    def test_config_persistence(self, tmp_path):
        """Test that config persists across instances."""
        from Pagonic.core.config_manager import ConfigManager
        
        config_file = tmp_path / "test_config.json"
        
        # Set value
        config1 = ConfigManager(str(config_file))
        config1.set("compression_level", 9)
        
        # Read in new instance
        config2 = ConfigManager(str(config_file))
        assert config2.get("compression_level") == 9
    
    def test_recent_files(self, tmp_path):
        """Test recent files functionality."""
        from Pagonic.core.config_manager import ConfigManager
        
        config_file = tmp_path / "test_config.json"
        config = ConfigManager(str(config_file))
        
        # Add files
        config.add_recent_file("file1.zip")
        config.add_recent_file("file2.zip")
        config.add_recent_file("file3.zip")
        
        recent = config.get_recent_files()
        assert len(recent) == 3
        assert recent[0] == "file3.zip"  # Most recent first


# Quick manual test
if __name__ == "__main__":
    import tempfile
    
    print("🧪 Testing Callback Integration...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test files
        for i in range(3):
            (tmpdir / f"test{i}.txt").write_text(f"Content {i}")
        
        # Test ZipWriter callback
        print("\n1. Testing ZipWriter callback...")
        output_zip = tmpdir / "test.zip"
        
        def writer_callback(current, total):
            percent = (current / total) * 100
            print(f"   Compressing: {current}/{total} ({percent:.0f}%)")
        
        writer = ZipWriter(str(output_zip))
        for f in tmpdir.glob("*.txt"):
            writer.add_file(str(f))
        writer.finalize(progress_callback=writer_callback)
        print("   ✅ ZipWriter callback works!")
        
        # Test ZipReader callback
        print("\n2. Testing ZipReader callback...")
        extract_dir = tmpdir / "extracted"
        
        def reader_callback(current, total, filename):
            percent = (current / total) * 100
            print(f"   Extracting: {current}/{total} ({percent:.0f}%) - {filename}")
        
        reader = ZipReader(str(output_zip))
        reader.extract_all(str(extract_dir), progress_callback=reader_callback)
        print("   ✅ ZipReader callback works!")
        
        # Test ConfigManager
        print("\n3. Testing ConfigManager...")
        from Pagonic.core.config_manager import ConfigManager
        
        config = ConfigManager(str(tmpdir / "config.json"))
        config.set("test_value", 42)
        assert config.get("test_value") == 42
        print("   ✅ ConfigManager works!")
    
    print("\n🎉 All callback integration tests passed!")
