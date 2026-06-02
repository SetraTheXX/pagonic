"""
Hybrid Fast Path Decompressor - CORRECTED VERSION
================================================

Bu modül dosya boyutuna göre optimal strateji seçer:
- Small files (<10MB): Direct zlib (speed priority)
- Large files (>10MB): Buffer pools (memory priority)

Hedef: Best of both worlds
"""

import zlib
import os
from typing import Optional, BinaryIO, Dict, Any
import logging

try:
    from optimized_decompressor import create_optimized_decompressor
    from adaptive_buffer import get_optimal_buffer_config
    from buffer_pool import get_pools_stats
except ImportError:
    from .optimized_decompressor import create_optimized_decompressor
    from .adaptive_buffer import get_optimal_buffer_config
    from .buffer_pool import get_pools_stats

logger = logging.getLogger(__name__)

class HybridFastPathDecompressor:
    """
    Hybrid decompressor: Fast path for small files, optimized path for large files
    
    Strategy:
    - Files < 10MB: Direct zlib (fast, simple)
    - Files >= 10MB: Buffer pools + adaptive sizing (memory efficient)
    """
    
    def __init__(self, threshold_mb: int = 10, wbits: int = -15):
        self.threshold_bytes = threshold_mb * 1024 * 1024  # 10MB default
        self.wbits = wbits
        
        # Lazy initialization for optimized decompressor
        self._optimized_decompressor = None
        
        # Stats tracking
        self._stats = {
            'fast_path_used': 0,
            'optimized_path_used': 0,
            'fast_path_bytes': 0,
            'optimized_path_bytes': 0,
            'total_files': 0
        }
    
    def reset_stats(self):
        """İstatistikleri sıfırla"""
        self._stats = {
            'fast_path_used': 0,
            'optimized_path_used': 0,
            'fast_path_bytes': 0,
            'optimized_path_bytes': 0,
            'total_files': 0
        }
    
    def _get_optimized_decompressor(self):
        """Lazy initialization of optimized decompressor"""
        if self._optimized_decompressor is None:
            self._optimized_decompressor = create_optimized_decompressor(self.wbits)
        return self._optimized_decompressor
    
    def decompress_data(self, 
                       compressed_data: bytes, 
                       filename: str = "unknown",
                       uncompressed_size: Optional[int] = None) -> bytes:
        """
        Compressed data'yı hybrid strategy ile decompress et
        
        Args:
            compressed_data: Sıkıştırılmış veri
            filename: Dosya adı (logging için)
            uncompressed_size: Beklenen uncompressed boyut
            
        Returns:
            bytes: Decompressed data
        """
        self._stats['total_files'] += 1
        
        # Strategy decision based on uncompressed size (if available) or estimated size
        if uncompressed_size is not None:
            decision_size = uncompressed_size
        else:
            decision_size = len(compressed_data) * 3  # Conservative estimate
        
        if decision_size < self.threshold_bytes:
            # FAST PATH: Direct zlib
            return self._fast_path_decompress(compressed_data, filename, decision_size)
        else:
            # OPTIMIZED PATH: Buffer pools
            return self._optimized_path_decompress(compressed_data, filename, uncompressed_size)
    
    def _fast_path_decompress(self, compressed_data: bytes, filename: str, estimated_size: int) -> bytes:
        """Fast path: Direct zlib decompression"""
        try:
            start_time = logger.isEnabledFor(logging.DEBUG) and logger.getEffectiveLevel() <= logging.DEBUG
            if start_time:
                import time
                start = time.perf_counter()
            
            # Direct zlib decompression
            decompressor = zlib.decompressobj(self.wbits)
            decompressed = decompressor.decompress(compressed_data)
            decompressed += decompressor.flush()
            
            # Update stats
            self._stats['fast_path_used'] += 1
            self._stats['fast_path_bytes'] += len(decompressed)
            
            if start_time:
                duration = time.perf_counter() - start
                throughput = (len(decompressed) / 1024 / 1024) / duration if duration > 0 else 0
                logger.debug(f"🚀 Fast path: {filename} - {len(decompressed)/1024:.1f}KB in {duration:.3f}s ({throughput:.1f} MB/s)")
            
            return decompressed
            
        except zlib.error as e:
            logger.error(f"Fast path decompression failed for {filename}: {e}")
            raise
    
    def _optimized_path_decompress(self, compressed_data: bytes, filename: str, uncompressed_size: Optional[int]) -> bytes:
        """Optimized path: Buffer pools + adaptive sizing"""
        try:
            start_time = logger.isEnabledFor(logging.DEBUG) and logger.getEffectiveLevel() <= logging.DEBUG
            if start_time:
                import time
                start = time.perf_counter()
            
            # Use optimized decompressor
            decompressor = self._get_optimized_decompressor()
            decompressed = decompressor.decompress_to_bytes(
                compressed_data,
                filename=filename,
                expected_size=uncompressed_size
            )
            
            # Update stats
            self._stats['optimized_path_used'] += 1
            self._stats['optimized_path_bytes'] += len(decompressed)
            
            if start_time:
                duration = time.perf_counter() - start
                throughput = (len(decompressed) / 1024 / 1024) / duration if duration > 0 else 0
                logger.debug(f"🎯 Optimized path: {filename} - {len(decompressed)/1024:.1f}KB in {duration:.3f}s ({throughput:.1f} MB/s)")
            
            return decompressed
            
        except Exception as e:
            logger.error(f"Optimized path decompression failed for {filename}: {e}")
            # Fallback to fast path
            logger.info(f"Falling back to fast path for {filename}")
            return self._fast_path_decompress(compressed_data, filename, len(compressed_data) * 3)
    
    def get_stats(self) -> Dict[str, Any]:
        """Decompression istatistiklerini döndür"""
        total_bytes = self._stats['fast_path_bytes'] + self._stats['optimized_path_bytes']
        
        stats = self._stats.copy()
        stats.update({
            'total_bytes_processed': total_bytes,
            'fast_path_percentage': (self._stats['fast_path_bytes'] / total_bytes * 100) if total_bytes > 0 else 0,
            'optimized_path_percentage': (self._stats['optimized_path_bytes'] / total_bytes * 100) if total_bytes > 0 else 0,
            'threshold_mb': self.threshold_bytes / (1024 * 1024)
        })
        
        return stats


# Test script
if __name__ == "__main__":
    print("🚀 Testing Hybrid Fast Path Decompressor...")
    
    import time
    
    # Create test data
    small_data = b"Small test data. " * 10000  # ~170KB  
    large_data = b"Large test data with extensive content. " * 400000  # ~14MB
    
    # Compress with raw deflate (no headers)
    small_compressed = zlib.compress(small_data)[2:-4]  # Remove gzip headers
    large_compressed = zlib.compress(large_data)[2:-4]  # Remove gzip headers
    
    # Create hybrid decompressor
    hybrid = HybridFastPathDecompressor(threshold_mb=10)
    
    # Test small file (should use fast path)
    print(f"\n🚀 Testing small file (fast path expected):")
    start_time = time.perf_counter()
    small_result = hybrid.decompress_data(small_compressed, "small.txt", len(small_data))
    small_duration = time.perf_counter() - start_time
    
    print(f"  Result: {len(small_result)/1024:.1f}KB in {small_duration:.4f}s")
    print(f"  Integrity: {' PASS' if small_result == small_data else '❌ FAIL'}")
    
    # Test large file (should use optimized path)
    print(f"\n🎯 Testing large file (optimized path expected):")
    start_time = time.perf_counter()
    large_result = hybrid.decompress_data(large_compressed, "large.txt", len(large_data))
    large_duration = time.perf_counter() - start_time
    
    print(f"  Result: {len(large_result)/1024/1024:.1f}MB in {large_duration:.4f}s")
    print(f"  Integrity: {' PASS' if large_result == large_data else '❌ FAIL'}")
    
    # Stats
    print(f"\n📊 Hybrid Decompressor Stats:")
    stats = hybrid.get_stats()
    print(f"  Fast path used: {stats['fast_path_used']} files ({stats['fast_path_percentage']:.1f}% of data)")
    print(f"  Optimized path used: {stats['optimized_path_used']} files ({stats['optimized_path_percentage']:.1f}% of data)")
    print(f"  Total files: {stats['total_files']}")
    print(f"  Total data processed: {stats['total_bytes_processed']/1024/1024:.1f}MB")
    print(f"  Threshold: {stats['threshold_mb']}MB")
    
    print(f"\n🏆 Hybrid Fast Path Decompressor ready for integration!")
