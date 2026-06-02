"""
Format Handler implementations for specific compression formats.
"""

import os
import importlib
import sys
import importlib.util
from typing import List, Type, Optional, Dict
from ..base import FormatHandler
from ..errors import ValidationError

from .zip_handler import ZipHandler, register_zip_handler

def discover_handlers(custom_dir: Optional[str] = None) -> List[Type[FormatHandler]]:
    """
    Handlers dizinindeki tüm format handler'ları otomatik olarak keşfeder.

    Args:
        custom_dir (str, optional): Özel bir dizinden handler'ları yüklemek için kullanılır.
                                  None ise varsayılan dizin kullanılır.

    Returns:
        List[Type[FormatHandler]]: Bulunan handler sınıflarının listesi
    """
    handlers = []
    current_dir = custom_dir if custom_dir else os.path.dirname(__file__)
    
    # .py uzantılı dosyaları tara
    for file in os.listdir(current_dir):
        if file.endswith('.py') and not file.startswith('__'):
            module_name = file[:-3]  # .py uzantısını kaldır
            try:
                # Modülü dinamik olarak yükle
                if custom_dir:
                    spec = importlib.util.spec_from_file_location(
                        module_name, 
                        os.path.join(custom_dir, file)
                    )
                    if spec is not None and spec.loader is not None:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                    else:
                        print(f"Spec veya loader oluşturulamadı: {module_name}")
                        continue
                else:
                    module = importlib.import_module(f'.{module_name}', package=__package__)
                
                # Modüldeki FormatHandler alt sınıflarını bul
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, FormatHandler) and
                        attr != FormatHandler):
                        handlers.append(attr)
            except Exception as e:
                print(f"Handler yüklenirken hata: {module_name} - {str(e)}")
    
    return handlers

def register_handlers(priority_map: Optional[Dict] = None, custom_dir: Optional[str] = None) -> None:
    """
    Keşfedilen handler'ları sisteme kaydeder.

    Args:
        priority_map: Format isimlerine göre öncelik değerleri
        custom_dir: Handler'ların aranacağı özel dizin
    """
    priority_map = priority_map or {}
    handlers = discover_handlers(custom_dir)
    
    for handler_class in handlers:
        # Handler'ın instance'ını oluşturmadan ismini al
        temp_instance = handler_class()
        priority = priority_map.get(temp_instance.name, 0)
        
        # Handler'ı kaydet
        FormatHandler.register(handler_class, priority=priority)

# Uygulama başladığında handler'ları otomatik kaydet
register_handlers({
    '7z': 90,    # 7Z ikinci öncelikli
    'rar': 80,   # RAR üçüncü öncelikli
})
