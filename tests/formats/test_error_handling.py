import pytest
import logging
from unittest.mock import MagicMock, patch

from core.formats.registry import FormatRegistry
from core.formats.errors import (
    FormatError, ValidationError, CompressionError,
    UnsupportedFormatError, ConversionError, ResourceError,
    ErrorContext, ErrorSeverity, ErrorCategory
)

class MockHandler:
    def __init__(self, name="test_format"):
        self.name = name
        self.can_compress = True
        self.can_decompress = True
        self.typical_ratio = 0.5
        self.max_compression_level = 9

class TestErrorHandling:
    
    @pytest.fixture
    def registry(self):
        reg = FormatRegistry()
        reg.clear_error_history()  # Test öncesi temizlik
        return reg

    def test_validation_error(self, registry):
        """Test validation error handling"""
        with pytest.raises(FormatError) as exc_info:
            registry.register(None)
        
        error = exc_info.value
        assert isinstance(error, FormatError)
        assert error.context.operation == "register_handler"
        assert "Failed to register handler" in str(error)

    def test_unsupported_format_error(self, registry):
        """Test unsupported format error handling"""
        with pytest.raises(UnsupportedFormatError) as exc_info:
            registry.get_handler("nonexistent_format")
        
        error = exc_info.value
        assert error.context.operation == "get_handler"
        assert error.context.format_name == "nonexistent_format"

    def test_conversion_error(self, registry):
        """Test conversion error handling"""
        # Geçersiz format dönüşümü
        with pytest.raises(ConversionError) as exc_info:
            registry.suggest_conversion("unknown1", "unknown2")
        
        error = exc_info.value
        assert error.context.operation == "suggest_conversion"
        assert "unknown1->unknown2" in error.context.format_name

    def test_error_history(self, registry):
        """Test error history management"""
        # Birkaç hata oluştur
        try:
            registry.get_handler("nonexistent")
        except FormatError:
            pass

        try:
            registry.suggest_conversion("unknown1", "unknown2")
        except FormatError:
            pass

        # Hata geçmişini kontrol et
        history = registry.get_error_history()
        assert len(history) == 2
        assert isinstance(history[0], UnsupportedFormatError)
        assert isinstance(history[1], ConversionError)

        # Geçmiş temizleme
        registry.clear_error_history()
        assert len(registry.get_error_history()) == 0

    def test_error_logging(self, registry):
        """Test error logging functionality"""
        with patch('core.formats.errors.logger.log') as mock_log:
            try:
                registry.get_handler("nonexistent")
            except FormatError:
                pass

            # Loglama çağrısını kontrol et
            mock_log.assert_called()
            level, message = mock_log.call_args[0]
            assert level == logging.ERROR
            assert "nonexistent" in message

    def test_detailed_error_context(self, registry):
        """Test error context details"""
        context = ErrorContext(
            operation="test_op",
            format_name="test_format",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.VALIDATION,
            file_path="/test/path",
            details={"key": "value"},
            recovery_hints=["Fix A", "Try B"]
        )
        
        error = ValidationError("Test error", context)
        error_str = str(error)
        
        # Hata mesajında tüm detayların olduğunu kontrol et
        assert "VALIDATION_ERROR" in error_str
        assert "Severity: ERROR" in error_str
        assert "Category: VALIDATION" in error_str
        assert "Operation: test_op" in error_str
        assert "Format: test_format" in error_str
        assert "File: /test/path" in error_str
        assert "key: value" in error_str
        assert "Fix A" in error_str
        assert "Try B" in error_str

    def test_recoverable_error(self, registry):
        """Test error recovery functionality"""
        context = ErrorContext(
            operation="compress",
            format_name="zip",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.COMPRESSION,
            recovery_hints=["Check disk space", "Try lower compression"]
        )
        
        error = CompressionError("Compression failed", context)
        
        # Toparlanma özelliklerini test et
        assert error.can_recover()
        recovery_steps = error.get_recovery_steps()
        assert len(recovery_steps) == 2
        assert "Check disk space" in recovery_steps
        assert "Try lower compression" in recovery_steps

    def test_error_severity_logging(self, registry):
        """Test error severity based logging"""
        test_cases = [
            (ErrorSeverity.INFO, logging.INFO),
            (ErrorSeverity.WARNING, logging.WARNING),
            (ErrorSeverity.ERROR, logging.ERROR),
            (ErrorSeverity.CRITICAL, logging.CRITICAL)
        ]
        
        for severity, expected_level in test_cases:
            with patch('core.formats.errors.logger.log') as mock_log:
                context = ErrorContext(
                    operation="test",
                    format_name="test",
                    severity=severity,
                    category=ErrorCategory.VALIDATION
                )
                FormatError("Test error", context)
                
                mock_log.assert_called_once()
                actual_level, _ = mock_log.call_args[0]
                assert actual_level == expected_level
