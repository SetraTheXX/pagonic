"""
Buffer Pool ve Decompressor Pool Optimizasyonu
==============================================

Bu modül ZIP dosyalarının açılması sırasında bellek fragmentasyonunu önlemek
ve zlib decompressor nesnelerini yeniden kullanmak için geliştirilmiştir.

Gün 8 - Adım 2.3: Akış + Tampon Havuzu + zlib Optimization
Hedef: %50 bellek azaltma + %100-150 hız artışı
"""

import zlib
import threading
from typing import Dict, Optional
from collections import deque
import gc
import logging

logger = logging.getLogger(__name__)

class BufferPool:
    """
    Önceden ayrılmış tampon havuzu - bellek fragmentasyonunu önler
    
    Özellikleri:
    - 64KB - 8MB arası uyarlanabilir tampon boyutları
    - Thread-safe işlemler
    - Automatic cleanup ve memory pressure handling
    - Usage statistics tracking
    """
    
    def __init__(self, max_buffers_per_size: int = 10):
        self.max_buffers_per_size = max_buffers_per_size
        self._pools: Dict[int, deque] = {}
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'created': 0,
            'returned': 0
        }
        
        # Standard buffer sizes (power of 2 for efficiency)
        self.standard_sizes = [
            64 * 1024,    # 64KB - small files
            256 * 1024,   # 256KB - medium files  
            1024 * 1024,  # 1MB - large files
            4 * 1024 * 1024,  # 4MB - very large files
            8 * 1024 * 1024   # 8MB - huge files
        ]
        
        # Pre-allocate some common buffers
        self._preallocate_buffers()
    
    def _preallocate_buffers(self):
        """Yaygın kullanılan tampon boyutlarını önceden ayır"""
        with self._lock:
            for size in self.standard_sizes[:3]:  # İlk 3 boyut için preallocate
                self._pools[size] = deque()
                for _ in range(2):  # Her boyuttan 2 buffer başlat
                    buffer = bytearray(size)
                    self._pools[size].append(buffer)
                    self._stats['created'] += 1
    
    def get_buffer(self, requested_size: int) -> bytearray:
        """
        İstenen boyutta tampon al
        
        Args:
            requested_size: İstenen minimum tampon boyutu
            
        Returns:
            bytearray: Kullanıma hazır tampon
        """
        # En uygun tampon boyutunu bul (power of 2, >= requested_size)
        optimal_size = self._find_optimal_size(requested_size)
        
        with self._lock:
            if optimal_size in self._pools and self._pools[optimal_size]:
                # Pool'dan mevcut buffer al
                buffer = self._pools[optimal_size].popleft()
                self._stats['hits'] += 1
                
                # Buffer'ı temizle (güvenlik için)
                buffer[:] = b'\x00' * len(buffer)
                return buffer
            else:
                # Yeni buffer oluştur
                buffer = bytearray(optimal_size)
                self._stats['misses'] += 1
                self._stats['created'] += 1
                return buffer
    
    def return_buffer(self, buffer: bytearray):
        """
        Kullanılmış tamponu pool'a geri ver
        
        Args:
            buffer: Geri verilecek tampon
        """
        if not buffer:
            return
            
        buffer_size = len(buffer)
        
        with self._lock:
            if buffer_size not in self._pools:
                self._pools[buffer_size] = deque()
            
            # Pool'da çok fazla buffer varsa geri alma
            if len(self._pools[buffer_size]) >= self.max_buffers_per_size:
                # Eski buffer'ları temizle (memory pressure)
                self._pools[buffer_size].popleft()
            
            self._pools[buffer_size].append(buffer)
            self._stats['returned'] += 1
    
    def _find_optimal_size(self, requested_size: int) -> int:
        """İstenen boyut için optimal buffer size bul"""
        for size in self.standard_sizes:
            if size >= requested_size:
                return size
        
        # Standard sizes'dan büyük ise, power of 2'ye yuvarla
        power = 1
        while (1 << power) < requested_size:
            power += 1
        return 1 << power
    
    def get_stats(self) -> Dict:
        """Pool istatistiklerini döndür"""
        with self._lock:
            total_buffers = sum(len(pool) for pool in self._pools.values())
            hit_rate = self._stats['hits'] / (self._stats['hits'] + self._stats['misses']) if (self._stats['hits'] + self._stats['misses']) > 0 else 0
            
            return {
                **self._stats,
                'total_pooled_buffers': total_buffers,
                'hit_rate': hit_rate,
                'pool_sizes': {size: len(pool) for size, pool in self._pools.items()}
            }
    
    def cleanup(self):
        """Memory pressure durumunda pool'u temizle"""
        with self._lock:
            for pool in self._pools.values():
                pool.clear()
            gc.collect()
            logger.info("Buffer pool cleaned up")


class DecompressorPool:
    """
    zlib.decompressobj nesnelerini yeniden kullanım için pool
    
    Özellikleri:
    - Thread-safe decompressor object pooling
    - Different compression levels support
    - Automatic cleanup ve memory management
    - Performance metrics tracking
    """
    
    def __init__(self, max_decompressors: int = 20):
        self.max_decompressors = max_decompressors
        self._pools: Dict[int, deque] = {}  # wbits -> decompressor pool
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'created': 0,
            'returned': 0,
            'active': 0
        }
        
        # Common wbits values for ZIP
        self.common_wbits = [-15, -9, 15, 9]  # Raw deflate ve standard deflate
        
        # Pre-create some decompressors
        self._preallocate_decompressors()
    
    def _preallocate_decompressors(self):
        """Yaygın kullanılan decompressor'ları önceden oluştur"""
        with self._lock:
            for wbits in self.common_wbits:
                self._pools[wbits] = deque()
                # Raw deflate (-15) için daha fazla preallocate
                count = 3 if wbits == -15 else 1
                for _ in range(count):
                    try:
                        decompressor = zlib.decompressobj(wbits)
                        self._pools[wbits].append(decompressor)
                        self._stats['created'] += 1
                    except Exception as e:
                        logger.warning(f"Failed to preallocate decompressor for wbits={wbits}: {e}")
    
    def get_decompressor(self, wbits: int = -15):
        """
        Decompressor nesnesi al
        
        Args:
            wbits: zlib window bits (ZIP için genelde -15)
            
        Returns:
            zlib decompressor object: Kullanıma hazır decompressor
        """
        with self._lock:
            if wbits in self._pools and self._pools[wbits]:
                # Pool'dan mevcut decompressor al
                decompressor = self._pools[wbits].popleft()
                self._stats['hits'] += 1
                self._stats['active'] += 1
                return decompressor
            else:
                # Yeni decompressor oluştur
                try:
                    decompressor = zlib.decompressobj(wbits)
                    self._stats['misses'] += 1
                    self._stats['created'] += 1
                    self._stats['active'] += 1
                    return decompressor
                except Exception as e:
                    logger.error(f"Failed to create decompressor with wbits={wbits}: {e}")
                    raise
    
    def return_decompressor(self, decompressor, wbits: int = -15):
        """
        Kullanılmış decompressor'ı pool'a geri ver
        
        Args:
            decompressor: Geri verilecek decompressor
            wbits: Decompressor'ın wbits değeri
        """
        if not decompressor:
            return
        
        try:
            with self._lock:
                if wbits not in self._pools:
                    self._pools[wbits] = deque()
                
                # Pool'da çok fazla decompressor varsa ekleme
                if len(self._pools[wbits]) < self.max_decompressors:
                    try:
                        new_decompressor = zlib.decompressobj(wbits)
                        self._pools[wbits].append(new_decompressor)
                        self._stats['returned'] += 1
                    except Exception as e:
                        logger.warning(f"Failed to create replacement decompressor: {e}")
                
                self._stats['active'] = max(0, self._stats['active'] - 1)
                
        except Exception as e:
            logger.warning(f"Failed to return decompressor: {e}")
    
    def get_stats(self) -> Dict:
        """Pool istatistiklerini döndür"""
        with self._lock:
            total_pooled = sum(len(pool) for pool in self._pools.values())
            hit_rate = self._stats['hits'] / (self._stats['hits'] + self._stats['misses']) if (self._stats['hits'] + self._stats['misses']) > 0 else 0
            
            return {
                **self._stats,
                'total_pooled_decompressors': total_pooled,
                'hit_rate': hit_rate,
                'pool_sizes': {wbits: len(pool) for wbits, pool in self._pools.items()}
            }
    
    def cleanup(self):
        """Memory pressure durumunda pool'u temizle"""
        with self._lock:
            for pool in self._pools.values():
                pool.clear()
            self._stats['active'] = 0
            gc.collect()
            logger.info("Decompressor pool cleaned up")


# Global singletons
_buffer_pool: Optional[BufferPool] = None
_decompressor_pool: Optional[DecompressorPool] = None
_pool_lock = threading.Lock()

def get_buffer_pool() -> BufferPool:
    """Global buffer pool instance döndür"""
    global _buffer_pool
    if _buffer_pool is None:
        with _pool_lock:
            if _buffer_pool is None:
                _buffer_pool = BufferPool()
    return _buffer_pool

def get_decompressor_pool() -> DecompressorPool:
    """Global decompressor pool instance döndür"""
    global _decompressor_pool
    if _decompressor_pool is None:
        with _pool_lock:
            if _decompressor_pool is None:
                _decompressor_pool = DecompressorPool()
    return _decompressor_pool

def get_pools_stats() -> Dict:
    """Her iki pool'un istatistiklerini döndür"""
    return {
        'buffer_pool': get_buffer_pool().get_stats(),
        'decompressor_pool': get_decompressor_pool().get_stats()
    }

def cleanup_pools():
    """Memory pressure durumunda her iki pool'u temizle"""
    if _buffer_pool:
        _buffer_pool.cleanup()
    if _decompressor_pool:
        _decompressor_pool.cleanup()


if __name__ == "__main__":
    # Test ve demo
    print("=== Buffer Pool ve Decompressor Pool Test ===")
    
    # Buffer pool test
    buffer_pool = get_buffer_pool()
    print(" Buffer pool oluşturuldu")
    
    # Buffer al ve geri ver
    buffer1 = buffer_pool.get_buffer(100 * 1024)  # 100KB
    buffer2 = buffer_pool.get_buffer(1024 * 1024)  # 1MB
    
    print(f"📦 Buffer 1 size: {len(buffer1):,} bytes ({len(buffer1)//1024}KB)")
    print(f"📦 Buffer 2 size: {len(buffer2):,} bytes ({len(buffer2)//1024//1024}MB)")
    
    buffer_pool.return_buffer(buffer1)
    buffer_pool.return_buffer(buffer2)
    
    print("📊 Buffer pool stats:", buffer_pool.get_stats())
    
    # Decompressor pool test
    decompressor_pool = get_decompressor_pool()
    print("\n Decompressor pool oluşturuldu")
    
    # Decompressor al ve geri ver
    decomp1 = decompressor_pool.get_decompressor(-15)
    decomp2 = decompressor_pool.get_decompressor(-15)
    
    print(f"🔧 Decompressor 1: {type(decomp1).__name__}")
    print(f"🔧 Decompressor 2: {type(decomp2).__name__}")
    
    decompressor_pool.return_decompressor(decomp1, -15)
    decompressor_pool.return_decompressor(decomp2, -15)
    
    print("📊 Decompressor pool stats:", decompressor_pool.get_stats())
    
    # Combined stats
    print("\n📈 Final combined stats:")
    combined_stats = get_pools_stats()
    print(f"Buffer pool hit rate: {combined_stats['buffer_pool']['hit_rate']:.1%}")
    print(f"Decompressor pool hit rate: {combined_stats['decompressor_pool']['hit_rate']:.1%}")
    print(f"Total pooled buffers: {combined_stats['buffer_pool']['total_pooled_buffers']}")
    print(f"Total pooled decompressors: {combined_stats['decompressor_pool']['total_pooled_decompressors']}")
