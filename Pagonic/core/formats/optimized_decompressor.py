"""
Optimized Streaming Decompression
=================================

Bu modül buffer pool ve adaptive sizing kullanarak
optimize edilmiş streaming decompression sağlar.

Hedef: Memory efficient + fast decompression
"""

import zlib
import io
from typing import BinaryIO, Iterator, Tuple, Optional, Dict, Any
import logging

try:
    from buffer_pool import get_buffer_pool, get_decompressor_pool
    from adaptive_buffer import get_optimal_buffer_config
except ImportError:
    from .buffer_pool import get_buffer_pool, get_decompressor_pool
    from .adaptive_buffer import get_optimal_buffer_config

logger = logging.getLogger(__name__)

class OptimizedStreamDecompressor:
    """
    Buffer pool ve adaptive sizing kullanarak optimize edilmiş streaming decompressor
    
    Özellikler:
    - Automatic buffer size optimization
    - Memory pool reuse
    - Chunk-based processing
    - Progress tracking
    - Memory pressure handling
    """
    
    def __init__(self, wbits: int = -15):
        self.wbits = wbits
        self.buffer_pool = get_buffer_pool()
        self.decompressor_pool = get_decompressor_pool()
        self._stats = {
            'total_compressed': 0,
            'total_decompressed': 0,
            'chunks_processed': 0,
            'buffer_reuses': 0,
            'decompressor_reuses': 0
        }
    
    def decompress_stream(self, 
                         compressed_data: bytes, 
                         filename: str = "unknown",
                         expected_size: Optional[int] = None) -> Iterator[Tuple[bytes, Dict[str, Any]]]:
        """
        Compressed data'yı streaming şekilde decompress et
        
        Args:
            compressed_data: Sıkıştırılmış veri
            filename: Dosya adı (adaptive sizing için)
            expected_size: Beklenen uncompressed boyut
            
        Yields:
            Tuple[bytes, Dict]: (decompressed_chunk, progress_info)
        """
        # Optimal buffer configuration al
        config = get_optimal_buffer_config(filename, len(compressed_data))
        buffer_size = config['buffer_size']
        chunk_size = config['chunk_size']
        
        logger.debug(f"Decompressing {filename}: buffer={buffer_size//1024}KB, chunk={chunk_size//1024}KB")
        
        # Pool'dan resources al
        buffer = self.buffer_pool.get_buffer(buffer_size)
        decompressor = self.decompressor_pool.get_decompressor(self.wbits)
        
        try:
            # Compressed data stream oluştur
            compressed_stream = io.BytesIO(compressed_data)
            
            total_processed = 0
            total_output = 0
            chunk_count = 0
            
            while True:
                # Compressed data chunk oku
                compressed_chunk = compressed_stream.read(chunk_size)
                if not compressed_chunk:
                    break
                
                try:
                    # Decompress chunk
                    decompressed_chunk = decompressor.decompress(compressed_chunk)
                    
                    if decompressed_chunk:
                        # Buffer'a kopyala (safety için)
                        output_size = len(decompressed_chunk)
                        if output_size <= len(buffer):
                            buffer[:output_size] = decompressed_chunk
                            output_data = bytes(buffer[:output_size])
                        else:
                            # Chunk buffer'dan büyükse direkt kullan
                            output_data = decompressed_chunk
                        
                        total_processed += len(compressed_chunk)
                        total_output += output_size
                        chunk_count += 1
                        
                        # Progress info
                        progress = {
                            'chunk_number': chunk_count,
                            'compressed_processed': total_processed,
                            'decompressed_output': total_output,
                            'compression_ratio': total_output / total_processed if total_processed > 0 else 1.0,
                            'progress_percent': (total_processed / len(compressed_data)) * 100 if len(compressed_data) > 0 else 0,
                            'buffer_config': config
                        }
                        
                        yield output_data, progress
                
                except zlib.error as e:
                    logger.error(f"Decompression error in chunk {chunk_count}: {e}")
                    break
            
            # Final flush
            try:
                final_data = decompressor.flush()
                if final_data:
                    total_output += len(final_data)
                    progress = {
                        'chunk_number': chunk_count + 1,
                        'compressed_processed': total_processed,
                        'decompressed_output': total_output,
                        'compression_ratio': total_output / total_processed if total_processed > 0 else 1.0,
                        'progress_percent': 100.0,
                        'is_final': True,
                        'buffer_config': config
                    }
                    yield final_data, progress
            except zlib.error as e:
                logger.warning(f"Final flush error: {e}")
            
            # Update stats
            self._stats['total_compressed'] += len(compressed_data)
            self._stats['total_decompressed'] += total_output
            self._stats['chunks_processed'] += chunk_count
            self._stats['buffer_reuses'] += 1
            self._stats['decompressor_reuses'] += 1
            
        finally:
            # Resources'ları pool'a geri ver
            self.buffer_pool.return_buffer(buffer)
            self.decompressor_pool.return_decompressor(decompressor, self.wbits)
    
    def decompress_to_bytes(self, 
                           compressed_data: bytes, 
                           filename: str = "unknown",
                           expected_size: Optional[int] = None) -> bytes:
        """
        Compressed data'yı tek seferde bytes olarak decompress et
        
        Args:
            compressed_data: Sıkıştırılmış veri
            filename: Dosya adı
            expected_size: Beklenen boyut
            
        Returns:
            bytes: Decompressed data
        """
        result_chunks = []
        total_size = 0
        
        for chunk, progress in self.decompress_stream(compressed_data, filename, expected_size):
            result_chunks.append(chunk)
            total_size += len(chunk)
        
        logger.debug(f"Decompressed {filename}: {len(compressed_data):,} -> {total_size:,} bytes")
        return b''.join(result_chunks)
    
    def decompress_to_file(self, 
                          compressed_data: bytes, 
                          output_file: BinaryIO, 
                          filename: str = "unknown",
                          expected_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Compressed data'yı dosyaya streaming şekilde decompress et
        
        Args:
            compressed_data: Sıkıştırılmış veri
            output_file: Output file handle
            filename: Dosya adı
            expected_size: Beklenen boyut
            
        Returns:
            Dict: Decompression summary
        """
        total_written = 0
        chunk_count = 0
        final_compression_ratio = 1.0
        
        for chunk, progress in self.decompress_stream(compressed_data, filename, expected_size):
            output_file.write(chunk)
            total_written += len(chunk)
            chunk_count += 1
            final_compression_ratio = progress['compression_ratio']
        
        summary = {
            'compressed_size': len(compressed_data),
            'decompressed_size': total_written,
            'compression_ratio': final_compression_ratio,
            'chunks_processed': chunk_count,
            'filename': filename
        }
        
        logger.info(f"File decompressed: {filename} - {len(compressed_data):,} -> {total_written:,} bytes ({final_compression_ratio:.2f}x)")
        return summary
    
    def get_stats(self) -> Dict[str, Any]:
        """Decompressor istatistiklerini döndür"""
        return {
            **self._stats,
            'buffer_pool_stats': self.buffer_pool.get_stats(),
            'decompressor_pool_stats': self.decompressor_pool.get_stats()
        }
    
    def reset_stats(self):
        """İstatistikleri sıfırla"""
        self._stats = {
            'total_compressed': 0,
            'total_decompressed': 0,
            'chunks_processed': 0,
            'buffer_reuses': 0,
            'decompressor_reuses': 0
        }


def create_optimized_decompressor(wbits: int = -15) -> OptimizedStreamDecompressor:
    """
    Optimized decompressor instance oluştur
    
    Args:
        wbits: zlib window bits (ZIP için -15)
        
    Returns:
        OptimizedStreamDecompressor: Hazır decompressor
    """
    return OptimizedStreamDecompressor(wbits)


if __name__ == "__main__":
    # Test ve demo
    print("=== Optimized Stream Decompressor Test ===")
      # Test data oluştur
    original_data = b"Hello, World! " * 1000  # 14KB test data
    # ZIP-compatible compression (raw deflate)
    compressor = zlib.compressobj(level=6, wbits=-15)
    compressed_data = compressor.compress(original_data)
    compressed_data += compressor.flush()
    
    print(f"📦 Test data: {len(original_data):,} bytes -> {len(compressed_data):,} bytes ({len(compressed_data)/len(original_data):.2f}x compression)")
    
    # Optimized decompressor test
    decompressor = create_optimized_decompressor()
    
    print(f"\n🚀 Streaming decompression test:")
    chunk_count = 0
    total_output = 0
    
    for chunk, progress in decompressor.decompress_stream(compressed_data, "test.txt"):
        chunk_count += 1
        total_output += len(chunk)
        print(f"  Chunk {chunk_count}: {len(chunk):,} bytes ({progress['progress_percent']:.1f}% complete)")
    
    print(f" Streaming complete: {chunk_count} chunks, {total_output:,} bytes total")
    
    # Direct decompression test
    print(f"\n⚡ Direct decompression test:")
    decompressed = decompressor.decompress_to_bytes(compressed_data, "test.txt")
    print(f" Direct complete: {len(decompressed):,} bytes")
    print(f"🔍 Data integrity: {' PASS' if decompressed == original_data else '❌ FAIL'}")
    
    # Stats
    print(f"\n📊 Decompressor stats:")
    stats = decompressor.get_stats()
    print(f"  Total compressed: {stats['total_compressed']:,} bytes")
    print(f"  Total decompressed: {stats['total_decompressed']:,} bytes")
    print(f"  Chunks processed: {stats['chunks_processed']}")
    print(f"  Buffer reuses: {stats['buffer_reuses']}")
    print(f"  Buffer pool hit rate: {stats['buffer_pool_stats']['hit_rate']:.1%}")
    print(f"  Decompressor pool hit rate: {stats['decompressor_pool_stats']['hit_rate']:.1%}")
    
    print(f"\n🏆 Optimized streaming decompressor ready!")
