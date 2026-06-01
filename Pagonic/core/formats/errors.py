"""
Custom exceptions for format handling
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum, auto
import traceback
import logging

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Hata ciddiyet seviyeleri"""
    INFO = auto()  # Bilgilendirme
    WARNING = auto()  # Uyarı
    ERROR = auto()  # Hata
    CRITICAL = auto()  # Kritik hata

class ErrorCategory(Enum):
    """Hata kategorileri"""
    VALIDATION = auto()  # Format/dosya doğrulama hataları
    COMPRESSION = auto()  # Sıkıştırma işlem hataları
    IO = auto()  # Dosya sistemi hataları
    RESOURCE = auto()  # Sistem kaynak hataları
    SECURITY = auto()  # Security and encryption errors
    CONVERSION = auto()  # Format dönüşüm hataları
    CONCURRENCY = auto()  # Eşzamanlılık hataları
    UNKNOWN = auto()  # Sınıflandırılamayan hatalar

@dataclass
class ErrorContext:
    """Hata bağlamı için gelişmiş veri sınıfı"""
    operation: str  # Yapılan işlem (compress, decompress, validate, vb.)
    format_name: str  # Hata oluşan format
    severity: ErrorSeverity  # Hata ciddiyet seviyesi
    category: ErrorCategory  # Hata kategorisi
    file_path: Optional[str] = None  # Hata oluşan dosya
    details: Optional[Dict[str, Any]] = None  # Ek detaylar
    stack_trace: Optional[str] = None  # Hata yığını
    recovery_hints: Optional[List[str]] = None  # Toparlanma önerileri

class RecoverableError:
    """Hatadan toparlanma davranışı için mixin sınıfı"""
    context: Optional['ErrorContext']  # Type hint for mixin usage
    
    def can_recover(self) -> bool:
        """Hatadan toparlanılabilir mi?"""
        return bool(self.context and self.context.recovery_hints)
    
    def get_recovery_steps(self) -> List[str]:
        """Toparlanma adımlarını döndürür"""
        if self.context and self.context.recovery_hints:
            return self.context.recovery_hints
        return []

class FormatError(Exception):
    """Base exception for all format-related errors"""
    def __init__(self, 
                 message: str, 
                 context: Optional[ErrorContext] = None,
                 cause: Optional[Exception] = None):
        super().__init__(message)
        if context is None:
            context = ErrorContext(
                operation="unknown",
                format_name="unknown",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.UNKNOWN
            )
        self.context = context
        self.error_code = "FORMAT_ERROR"
        self.__cause__ = cause
        
        # Hata yığınını kaydet
        if not context.stack_trace:
            self.context.stack_trace = "".join(traceback.format_tb(self.__traceback__))
            
        # Hatayı logla
        self._log_error()

    def _log_error(self):
        """Hatayı uygun seviyede loglar"""
        severity_map = {
            ErrorSeverity.INFO: logging.INFO,
            ErrorSeverity.WARNING: logging.WARNING,
            ErrorSeverity.ERROR: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }
        log_level = severity_map.get(self.context.severity, logging.ERROR)
        logger.log(log_level, str(self))

    def __str__(self):
        base_msg = super().__str__()
        if not self.context:
            return base_msg
        
        ctx = self.context
        msg_parts = [
            f"{self.error_code}: {base_msg}",
            f"Severity: {ctx.severity.name}",
            f"Category: {ctx.category.name}",
            f"Operation: {ctx.operation}",
            f"Format: {ctx.format_name}"
        ]
        
        if ctx.file_path:
            msg_parts.append(f"File: {ctx.file_path}")
        if ctx.details:
            msg_parts.append("Details:")
            for k, v in ctx.details.items():
                msg_parts.append(f"  {k}: {v}")
        if ctx.recovery_hints:
            msg_parts.append("Recovery Steps:")
            for hint in ctx.recovery_hints:
                msg_parts.append(f"  - {hint}")
        if ctx.stack_trace:
            msg_parts.append("\nStack Trace:")
            msg_parts.append(ctx.stack_trace)
                
        return "\n".join(msg_parts)

class ValidationError(FormatError, RecoverableError):
    """Format doğrulama hatası"""
    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        if context:
            context.category = ErrorCategory.VALIDATION
            # Severity özel olarak WARNING olarak belirtilmediyse ERROR kullan
            if context.severity != ErrorSeverity.WARNING:
                context.severity = ErrorSeverity.ERROR
            if not context.recovery_hints:
                context.recovery_hints = [
                    "Dosya formatını kontrol edin",
                    "Dosyanın bozuk olmadığından emin olun",
                    "Desteklenen format versiyonlarını kontrol edin"
                ]
        super().__init__(message, context)
        self.error_code = "VALIDATION_ERROR"

class CompressionError(FormatError, RecoverableError):
    """Sıkıştırma/açma hatası"""
    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        if context:
            context.category = ErrorCategory.COMPRESSION
            context.severity = ErrorSeverity.ERROR
            if not context.recovery_hints:
                context.recovery_hints = [
                    "Yeterli disk alanı olduğundan emin olun",
                    "Dosyaların yazma izinlerini kontrol edin",
                    "Sıkıştırma seviyesini düşürmeyi deneyin",
                    "Dosyaları daha küçük parçalara bölmeyi deneyin"
                ]
        super().__init__(message, context)
        self.error_code = "COMPRESSION_ERROR"

class UnsupportedFormatError(FormatError):
    """Desteklenmeyen format hatası"""
    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        if context:
            context.category = ErrorCategory.VALIDATION
            context.severity = ErrorSeverity.ERROR
            if not context.recovery_hints:
                context.recovery_hints = [
                    "Desteklenen formatları kontrol edin",
                    "İlgili format handler'ı yüklü olduğundan emin olun",
                    "Alternatif bir format kullanmayı deneyin"
                ]
        super().__init__(message, context)
        self.error_code = "UNSUPPORTED_FORMAT"

class ConversionError(FormatError, RecoverableError):
    """Format dönüşüm hatası"""
    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        if context:
            context.category = ErrorCategory.CONVERSION
            context.severity = ErrorSeverity.ERROR
            if not context.recovery_hints:
                context.recovery_hints = [
                    "Kaynak ve hedef formatların uyumluluğunu kontrol edin",
                    "Alternatif bir ara format kullanmayı deneyin",
                    "Dönüşüm seçeneklerini gözden geçirin"
                ]
        super().__init__(message, context)
        self.error_code = "CONVERSION_ERROR"

class EncryptionError(FormatError):
    """Encryption and decryption error"""
    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        if context:
            context.category = ErrorCategory.SECURITY
            context.severity = ErrorSeverity.CRITICAL
            if not context.recovery_hints:
                context.recovery_hints = [
                    "Verify that the password is correct",
                    "Check the encryption keys",
                    "Verify encryption algorithm compatibility"
                ]
        super().__init__(message, context)
        self.error_code = "ENCRYPTION_ERROR"

class SecurityError(FormatError):
    """Security validation failures (ZIP bomb, path traversal, etc.)"""
    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        if context:
            context.category = ErrorCategory.SECURITY
            context.severity = ErrorSeverity.CRITICAL
            if not context.recovery_hints:
                context.recovery_hints = [
                    "Verify the source of the file is trusted",
                    "Check file size and compression ratio",
                    "Scan file for malicious content",
                    "Use security validation before processing"
                ]
        super().__init__(message, context)
        self.error_code = "SECURITY_ERROR"

class ResourceError(FormatError, RecoverableError):
    """Sistem kaynakları ile ilgili hatalar"""
    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        if context:
            context.category = ErrorCategory.RESOURCE
            context.severity = ErrorSeverity.ERROR
            if not context.recovery_hints:
                context.recovery_hints = [
                    "Yeterli disk alanı olduğundan emin olun",
                    "Bellek kullanımını kontrol edin",
                    "Gereksiz dosyaları temizleyin",
                    "İşlem önceliğini düşürmeyi deneyin"
                ]
        super().__init__(message, context)
        self.error_code = "RESOURCE_ERROR"

class ConcurrencyError(FormatError, RecoverableError):
    """Eşzamanlı işlemlerle ilgili hatalar"""
    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        if context:
            context.category = ErrorCategory.CONCURRENCY
            context.severity = ErrorSeverity.WARNING
            if not context.recovery_hints:
                context.recovery_hints = [
                    "İşlemi tekrar deneyin",
                    "Kilitlerin serbest bırakılmasını bekleyin",
                    "İşlem sırasını değiştirmeyi deneyin",
                    "Eşzamanlı işlem sayısını azaltın"
                ]
        super().__init__(message, context)
        self.error_code = "CONCURRENCY_ERROR"

class IOError(FormatError, RecoverableError):
    """Dosya sistemi işlem hataları"""
    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        if context:
            context.category = ErrorCategory.IO
            context.severity = ErrorSeverity.ERROR
            if not context.recovery_hints:
                context.recovery_hints = [
                    "Dosya/klasör izinlerini kontrol edin",
                    "Dosyanın kilitli olmadığından emin olun",
                    "Disk alanını kontrol edin",
                    "Dosya yolunun geçerli olduğunu doğrulayın"
                ]
        super().__init__(message, context)
        self.error_code = "IO_ERROR"
