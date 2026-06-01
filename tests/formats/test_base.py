"""
Tests for the FormatHandler ABC implementation
"""
import sys
import os
from pathlib import Path

# Add the parent directories to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "Ana Pagonic" / "Pagonic"))

import pytest
from core.formats.base import FormatHandler
from typing import Dict, List, Optional, Any

class MockFormatHandler(FormatHandler):
    """Mock implementation of FormatHandler for testing"""
    
    def __init__(self, name: str = "mock", extensions: List[str] = [".mock"]):
        self.name = name
        self.extensions = extensions
        self.can_compress = True
        self.can_decompress = True
        self.compression_ratio = 0.5
        self.metadata = {"size": 1000, "files": ["test.txt"]}

    def compress(self, files: List[str], output: str, 
                options: Optional[Dict[str, Any]] = None) -> None:
        if not files:
            raise ValueError("No files provided")
        return None

    def decompress(self, archive: str, target_dir: str,
                  options: Optional[Dict[str, Any]] = None) -> None:
        if not archive:
            raise ValueError("No archive provided")
        return None

    def validate(self, file_path: str) -> bool:
        return any(file_path.endswith(ext) for ext in self.extensions)
    
    def get_metadata(self, archive: str) -> Dict[str, Any]:
        return self.metadata

    def get_compression_ratio(self, archive: Optional[str] = None) -> float:
        return self.compression_ratio

def test_abstract_class_instantiation():
    """Test that FormatHandler cannot be instantiated directly"""
    with pytest.raises(TypeError):
        FormatHandler()

def test_mock_handler_instantiation():
    """Test that concrete implementation can be instantiated"""
    handler = MockFormatHandler()
    assert isinstance(handler, FormatHandler)
    assert handler.name == "mock"
    assert handler.extensions == [".mock"]
    assert handler.can_compress is True
    assert handler.can_decompress is True

def test_compression():
    """Test basic compression functionality"""
    handler = MockFormatHandler()
    # Should work with valid input
    handler.compress(["test.txt"], "output.mock")
    # Should raise error with invalid input
    with pytest.raises(ValueError):
        handler.compress([], "output.mock")

def test_decompression():
    """Test basic decompression functionality"""
    handler = MockFormatHandler()
    # Should work with valid input
    handler.decompress("test.mock", "output_dir")
    # Should raise error with invalid input
    with pytest.raises(ValueError):
        handler.decompress("", "output_dir")

def test_validation():
    """Test file validation"""
    handler = MockFormatHandler()
    assert handler.validate("test.mock") is True
    assert handler.validate("test.txt") is False

def test_metadata():
    """Test metadata retrieval"""
    handler = MockFormatHandler()
    metadata = handler.get_metadata("test.mock")
    assert isinstance(metadata, dict)
    assert "size" in metadata
    assert "files" in metadata

def test_compression_ratio():
    """Test compression ratio calculation"""
    handler = MockFormatHandler()
    ratio = handler.get_compression_ratio()
    assert isinstance(ratio, float)
    assert 0 <= ratio <= 1  # Ratio should be between 0 and 1

def test_custom_handler():
    """Test handler with custom parameters"""
    handler = MockFormatHandler("custom", [".cst", ".test"])
    assert handler.name == "custom"
    assert ".cst" in handler.extensions
    assert ".test" in handler.extensions
    assert handler.validate("test.cst") is True
    assert handler.validate("test.test") is True

def test_handler_registration():
    """Test plugin registration system"""
    # Temizlik
    FormatHandler._registered_handlers.clear()
    FormatHandler._handler_priorities.clear()
    
    # Handler kayıt
    FormatHandler.register(MockFormatHandler, priority=10)
    
    # Handler bulunabilmeli
    handler = FormatHandler.get_handler("mock")
    assert isinstance(handler, MockFormatHandler)
    
    # Öncelik doğru olmalı
    assert FormatHandler._handler_priorities["mock"] == 10

def test_handler_priorities():
    """Test handler priority system"""
    # Temizlik
    FormatHandler._registered_handlers.clear()
    FormatHandler._handler_priorities.clear()
    
    # Farklı öncelikli handler'lar kaydet
    class HighPriorityHandler(MockFormatHandler):
        def __init__(self): super().__init__("high", [".high"])
    
    class LowPriorityHandler(MockFormatHandler):
        def __init__(self): super().__init__("low", [".low"])
    
    FormatHandler.register(LowPriorityHandler, priority=0)
    FormatHandler.register(HighPriorityHandler, priority=100)
    
    # Öncelik sırasını kontrol et
    formats = FormatHandler.get_supported_formats()
    assert formats[0] == "high"  # Yüksek öncelikli ilk sırada
    assert formats[1] == "low"   # Düşük öncelikli son sırada

def test_default_options():
    """Test default options system"""
    # Test options
    test_options = {"level": 9, "method": "deflate"}
    
    # Set default options
    FormatHandler.set_default_options("mock", test_options)
    
    # Create handler and check options
    handler = MockFormatHandler()
    options = handler.get_options()
    
    assert "level" in options
    assert options["level"] == 9
    assert options["method"] == "deflate"
