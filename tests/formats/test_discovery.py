"""Tests for the handler discovery system"""

import os
import sys
import pytest
import tempfile
from pathlib import Path
from typing import List, Type

from core.formats.base import FormatHandler
from core.formats.handlers import discover_handlers
from core.formats.errors import ValidationError, FormatError

class MockTestHandler(FormatHandler):
    """Mock handler implementation for testing"""
    def __init__(self):
        self.name = "test"
        self.extensions = [".test"]
        self.can_compress = True
        self.can_decompress = True
    
    def compress(self, files, output, options=None):
        pass
    
    def decompress(self, archive, target_dir, options=None):
        pass
    
    def validate(self, file_path):
        return True

@pytest.fixture
def temp_module_dir():
    """Create a temporary directory for test modules"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Add to Python path so modules can be imported
        sys.path.insert(0, tmp_dir)
        yield tmp_dir
        sys.path.remove(tmp_dir)

def test_discover_valid_handler(temp_module_dir):
    """Test discovery of a valid handler"""
    # Create a valid handler module
    module_path = Path(temp_module_dir) / "valid_handler.py"
    with open(module_path, "w") as f:
        f.write("""
from core.formats.base import FormatHandler

class ValidHandler(FormatHandler):
    def __init__(self):
        self.name = "valid"
        self.extensions = [".valid"]
        self.can_compress = True
        self.can_decompress = True
    
    def compress(self, files, output, options=None):
        pass
    
    def decompress(self, archive, target_dir, options=None):
        pass
    
    def validate(self, file_path):
        return True
""")
    
    handlers = discover_handlers(temp_module_dir)
    assert any(h.__name__ == "ValidHandler" for h in handlers)

def test_ignore_invalid_handler(temp_module_dir):
    """Test that invalid handlers are ignored"""
    module_path = Path(temp_module_dir) / "invalid_handler.py"
    with open(module_path, "w") as f:
        f.write("""
class InvalidHandler:
    \"\"\"Not a FormatHandler subclass\"\"\"
    pass
""")
    
    handlers = discover_handlers(temp_module_dir)
    assert not any(h.__name__ == "InvalidHandler" for h in handlers)

def test_handle_syntax_error(temp_module_dir):
    """Test handling of syntax errors in handler modules"""
    module_path = Path(temp_module_dir) / "broken.py"
    with open(module_path, "w") as f:
        f.write("this is not valid python code")
    
    handlers = discover_handlers(temp_module_dir)  # Should not raise
    assert len(handlers) == 0  # No handlers should be found

def test_handle_missing_dependencies(temp_module_dir):
    """Test handling of modules with missing dependencies"""
    module_path = Path(temp_module_dir) / "missing_deps.py"
    with open(module_path, "w") as f:
        f.write("""
from nonexistent_package import SomeClass
from core.formats.base import FormatHandler

class DependentHandler(FormatHandler):
    pass
""")
    
    handlers = discover_handlers(temp_module_dir)  # Should not raise
    assert not any(h.__name__ == "DependentHandler" for h in handlers)

def test_handle_circular_imports(temp_module_dir):
    """Test handling of circular imports in handler modules"""
    # Create two modules that import each other
    module1_path = Path(temp_module_dir) / "circular1.py"
    module2_path = Path(temp_module_dir) / "circular2.py"
    
    with open(module1_path, "w") as f:
        f.write("""
from core.formats.base import FormatHandler
from circular2 import Handler2

class Handler1(FormatHandler):
    pass
""")
    
    with open(module2_path, "w") as f:
        f.write("""
from core.formats.base import FormatHandler
from circular1 import Handler1

class Handler2(FormatHandler):
    pass
""")
    
    handlers = discover_handlers(temp_module_dir)  # Should not raise
    assert not any(h.__name__ in ("Handler1", "Handler2") for h in handlers)