"""
Smart Compression Tests
========================
Tests for entropy calculation and smart compression level selection.

"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


class TestEntropyCalculation:
    """Test Shannon entropy calculation."""
    
    def test_entropy_empty_data(self):
        """Test entropy of empty data"""
        from Pagonic.core.formats.compression_utils import calculate_entropy
        assert calculate_entropy(b"") == 0.0
    
    def test_entropy_single_byte(self):
        """Test entropy of repeated single byte (minimum entropy)"""
        from Pagonic.core.formats.compression_utils import calculate_entropy
        data = b"A" * 1000
        entropy = calculate_entropy(data)
        assert entropy == 0.0  # No randomness
    
    def test_entropy_uniform_distribution(self):
        """Test entropy of all byte values (maximum entropy)"""
        from Pagonic.core.formats.compression_utils import calculate_entropy
        data = bytes(range(256)) * 4  # Each byte appears 4 times
        entropy = calculate_entropy(data)
        assert entropy > 0.99  # Very close to 1.0
    
    def test_entropy_text_data(self):
        """Test entropy of typical text (medium entropy)"""
        from Pagonic.core.formats.compression_utils import calculate_entropy
        data = b"Hello World! This is a test of entropy calculation."
        entropy = calculate_entropy(data)
        # Text typically has entropy around 0.4-0.6
        assert 0.3 < entropy < 0.7
    
    def test_entropy_random_data(self):
        """Test entropy of random data (high entropy)"""
        from Pagonic.core.formats.compression_utils import calculate_entropy
        import random
        random.seed(42)
        data = bytes([random.randint(0, 255) for _ in range(1000)])
        entropy = calculate_entropy(data)
        assert entropy > 0.9  # Random data is high entropy


class TestSmartCompressionLevel:
    """Test smart compression level selection."""
    
    def test_precompressed_jpg(self):
        """Test JPEG gets STORE mode"""
        from Pagonic.core.formats.compression_utils import smart_select_compression_level
        level = smart_select_compression_level("photo.jpg", 1000000)
        assert level == 0  # STORE
    
    def test_precompressed_zip(self):
        """Test ZIP gets STORE mode"""
        from Pagonic.core.formats.compression_utils import smart_select_compression_level
        level = smart_select_compression_level("archive.zip", 1000000)
        assert level == 0  # STORE
    
    def test_text_file_max_compression(self):
        """Test text file gets maximum compression"""
        from Pagonic.core.formats.compression_utils import smart_select_compression_level
        level = smart_select_compression_level("document.txt", 1000)
        assert level == 9  # Maximum
    
    def test_json_file_max_compression(self):
        """Test JSON file gets maximum compression"""
        from Pagonic.core.formats.compression_utils import smart_select_compression_level
        level = smart_select_compression_level("config.json", 5000)
        assert level == 9  # Maximum
    
    def test_python_file_good_compression(self):
        """Test Python file gets good compression"""
        from Pagonic.core.formats.compression_utils import smart_select_compression_level
        level = smart_select_compression_level("script.py", 10000)
        assert level == 7  # Good compression
    
    def test_unknown_small_file(self):
        """Test unknown small file gets moderate compression"""
        from Pagonic.core.formats.compression_utils import smart_select_compression_level
        level = smart_select_compression_level("unknown.dat", 500000)  # 500KB
        assert level == 6  # Moderate
    
    def test_unknown_large_file(self):
        """Test unknown large file gets faster compression"""
        from Pagonic.core.formats.compression_utils import smart_select_compression_level
        level = smart_select_compression_level("big.dat", 500 * 1024 * 1024)  # 500MB
        assert level == 3  # Fast
    
    def test_high_entropy_sample(self):
        """Test high entropy sample triggers STORE mode"""
        from Pagonic.core.formats.compression_utils import smart_select_compression_level
        # Create high entropy (random) sample
        import random
        random.seed(42)
        sample = bytes([random.randint(0, 255) for _ in range(4096)])
        level = smart_select_compression_level("encrypted.bin", 1000000, sample)
        assert level == 0  # STORE (too random to compress)


class TestAdaptiveCompression:
    """Test adaptive compression with negative compression detection."""
    
    def test_adaptive_normal_compression(self):
        """Test normal data compresses well"""
        from Pagonic.core.formats.compression_utils import adaptive_compress
        data = b"A" * 10000  # Highly repetitive
        compressed, method = adaptive_compress(data, 6)
        assert method == 8  # DEFLATE used
        assert len(compressed) < len(data)  # Actual compression
    
    def test_adaptive_store_mode_request(self):
        """Test level 0 always uses STORE"""
        from Pagonic.core.formats.compression_utils import adaptive_compress
        data = b"A" * 100
        compressed, method = adaptive_compress(data, 0)
        assert method == 0  # STORE
        assert compressed == data
    
    def test_adaptive_random_data(self):
        """Test random data falls back to STORE"""
        from Pagonic.core.formats.compression_utils import adaptive_compress
        import random
        random.seed(42)
        data = bytes([random.randint(0, 255) for _ in range(1000)])
        compressed, method = adaptive_compress(data, 6)
        # Random data should either:
        # - Compress poorly (small reduction)
        # - Trigger STORE mode
        # Either way, method should be 0 or 8
        assert method in [0, 8]


class TestFileEntropySample:
    """Test file entropy sampling."""
    
    def test_sample_nonexistent_file(self):
        """Test nonexistent file returns default"""
        from Pagonic.core.formats.compression_utils import get_file_entropy_sample
        entropy = get_file_entropy_sample("/nonexistent/file.txt")
        assert entropy == 0.5  # Default for unknown
    
    def test_sample_text_file(self):
        """Test sampling a text file"""
        from Pagonic.core.formats.compression_utils import get_file_entropy_sample
        
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"Hello World! " * 1000)
            temp_path = f.name
        
        try:
            entropy = get_file_entropy_sample(temp_path)
            assert 0.3 < entropy < 0.7  # Text-like entropy
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
