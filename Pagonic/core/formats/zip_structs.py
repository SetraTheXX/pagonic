"""
ZIP Format Parser Altyapısı - Gün 7 Phase 0.1
============================================
PAGONIC projesi için ZIP dosyalarının iç yapısını ayrıştıran modüler parser.

Bu modül ZIP formatının doğrudan ayrıştırılması için gereken tüm yapıları içerir:
- End of Central Directory (EOCD) detection
- Central Directory Entry parsing  
- Local File Header extraction
- Offset-based binary parsing
- Error handling for malformed ZIP files

Hedef: decompress() fonksiyonunu ZIP-aware hale getirmek.
"""

import struct
from dataclasses import dataclass
from typing import Tuple, List, BinaryIO, Optional, Union
from pathlib import Path


# ================================================================================
# ZIP FORMAT MAGIC NUMBERS VE SABİTLER
# ================================================================================

class ZipSignatures:
    """ZIP format için magic number ve signature sabitleri."""
    
    # ZIP Central Directory End signature (EOCD)
    EOCD_SIGNATURE = 0x06054b50
    
    # Central Directory File Header signature
    CD_HEADER_SIGNATURE = 0x02014b50
    
    # Local File Header signature
    LOCAL_FILE_HEADER_SIGNATURE = 0x04034b50
    
    # ZIP64 extensions (gelecek için)
    ZIP64_EOCD_SIGNATURE = 0x06064b50
    ZIP64_EOCD_LOCATOR_SIGNATURE = 0x07064b50


class CompressionMethods:
    """Desteklenen sıkıştırma yöntemleri."""
    
    STORE = 0      # Sıkıştırma yok (raw storage)
    DEFLATE = 8    # zlib deflate algoritması
    
    # Desteklenen yöntemler listesi
    SUPPORTED = {STORE, DEFLATE}
    
    @classmethod
    def is_supported(cls, method: int) -> bool:
        """Sıkıştırma yönteminin desteklenip desteklenmediğini kontrol eder."""
        return method in cls.SUPPORTED


# ================================================================================
# DATACLASS YAPILAR - ZIP FORMAT STRUCTURES
# ================================================================================

@dataclass
class EOCDRecord:
    """End of Central Directory Record yapısı."""
    
    signature: int                    # 0x06054b50
    disk_number: int                  # Bu disk numarası
    cd_start_disk: int               # Central Directory'nin başladığı disk
    cd_entries_on_disk: int          # Bu diskteki CD entry sayısı
    total_cd_entries: int            # Toplam CD entry sayısı
    cd_size: int                     # Central Directory boyutu
    cd_offset: int                   # Central Directory offset'i
    comment_length: int              # ZIP dosya yorumu uzunluğu
    comment: bytes                   # ZIP dosya yorumu
    
    # Calculated fields
    eocd_offset: int = 0             # EOCD'nin dosyadaki offset'i
    
    def __post_init__(self):
        """Validation ve post-processing."""
        if self.signature != ZipSignatures.EOCD_SIGNATURE:
            raise ValueError(f"Invalid EOCD signature: 0x{self.signature:08x}")


@dataclass  
class CentralDirectoryEntry:
    """Central Directory File Header yapısı."""
    
    signature: int                   # 0x02014b50
    version_made_by: int            # Dosyayı oluşturan sistem
    version_needed: int             # Extract için gereken minimum versiyon
    flags: int                      # General purpose bit flags
    compression_method: int         # Sıkıştırma yöntemi (0=store, 8=deflate)
    last_mod_time: int             # Son değişiklik zamanı
    last_mod_date: int             # Son değişiklik tarihi
    crc32: int                     # CRC-32 checksum
    compressed_size: int           # Sıkıştırılmış boyut
    uncompressed_size: int         # Asıl boyut
    filename_length: int           # Dosya adı uzunluğu
    extra_field_length: int        # Extra field uzunluğu
    comment_length: int            # Dosya yorumu uzunluğu
    disk_start: int                # Dosyanın başladığı disk
    internal_attrs: int            # Internal file attributes
    external_attrs: int            # External file attributes
    local_header_offset: int       # Local File Header offset'i
    
    # Variable length fields
    filename: str = ""             # Dosya adı
    extra_field: bytes = b""       # Extra field data
    comment: str = ""              # Dosya yorumu
    
    # Calculated fields
    cd_entry_offset: int = 0       # Bu CD entry'nin dosyadaki offset'i
    
    def __post_init__(self):
        """Validation ve post-processing."""
        if self.signature != ZipSignatures.CD_HEADER_SIGNATURE:
            raise ValueError(f"Invalid CD Header signature: 0x{self.signature:08x}")
        
        if not CompressionMethods.is_supported(self.compression_method):
            raise ValueError(f"Unsupported compression method: {self.compression_method}")


@dataclass
class LocalFileHeader:
    """Local File Header yapısı."""
    
    signature: int                   # 0x04034b50
    version_needed: int             # Extract için gereken minimum versiyon
    flags: int                      # General purpose bit flags
    compression_method: int         # Sıkıştırma yöntemi
    last_mod_time: int             # Son değişiklik zamanı
    last_mod_date: int             # Son değişiklik tarihi
    crc32: int                     # CRC-32 checksum
    compressed_size: int           # Sıkıştırılmış boyut
    uncompressed_size: int         # Asıl boyut
    filename_length: int           # Dosya adı uzunluğu
    extra_field_length: int        # Extra field uzunluğu
    
    # Variable length fields
    filename: str = ""             # Dosya adı
    extra_field: bytes = b""       # Extra field data
    
    # Calculated fields
    header_offset: int = 0         # Bu header'ın dosyadaki offset'i
    data_offset: int = 0           # Dosya verisinin başladığı offset
    
    def __post_init__(self):
        """Validation ve post-processing."""
        if self.signature != ZipSignatures.LOCAL_FILE_HEADER_SIGNATURE:
            raise ValueError(f"Invalid Local File Header signature: 0x{self.signature:08x}")
        
        if not CompressionMethods.is_supported(self.compression_method):
            raise ValueError(f"Unsupported compression method: {self.compression_method}")
        
        # Data offset hesaplama
        self.data_offset = (self.header_offset + 30 + 
                           self.filename_length + self.extra_field_length)


# ================================================================================
# ZIP64 EXTENDED STRUCTURES
# ================================================================================

@dataclass
class ZIP64EndOfCentralDirRecord:
    """ZIP64 End of Central Directory Record (56+ bytes).
    
    Used when archive exceeds 4GB or contains more than 65535 files.
    Located just before the ZIP64 EOCD Locator.
    """
    signature: int                    # 0x06064b50
    size_of_zip64_eocd: int          # Size of this record minus 12
    version_made_by: int             # Version made by
    version_needed: int              # Version needed to extract
    disk_number: int                 # Number of this disk (32-bit)
    cd_start_disk: int               # Disk where CD starts (32-bit)
    cd_entries_on_disk: int          # CD entries on this disk (64-bit)
    total_cd_entries: int            # Total CD entries (64-bit)
    cd_size: int                     # Size of CD (64-bit)
    cd_offset: int                   # Offset of CD (64-bit)
    
    def __post_init__(self):
        if self.signature != ZipSignatures.ZIP64_EOCD_SIGNATURE:
            raise ValueError(f"Invalid ZIP64 EOCD signature: 0x{self.signature:08x}")


@dataclass
class ZIP64EndOfCentralDirLocator:
    """ZIP64 End of Central Directory Locator (20 bytes).
    
    Located immediately before the standard EOCD record.
    Points to the ZIP64 EOCD record location.
    """
    signature: int                    # 0x07064b50
    zip64_eocd_disk: int             # Disk number with ZIP64 EOCD
    zip64_eocd_offset: int           # Offset of ZIP64 EOCD (64-bit)
    total_disks: int                 # Total number of disks
    
    def __post_init__(self):
        if self.signature != ZipSignatures.ZIP64_EOCD_LOCATOR_SIGNATURE:
            raise ValueError(f"Invalid ZIP64 Locator signature: 0x{self.signature:08x}")


@dataclass
class ZIP64ExtraField:
    """ZIP64 Extended Information Extra Field (Tag 0x0001).
    
    Present in Local File Header and Central Directory when
    file sizes exceed 32-bit limits.
    """
    uncompressed_size: Optional[int] = None  # 64-bit if original was 0xFFFFFFFF
    compressed_size: Optional[int] = None    # 64-bit if original was 0xFFFFFFFF
    local_header_offset: Optional[int] = None  # 64-bit if original was 0xFFFFFFFF
    disk_start: Optional[int] = None         # 32-bit if original was 0xFFFF


def parse_zip64_extra_field(extra_data: bytes, 
                            needs_uncompressed: bool = False,
                            needs_compressed: bool = False,
                            needs_offset: bool = False,
                            needs_disk: bool = False) -> Optional[ZIP64ExtraField]:
    """Parse ZIP64 extended information from extra field data.
    
    Args:
        extra_data: Raw extra field bytes
        needs_uncompressed: True if uncompressed_size was 0xFFFFFFFF
        needs_compressed: True if compressed_size was 0xFFFFFFFF
        needs_offset: True if local_header_offset was 0xFFFFFFFF
        needs_disk: True if disk_start was 0xFFFF
        
    Returns:
        ZIP64ExtraField with parsed values, or None if not found
    """
    ZIP64_EXTRA_TAG = 0x0001
    offset = 0
    
    while offset + 4 <= len(extra_data):
        tag, size = struct.unpack('<HH', extra_data[offset:offset+4])
        
        if tag == ZIP64_EXTRA_TAG:
            data = extra_data[offset+4:offset+4+size]
            field = ZIP64ExtraField()
            data_offset = 0
            
            # Fields are stored in order, only present if needed
            if needs_uncompressed and data_offset + 8 <= len(data):
                field.uncompressed_size = struct.unpack('<Q', data[data_offset:data_offset+8])[0]
                data_offset += 8
                
            if needs_compressed and data_offset + 8 <= len(data):
                field.compressed_size = struct.unpack('<Q', data[data_offset:data_offset+8])[0]
                data_offset += 8
                
            if needs_offset and data_offset + 8 <= len(data):
                field.local_header_offset = struct.unpack('<Q', data[data_offset:data_offset+8])[0]
                data_offset += 8
                
            if needs_disk and data_offset + 4 <= len(data):
                field.disk_start = struct.unpack('<I', data[data_offset:data_offset+4])[0]
                data_offset += 4
                
            return field
            
        offset += 4 + size
    
    return None


# ================================================================================
# FILENAME ENCODING FUNCTIONS (UTF-8 / CP437)
# ================================================================================

def encode_filename(name: str) -> tuple:
    """Encode filename to UTF-8 bytes with General Purpose Bit Flag 11.
    
    ZIP specification requires Bit 11 to be set when filenames are UTF-8 encoded.
    This ensures compatibility with modern ZIP readers.
    
    Args:
        name: Unicode filename string
        
    Returns:
        Tuple of (encoded_bytes, flags) where flags has Bit 11 set
    """
    encoded = name.encode('utf-8')
    flags = 0x800  # General Purpose Bit Flag 11 = UTF-8
    return encoded, flags


def decode_filename(data: bytes, flags: int) -> str:
    """Decode filename with smart UTF-8/CP437 fallback.
    
    Detection strategy:
    1. If Bit 11 set → UTF-8 (modern ZIP)
    2. Else → Try UTF-8 first, fallback to CP437 (DOS legacy)
    
    Args:
        data: Raw filename bytes from ZIP
        flags: General Purpose Bit Flags from header
        
    Returns:
        Decoded Unicode filename string
    """
    if flags & 0x800:  # General Purpose Bit 11 = UTF-8
        return data.decode('utf-8')
    else:
        # Legacy ZIP compatibility: try UTF-8 first, then CP437
        try:
            return data.decode('utf-8')
        except UnicodeDecodeError:
            return data.decode('cp437', errors='replace')


# ================================================================================
# ZIP PARSER EXCEPTIONS
# ================================================================================

class ZipParseError(Exception):
    """ZIP parsing sırasında oluşan genel hata."""
    pass


class EOCDNotFoundError(ZipParseError):
    """End of Central Directory bulunamadığında oluşan hata."""
    pass


class MalformedZipError(ZipParseError):
    """Bozuk ZIP dosyası tespit edildiğinde oluşan hata."""
    pass


class UnsupportedCompressionError(ZipParseError):
    """Desteklenmeyen sıkıştırma yöntemi tespit edildiğinde oluşan hata."""
    pass


# ================================================================================
# MAIN ZIP PARSER CLASS
# ================================================================================

class ZipAyrıştırıcı:
    """
    ZIP dosyalarının binary yapısını ayrıştıran ana sınıf.
    
    Bu sınıf ZIP dosyasının iç yapısını anlayabilir:
    - EOCD (End of Central Directory) bulur
    - Central Directory entries'i okur
    - Local File Headers'ı parse eder
    - Offset tabanlı erişim sağlar
    
    Kullanım:
        with open('dosya.zip', 'rb') as f:
            parser = ZipAyrıştırıcı(f)
            eocd = parser.find_eocd()
            entries = parser.parse_cd_entries(eocd)
    """
    
    def __init__(self, file_handle: BinaryIO):
        """
        ZIP parser'ı başlatır.
        
        Args:
            file_handle: Açılmış ZIP dosyası handle'ı (binary mode)
        """
        self.file_handle = file_handle
        
        # Dosya boyutunu hesapla
        current_pos = self.file_handle.tell()
        self.file_handle.seek(0, 2)  # EOF'a git
        self.file_size = self.file_handle.tell()
        self.file_handle.seek(current_pos)  # Eski pozisyona dön
        
    def find_eocd(self) -> EOCDRecord:
        """
        End of Central Directory Record'ı dosyanın sonundan tarayarak bulur.
        
        ZIP spesifikasyonuna göre EOCD dosyanın sonunda yer alır.
        Maximum 65KB (comment length limit) geriye doğru tarama yapar.
        
        Returns:
            EOCDRecord: Parse edilmiş EOCD yapısı
            
        Raises:
            EOCDNotFoundError: EOCD bulunamazsa
            MalformedZipError: EOCD bozuksa
        """
        # EOCD signature'ı geriye doğru tara
        max_comment_length = 0xFFFF  # 65535 bytes
        search_start = max(0, self.file_size - 22 - max_comment_length)  # Min EOCD size = 22
        search_length = self.file_size - search_start
        
        # Dosyanın sonunu oku
        self.file_handle.seek(search_start)
        data = self.file_handle.read(search_length)
        
        # EOCD signature'ını geriye doğru ara
        signature_bytes = struct.pack('<I', ZipSignatures.EOCD_SIGNATURE)
        
        for i in range(len(data) - 22, -1, -1):  # 22 = minimum EOCD size
            if data[i:i+4] == signature_bytes:
                # EOCD bulundu, parse et
                eocd_offset = search_start + i
                return self._parse_eocd_at_offset(eocd_offset)
        
        raise EOCDNotFoundError("End of Central Directory Record not found")
    
    def _parse_eocd_at_offset(self, offset: int) -> EOCDRecord:
        """
        Belirtilen offset'te EOCD'yi parse eder.
        
        Args:
            offset: EOCD'nin dosyadaki offset'i
            
        Returns:
            EOCDRecord: Parse edilmiş EOCD
        """
        self.file_handle.seek(offset)
        
        try:
            # EOCD fixed part (22 bytes)
            data = self.file_handle.read(22)
            if len(data) < 22:
                raise MalformedZipError("Incomplete EOCD record")
            
            # Struct unpack: little-endian format
            (signature, disk_number, cd_start_disk, cd_entries_on_disk,
             total_cd_entries, cd_size, cd_offset, comment_length) = struct.unpack('<IHHHHIIH', data)
            
            # Comment oku (varsa)
            comment = b""
            if comment_length > 0:
                comment = self.file_handle.read(comment_length)
                if len(comment) != comment_length:
                    raise MalformedZipError("Incomplete EOCD comment")
            
            return EOCDRecord(
                signature=signature,
                disk_number=disk_number,
                cd_start_disk=cd_start_disk,
                cd_entries_on_disk=cd_entries_on_disk,
                total_cd_entries=total_cd_entries,
                cd_size=cd_size,
                cd_offset=cd_offset,
                comment_length=comment_length,
                comment=comment,
                eocd_offset=offset
            )
            
        except struct.error as e:
            raise MalformedZipError(f"Failed to parse EOCD: {e}")
    
    def parse_cd_entries(self, eocd: EOCDRecord) -> List[CentralDirectoryEntry]:
        """
        Central Directory entries'i parse eder.
        
        Args:
            eocd: EOCD record (CD offset bilgisini içerir)
            
        Returns:
            List[CentralDirectoryEntry]: Parse edilmiş CD entries
        """
        entries = []
        cd_offset = eocd.cd_offset
        total_entries = eocd.total_cd_entries
        
        self.file_handle.seek(cd_offset)
        
        for i in range(total_entries):
            try:
                entry_offset = self.file_handle.tell()
                entry = self._parse_cd_entry_at_current_position(entry_offset)
                entries.append(entry)
                
            except Exception as e:
                raise MalformedZipError(f"Failed to parse CD entry {i}: {e}")
        
        return entries
    
    def _parse_cd_entry_at_current_position(self, entry_offset: int) -> CentralDirectoryEntry:
        """
        Mevcut dosya pozisyonunda CD entry'yi parse eder.
        
        Args:
            entry_offset: CD entry'nin dosyadaki offset'i
            
        Returns:
            CentralDirectoryEntry: Parse edilmiş CD entry
        """
        # CD header fixed part (46 bytes)
        data = self.file_handle.read(46)
        if len(data) < 46:
            raise MalformedZipError("Incomplete CD entry header")
        
        # Struct unpack
        (signature, version_made_by, version_needed, flags, compression_method,
         last_mod_time, last_mod_date, crc32, compressed_size, uncompressed_size,
         filename_length, extra_field_length, comment_length, disk_start,
         internal_attrs, external_attrs, local_header_offset) = struct.unpack('<IHHHHHHIIIHHHHHII', data)
        
        # Variable length fields oku
        filename = ""
        if filename_length > 0:
            filename_bytes = self.file_handle.read(filename_length)
            filename = filename_bytes.decode('utf-8', errors='replace')
        
        extra_field = b""
        if extra_field_length > 0:
            extra_field = self.file_handle.read(extra_field_length)
        
        comment = ""
        if comment_length > 0:
            comment_bytes = self.file_handle.read(comment_length)
            comment = comment_bytes.decode('utf-8', errors='replace')
        
        return CentralDirectoryEntry(
            signature=signature,
            version_made_by=version_made_by,
            version_needed=version_needed,
            flags=flags,
            compression_method=compression_method,
            last_mod_time=last_mod_time,
            last_mod_date=last_mod_date,
            crc32=crc32,
            compressed_size=compressed_size,
            uncompressed_size=uncompressed_size,
            filename_length=filename_length,
            extra_field_length=extra_field_length,
            comment_length=comment_length,
            disk_start=disk_start,
            internal_attrs=internal_attrs,
            external_attrs=external_attrs,
            local_header_offset=local_header_offset,
            filename=filename,
            extra_field=extra_field,
            comment=comment,
            cd_entry_offset=entry_offset
        )
    
    def parse_local_file_header(self, cd_entry: CentralDirectoryEntry) -> LocalFileHeader:
        """
        Belirtilen CD entry için Local File Header'ı parse eder.
        
        Args:
            cd_entry: Central Directory entry (offset bilgisini içerir)
            
        Returns:
            LocalFileHeader: Parse edilmiş local file header
        """
        offset = cd_entry.local_header_offset
        return self._parse_local_file_header_at_offset(offset)
    
    def _parse_local_file_header_at_offset(self, offset: int) -> LocalFileHeader:
        """
        Belirtilen offset'te Local File Header'ı parse eder.
        
        Args:
            offset: Local File Header'ın dosyadaki offset'i
            
        Returns:
            LocalFileHeader: Parse edilmiş header
        """
        self.file_handle.seek(offset)
        
        try:
            # Local file header fixed part (30 bytes)
            data = self.file_handle.read(30)
            if len(data) < 30:
                raise MalformedZipError("Incomplete Local File Header")            # Struct unpack
            (signature, version_needed, flags, compression_method, last_mod_time,
             last_mod_date, crc32, compressed_size, uncompressed_size,
             filename_length, extra_field_length) = struct.unpack('<IHHHHHIIIHH', data)
            
            # Variable length fields oku
            filename = ""
            if filename_length > 0:
                filename_bytes = self.file_handle.read(filename_length)
                filename = filename_bytes.decode('utf-8', errors='replace')
            
            extra_field = b""
            if extra_field_length > 0:
                extra_field = self.file_handle.read(extra_field_length)
            
            return LocalFileHeader(
                signature=signature,
                version_needed=version_needed,
                flags=flags,
                compression_method=compression_method,
                last_mod_time=last_mod_time,
                last_mod_date=last_mod_date,
                crc32=crc32,
                compressed_size=compressed_size,
                uncompressed_size=uncompressed_size,
                filename_length=filename_length,
                extra_field_length=extra_field_length,
                filename=filename,
                extra_field=extra_field,
                header_offset=offset
            )
            
        except struct.error as e:
            raise MalformedZipError(f"Failed to parse Local File Header: {e}")


# ================================================================================
# UTILITY FUNCTIONS - TEST VE DEBUG İÇİN
# ================================================================================

def parse_zip_structure(zip_path: Union[str, Path]) -> Tuple[EOCDRecord, List[CentralDirectoryEntry], List[LocalFileHeader]]:
    """
    ZIP dosyasının tüm yapısını parse eder.
    
    Convenience function - test ve debug için kullanışlı.
    
    Args:
        zip_path: ZIP dosyası yolu
        
    Returns:
        Tuple[EOCDRecord, List[CentralDirectoryEntry], List[LocalFileHeader]]:
        EOCD, CD entries ve Local File Headers
    """
    with open(zip_path, 'rb') as f:
        parser = ZipAyrıştırıcı(f)
        
        # EOCD bul
        eocd = parser.find_eocd()
        
        # CD entries parse et
        cd_entries = parser.parse_cd_entries(eocd)
        
        # Local file headers parse et
        local_headers = []
        for cd_entry in cd_entries:
            local_header = parser.parse_local_file_header(cd_entry)
            local_headers.append(local_header)
        
        return eocd, cd_entries, local_headers


def debug_zip_info(zip_path: Union[str, Path]) -> str:
    """
    ZIP dosyası hakkında debug bilgisi üretir.
    
    Args:
        zip_path: ZIP dosyası yolu
        
    Returns:
        str: Formatlanmış debug bilgisi
    """
    try:
        with open(zip_path, 'rb') as f:
            parser = ZipAyrıştırıcı(f)
            
            # EOCD bul
            eocd = parser.find_eocd()
            
            # CD entries parse et
            cd_entries = parser.parse_cd_entries(eocd)
            
            # Local file headers parse et
            local_headers = []
            for cd_entry in cd_entries:
                local_header = parser.parse_local_file_header(cd_entry)
                local_headers.append(local_header)
        
        info = []
        info.append(f"=== ZIP Debug Info: {zip_path} ===")
        info.append(f"Total entries: {eocd.total_cd_entries}")
        info.append(f"Central Directory offset: 0x{eocd.cd_offset:08x}")
        info.append(f"Central Directory size: {eocd.cd_size} bytes")
        info.append(f"EOCD offset: 0x{eocd.eocd_offset:08x}")
        info.append("")
        
        for i, (cd_entry, local_header) in enumerate(zip(cd_entries, local_headers)):
            info.append(f"Entry {i}: {cd_entry.filename}")
            info.append(f"  Compression: {cd_entry.compression_method} ({'store' if cd_entry.compression_method == 0 else 'deflate' if cd_entry.compression_method == 8 else 'unknown'})")
            info.append(f"  Sizes: {cd_entry.uncompressed_size} -> {cd_entry.compressed_size} bytes")
            info.append(f"  CRC32: 0x{cd_entry.crc32:08x}")
            info.append(f"  Local header offset: 0x{cd_entry.local_header_offset:08x}")
            info.append(f"  Data offset: 0x{local_header.data_offset:08x}")
            info.append("")
        
        return "\n".join(info)
        
    except Exception as e:
        return f"Error parsing ZIP: {e}"


if __name__ == "__main__":
    # Test/demo kodu
    import sys
    
    if len(sys.argv) > 1:
        zip_file = sys.argv[1]
        print(debug_zip_info(zip_file))
    else:
        print("Usage: python zip_structs.py <zip_file>")
        print("Example: python zip_structs.py test.zip")
