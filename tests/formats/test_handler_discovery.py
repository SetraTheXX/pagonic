"""Tests for handler discovery and automatic registration"""
import os
import pytest
from typing import List, Optional, Dict, Any
from core.formats.base import FormatHandler
from core.formats.registry import FormatRegistry
from core.formats.handlers import discover_handlers, register_handlers
from pathlib import Path

class TestHandlerDiscovery:
    @pytest.fixture
    def temp_handler_dir(self, tmp_path: Path):
        """Create a temporary directory with mock handler files"""
        handler_dir = tmp_path / "handlers"
        handler_dir.mkdir()
        
        # Create a valid handler file
        valid_handler = handler_dir / "valid_handler.py"
        valid_handler.write_text('''
from core.formats.base import FormatHandler

class TestHandler(FormatHandler):
    name = "test"
    extensions = [".test"]
    can_compress = True
    can_decompress = True

    def __init__(self):
        super().__init__()

    @property
    def priority(self):
        return self.__class__._handler_priorities.get(self.name, 0)

    def compress(self, files, output, options=None):
        pass

    def decompress(self, archive, target_dir, options=None):
        pass
        
    def validate(self, file_path):
        return True
    
    def compress(self, files, output, options=None):
        pass

    def decompress(self, archive, target_dir, options=None):
        pass
        
    def validate(self, file_path):
        return True
''')

        # Create invalid handler files
        invalid_syntax = handler_dir / "invalid_syntax.py"
        invalid_syntax.write_text('''
class BrokenHandler  # Missing colon and body
''')

        invalid_import = handler_dir / "invalid_import.py"
        invalid_import.write_text('''
from nonexistent_module import NonexistentClass
''')
        
        return handler_dir

    def test_discover_handlers(self, temp_handler_dir):
        """Test handler discovery from directory"""
        handlers = discover_handlers(str(temp_handler_dir))
        assert len(handlers) == 1
        
        handler_class = handlers[0]
        temp_instance = handler_class()
        assert temp_instance.name == "test"
        assert temp_instance.extensions == [".test"]
        assert temp_instance.can_compress is True

    def test_discover_handlers_with_errors(self, temp_handler_dir):
        """Test handler discovery with invalid handler files"""
        # Should not raise exceptions for invalid files
        handlers = discover_handlers(str(temp_handler_dir))
        assert len(handlers) == 1  # Only valid handler should be discovered    def test_register_handlers_with_priorities(self, temp_handler_dir):
        """Test handler registration with custom priorities"""
        # Clear any existing handlers first
        FormatHandler._registered_handlers.clear()
        FormatHandler._handler_priorities.clear()

        # Register with priority
        priority_map = {"test": 100}
        register_handlers(priority_map, str(temp_handler_dir))

        # Verify handler exists and has correct priority
        handler = FormatHandler.get_handler("test")
        assert handler is not None, "Handler should be registered"
        assert "test" in FormatHandler._handler_priorities, "Priority should be in _handler_priorities"
        assert FormatHandler._handler_priorities["test"] == 100, "Priority should be 100 in _handler_priorities"
        assert handler.priority == 100, "Handler priority should be 100"

    def test_register_handlers_default_priority(self, temp_handler_dir):
        """Test handler registration with default priority"""
        # Clear any existing handlers first
        FormatHandler._registered_handlers.clear()
        FormatHandler._handler_priorities.clear()
        
        # Register with default priority
        register_handlers(custom_dir=str(temp_handler_dir))
        
        # Verify handler exists and has default priority
        handler = FormatHandler.get_handler("test")
        assert handler is not None, "Handler should be registered"
        assert handler.priority == 0, "Handler priority should be 0"
