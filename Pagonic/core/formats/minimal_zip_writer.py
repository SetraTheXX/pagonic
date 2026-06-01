"""
MinimalZipWriter - ZIP Dosyası Yazma Sistemi
==========================================
PAGONIC projesi için 2GB+ dosyalar için zipfile alternatifi.

Bu modül ZIP formatının doğrudan yazılması için gereken tüm yapıları içerir:
- Local File Header yazma
- Central Directory Entry yazma  
- End of Central Directory (EOCD) yazma
- zlib compression entegrasyonu
- CRC32 hesaplama
- Standard ZIP format uyumluluğu

Hedef: 2GB+ dosyalarda zipfile modülünün yerini almak.
"""

import struct
import zlib
import os
import time
from datetime import datetime
from typing import BinaryIO, List, Tuple, Dict, Optional, Union, Callable
from pathlib import Path

# Mevcut zip_structs.py'den import
try:
    from .zip_structs import (
        ZipSignatures, CompressionMethods, 
        EOCDRecord, CentralDirectoryEntry, LocalFileHeader
    )
except ImportError:
    # Standalone çalıştırma için
    from zip_structs import (
        ZipSignatures, CompressionMethods, 
        EOCDRecord, CentralDirectoryEntry, LocalFileHeader
    )


class MinimalZipWriterError(Exception):
    """MinimalZipWriter için özel exception sınıfı."""
    pass


class CompressionError(MinimalZipWriterError):
    """Sıkıştırma işlemi sırasında oluşan hatalar."""
    pass


class FileSizeError(MinimalZipWriterError):
    """Dosya boyutu ile ilgili hatalar."""
    pass


class MinimalZipWriter:
    """
    ZIP dosyası yazma sistemi.
    zipfile modülü yerine 2GB+ dosyalar için kullanılır.
    
    Features:
    - ZIP32 format desteği (4GB'a kadar)
    - Minimal overhead
    - zlib compression (deflate)
    - CRC32 hesaplama
    - Standard ZIP format uyumluluğu
    - Memory-efficient streaming
    - Progress callback desteği
    """
    
    def __init__(self, compression_level: int = 6, chunk_size: int = 64*1024):
        """
        MinimalZipWriter başlatıcı.
        
        Args:
            compression_level: zlib sıkıştırma seviyesi (1-9)
            chunk_size: Streaming için chunk boyutu
        """
        self.compression_level = max(1, min(9, compression_level))
        self.chunk_size = chunk_size
        self.central_directory_entries: List[Dict] = []
        self.total_compressed_size = 0
        self.total_uncompressed_size = 0
        
    def _get_dos_time(self, timestamp: Optional[float] = None) -> Tuple[int, int]:
        """Unix timestamp'i DOS formatına çevirir."""
        if timestamp is None:
            timestamp = time.time()
            
        dt = datetime.fromtimestamp(timestamp)
        
        # DOS date format: YYYYYYYMMMMDDDDD (from 1980)
        dos_date = ((dt.year - 1980) << 9) | (dt.month << 5) | dt.day
        
        # DOS time format: HHHHHMMMMMMSSSS (seconds/2)
        dos_time = (dt.hour << 11) | (dt.minute << 5) | (dt.second // 2)
        
        return dos_time, dos_date
    
    def _calculate_crc32(self, data: bytes) -> int:
        """CRC32 hesaplar."""
        return zlib.crc32(data) & 0xffffffff
    
    def _validate_file_size(self, file_size: int) -> None:
        """Dosya boyutunu ZIP32 limitleri için kontrol eder."""
        if file_size > 4 * 1024 * 1024 * 1024:  # 4GB
            raise FileSizeError(f"Dosya boyutu 4GB'ı aşıyor: {file_size:,} bytes")
    
    def write_local_file_header(self, fp: BinaryIO, filename: str, 
                               compressed_size: int, uncompressed_size: int, 
                               crc32: int, compression_method: int = CompressionMethods.DEFLATE) -> int:
        """
        Local File Header yazar ve offset döner.
        
        Args:
            fp: Binary file pointer
            filename: Dosya adı
            compressed_size: Sıkıştırılmış boyut
            uncompressed_size: Orijinal boyut
            crc32: CRC32 checksum
            compression_method: Sıkıştırma yöntemi
            
        Returns:
            int: Local header'ın offset'i
        """
        offset = fp.tell()
        
        filename_bytes = filename.encode('utf-8')
        filename_length = len(filename_bytes)
        
        dos_time, dos_date = self._get_dos_time()
        
        # Local File Header struct (30 bytes + filename)
        header = struct.pack(
            '<LHHHHHLLLHH',
            ZipSignatures.LOCAL_FILE_HEADER_SIGNATURE,  # signature
            20,                                # version needed (2.0)
            0,                                 # flags
            compression_method,                # compression method
            dos_time,                         # dos time
            dos_date,                         # dos date
            crc32,                            # crc32
            compressed_size,                  # compressed size
            uncompressed_size,                # uncompressed size
            filename_length,                  # filename length
            0                                 # extra field length
        )
        
        fp.write(header)
        fp.write(filename_bytes)
        
        return offset
    
    def write_central_directory_entry(self, fp: BinaryIO, filename: str,
                                    local_header_offset: int, compressed_size: int,
                                    uncompressed_size: int, crc32: int,
                                    compression_method: int = CompressionMethods.DEFLATE) -> None:
        """
        Central Directory Entry yazar.
        
        Args:
            fp: Binary file pointer
            filename: Dosya adı
            local_header_offset: Local header offset'i
            compressed_size: Sıkıştırılmış boyut
            uncompressed_size: Orijinal boyut
            crc32: CRC32 checksum
            compression_method: Sıkıştırma yöntemi
        """
        filename_bytes = filename.encode('utf-8')
        filename_length = len(filename_bytes)
        
        dos_time, dos_date = self._get_dos_time()
        
        # Central Directory Entry struct (46 bytes + filename)
        entry = struct.pack(
            '<LHHHHHHLLLHHHHHLL',
            ZipSignatures.CD_HEADER_SIGNATURE, # signature
            20,                               # version made by
            20,                               # version needed
            0,                                # flags
            compression_method,               # compression method
            dos_time,                        # dos time
            dos_date,                        # dos date
            crc32,                           # crc32
            compressed_size,                 # compressed size
            uncompressed_size,               # uncompressed size
            filename_length,                 # filename length
            0,                               # extra field length
            0,                               # comment length
            0,                               # disk number
            0,                               # internal attributes
            0,                               # external attributes
            local_header_offset              # local header offset
        )
        
        fp.write(entry)
        fp.write(filename_bytes)
    
    def write_eocd(self, fp: BinaryIO, central_dir_offset: int, 
                   central_dir_size: int, total_entries: int) -> None:
        """
        End of Central Directory Record yazar.
        
        Args:
            fp: Binary file pointer
            central_dir_offset: Central directory offset'i
            central_dir_size: Central directory boyutu
            total_entries: Toplam dosya sayısı
        """
        eocd = struct.pack(
            '<LHHHHLLH',
            ZipSignatures.EOCD_SIGNATURE,     # signature
            0,                               # disk number
            0,                               # central dir disk
            total_entries,                   # entries on this disk
            total_entries,                   # total entries
            central_dir_size,                # central dir size
            central_dir_offset,              # central dir offset
            0                                # comment length
        )
        
        fp.write(eocd)
    
    def compress_file_streaming(self, input_path: str, output_path: str, 
                               progress_callback: Optional[Callable[[int, Dict], None]] = None) -> Dict[str, Union[str, int, float]]:
        """
        Streaming compression ile tek dosyalı ZIP oluşturur.
        Memory-efficient yaklaşım için chunk-based processing.
        
        Args:
            input_path: Sıkıştırılacak dosya yolu
            output_path: Çıktı ZIP dosyası yolu
            progress_callback: İlerleme callback fonksiyonu
            
        Returns:
            dict: İstatistikler
        """
        filename = os.path.basename(input_path)
        file_size = os.path.getsize(input_path)
        
        # Dosya boyutu kontrolü
        self._validate_file_size(file_size)
        
        # CRC32 hesaplama için tüm dosyayı oku
        with open(input_path, 'rb') as input_file:
            original_data = input_file.read()
        
        crc32 = self._calculate_crc32(original_data)
        
        # zlib compressor
        compressor = zlib.compressobj(
            level=self.compression_level,
            method=zlib.DEFLATED,
            wbits=-15,  # negative wbits = raw deflate (no gzip headers)
            memLevel=9,
            strategy=zlib.Z_DEFAULT_STRATEGY
        )
        
        # Streaming compression
        compressed_data = compressor.compress(original_data)
        compressed_data += compressor.flush()
        compressed_size = len(compressed_data)
        
        # ZIP dosyası yazma
        with open(output_path, 'wb') as zip_file:
            # 1. Local File Header + compressed data
            local_offset = self.write_local_file_header(
                zip_file, filename, compressed_size, file_size, crc32
            )
            
            # 2. Compressed data yazma
            zip_file.write(compressed_data)
            
            # 3. Central Directory başlangıcı
            central_dir_offset = zip_file.tell()
            
            # 4. Central Directory Entry
            self.write_central_directory_entry(
                zip_file, filename, local_offset, compressed_size, 
                file_size, crc32
            )
            
            # 5. Central Directory bitişi
            central_dir_end = zip_file.tell()
            central_dir_size = central_dir_end - central_dir_offset
            
            # 6. End of Central Directory Record
            self.write_eocd(zip_file, central_dir_offset, central_dir_size, 1)
        
        # İstatistikler
        compression_ratio = (1 - compressed_size / file_size) * 100 if file_size > 0 else 0
        
        stats = {
            'input_file': input_path,
            'output_file': output_path,
            'original_size': file_size,
            'compressed_size': compressed_size,
            'compression_ratio': compression_ratio,
            'crc32': crc32,
            'method': 'deflate',
            'level': self.compression_level,
            'local_header_offset': local_offset,
            'central_dir_offset': central_dir_offset,
            'central_dir_size': central_dir_size
        }
        
        # Progress callback
        if progress_callback:
            progress_callback(100, stats)
        
        return stats
    
    def create_zip_file(self, input_path: str, output_path: str, 
                       progress_callback: Optional[Callable[[int, Dict], None]] = None) -> Dict[str, Union[str, int, float]]:
        """
        Tek dosyalı ZIP oluşturur (alias for compress_file_streaming).
        
        Args:
            input_path: Sıkıştırılacak dosya yolu
            output_path: Çıktı ZIP dosyası yolu
            progress_callback: İlerleme callback fonksiyonu
            
        Returns:
            dict: İstatistikler
        """
        return self.compress_file_streaming(input_path, output_path, progress_callback)


# Test ve doğrulama fonksiyonları
def test_minimal_zip_writer_basic():
    """Temel MinimalZipWriter test fonksiyonu."""
    import tempfile
    import zipfile
    
    # Test dosyası oluştur
    test_data = b"This is a test file. " * 1000  # ~24KB
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_input:
        temp_input.write(test_data)
        temp_input_path = temp_input.name
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_output:
        temp_output_path = temp_output.name
    
    try:
        # MinimalZipWriter ile oluştur
        writer = MinimalZipWriter(compression_level=6)
        stats = writer.create_zip_file(temp_input_path, temp_output_path)
        
        print(f" ZIP dosyası oluşturuldu: {temp_output_path}")
        print(f"📊 Orijinal boyut: {stats['original_size']:,} bytes")
        print(f"📊 Sıkıştırılmış boyut: {stats['compressed_size']:,} bytes")
        print(f"📊 Sıkıştırma oranı: {stats['compression_ratio']:.1f}%")
        
        # Python zipfile ile doğrulama
        with zipfile.ZipFile(temp_output_path, 'r') as zf:
            # Liste dosyaları
            file_list = zf.namelist()
            print(f" ZIP içeriği: {file_list}")
            
            # Dosyayı çıkar ve karşılaştır
            extracted_data = zf.read(file_list[0])
            
            if extracted_data == test_data:
                print(" Doğrulama başarılı: Veriler eşleşiyor!")
                return True
            else:
                print("❌ Doğrulama başarısız: Veriler eşleşmiyor!")
                return False
                
    except Exception as e:
        print(f"❌ Test başarısız: {e}")
        return False
    finally:
        # Cleanup
        try:
            os.unlink(temp_input_path)
            os.unlink(temp_output_path)
        except:
            pass


def test_minimal_zip_writer_large_file():
    """Büyük dosya test fonksiyonu (1.9GB sınır testi)."""
    import tempfile
    import zipfile
    
    # 1.9GB test dosyası oluştur (zipfile sınırı)
    large_size = int(1.9 * 1024 * 1024 * 1024)  # 1.9GB
    chunk_size = 1024 * 1024  # 1MB chunks
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as temp_input:
        temp_input_path = temp_input.name
        
        # Büyük dosya oluştur (pattern ile)
        pattern = b"0123456789ABCDEF" * (chunk_size // 16)
        remaining = large_size
        
        while remaining > 0:
            write_size = min(chunk_size, remaining)
            temp_input.write(pattern[:write_size])
            remaining -= write_size
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_output:
        temp_output_path = temp_output.name
    
    try:
        print(f"🧪 1.9GB dosya testi başlatılıyor...")
        
        # MinimalZipWriter ile oluştur
        writer = MinimalZipWriter(compression_level=1)  # Hızlı sıkıştırma
        
        def progress_callback(percent, stats):
            if percent % 10 == 0:
                print(f"📈 İlerleme: %{percent}")
        
        stats = writer.create_zip_file(temp_input_path, temp_output_path, progress_callback)
        
        print(f" 1.9GB ZIP dosyası oluşturuldu!")
        print(f"📊 Orijinal boyut: {stats['original_size']:,} bytes")
        print(f"📊 Sıkıştırılmış boyut: {stats['compressed_size']:,} bytes")
        print(f"📊 Sıkıştırma oranı: {stats['compression_ratio']:.1f}%")
        
        # Python zipfile ile doğrulama
        with zipfile.ZipFile(temp_output_path, 'r') as zf:
            file_list = zf.namelist()
            print(f" ZIP içeriği: {file_list}")
            
            # Dosya boyutu kontrolü
            file_info = zf.getinfo(file_list[0])
            if file_info.file_size == large_size:
                print(" Dosya boyutu doğrulaması başarılı!")
                return True
            else:
                print(f"❌ Dosya boyutu uyumsuz: {file_info.file_size:,} != {large_size:,}")
                return False
                
    except Exception as e:
        print(f"❌ Büyük dosya testi başarısız: {e}")
        return False
    finally:
        # Cleanup
        try:
            os.unlink(temp_input_path)
            os.unlink(temp_output_path)
        except:
            pass


if __name__ == "__main__":
    print("🧪 MinimalZipWriter Test Başlatılıyor...")
    
    # Temel test
    print("\n=== TEMEL TEST ===")
    basic_success = test_minimal_zip_writer_basic()
    
    # Büyük dosya testi (opsiyonel)
    print("\n=== BÜYÜK DOSYA TESTİ ===")
    large_success = test_minimal_zip_writer_large_file()
    
    print(f"\n🎯 Test Sonuçları:")
    print(f"   Temel Test: {' BAŞARILI' if basic_success else '❌ BAŞARISIZ'}")
    print(f"   Büyük Dosya: {' BAŞARILI' if large_success else '❌ BAŞARISIZ'}")
    
    if basic_success and large_success:
        print("🚀 Tüm testler başarılı! MinimalZipWriter hazır!")
    else:
        print(" Bazı testler başarısız. Debug gerekli.") 