"""
Pagonic Format Handler Base Class
--------------------------------
Bu modül, tüm format handler'lar için temel ABC (Abstract Base Class) sınıfını içerir.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, ClassVar

class FormatHandler(ABC):
    """
    Format Handler temel sınıfı. Tüm format handler'lar bu sınıftan türetilmelidir.
    """
    
    # Plugin sistemi için sınıf seviyesinde özellikler
    _registered_handlers: ClassVar[Dict[str, 'FormatHandler']] = {}
    _handler_priorities: ClassVar[Dict[str, int]] = {}
    _default_options: ClassVar[Dict[str, Any]] = {}
    
    # Zorunlu özellikler
    name: str  # Format adı (zip, 7z, rar vb.)
    extensions: List[str]  # Desteklenen uzantılar (.zip, .7z vb.)
    can_compress: bool  # Sıkıştırma desteği
    can_decompress: bool  # Açma desteği

    @abstractmethod
    def compress(
        self, 
        files: List[str], 
        output: str,
        options: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Dosyaları sıkıştırır.

        Args:
            files: Sıkıştırılacak dosyaların listesi
            output: Çıktı arşiv dosyasının yolu
            options: Compression options (level, password, chunk_size, etc.)

        Raises:
            CompressionError: Sıkıştırma hatası durumunda
            ValidationError: Geçersiz dosya/format durumunda
        """
        pass

    @abstractmethod
    def decompress(
        self, 
        archive: str, 
        target_dir: str,
        options: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Arşiv dosyasını açar.

        Args:
            archive: Arşiv dosyasının yolu
            target_dir: Hedef klasör yolu
            options: Extraction options (password, extract_path, etc.)

        Raises:
            DecompressionError: Açma hatası durumunda
            ValidationError: Geçersiz arşiv durumunda
        """
        pass

    @abstractmethod
    def validate(self, file_path: str) -> bool:
        """
        Dosya formatının geçerli olup olmadığını kontrol eder.

        Args:
            file_path: Kontrol edilecek dosyanın yolu

        Returns:
            bool: Format geçerli ise True
        """
        pass

    def get_metadata(self, archive: str) -> Dict[str, Any]:
        """
        Arşiv dosyasının meta verilerini döndürür.

        Args:
            archive: Arşiv dosyasının yolu

        Returns:
            Dict[str, Any]: Meta veriler (boyut, dosya listesi, sıkıştırma oranı vb.)
        """
        return {}

    def get_compression_ratio(self, archive: Optional[str] = None) -> float:
        """
        Sıkıştırma oranını hesaplar.

        Args:
            archive: Opsiyonel arşiv dosyası. None ise son işlemin oranını döner

        Returns:
            float: Sıkıştırma oranı (0.0 - 1.0 arası)
        """
        return 0.0

    @classmethod
    def register(cls, handler_class: type['FormatHandler'], priority: int = 0) -> type['FormatHandler']:
        """
        Format handler'ı plugin sisteme kaydeder.

        Args:
            handler_class: Kaydedilecek handler sınıfı
            priority: Handler önceliği (yüksek sayı = yüksek öncelik)

        Returns:
            type[FormatHandler]: Kaydedilen handler sınıfı
        """
        handler = handler_class()
        cls._registered_handlers[handler.name] = handler
        cls._handler_priorities[handler.name] = priority
        return handler_class

    @classmethod
    def get_handler(cls, format_name: str) -> Optional['FormatHandler']:
        """
        İsme göre kayıtlı handler'ı döndürür.

        Args:
            format_name: Handler ismi

        Returns:
            Optional[FormatHandler]: Bulunan handler veya None
        """
        return cls._registered_handlers.get(format_name)

    @classmethod
    def get_supported_formats(cls) -> List[str]:
        """
        Desteklenen tüm formatları döndürür.

        Returns:
            List[str]: Format isimleri listesi
        """
        return sorted(cls._registered_handlers.keys(),
                     key=lambda x: (-cls._handler_priorities[x], x))

    @classmethod
    def set_default_options(cls, format_name: str, options: Dict[str, Any]) -> None:
        """
        Format için varsayılan seçenekleri ayarlar.

        Args:
            format_name: Format ismi
            options: Varsayılan seçenekler
        """
        cls._default_options[format_name] = options.copy()

    def get_options(self) -> Dict[str, Any]:
        """
        Format için varsayılan ve özel seçenekleri birleştirir.

        Returns:
            Dict[str, Any]: Birleştirilmiş seçenekler
        """
        default = self._default_options.get(self.name, {})
        return default
