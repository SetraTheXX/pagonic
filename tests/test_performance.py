"""
Performans ve Memory Testleri (Optimizasyon ve Otomasyon)
"""
import os
import time
import psutil
import pytest
from core.compression import (
    CompressionWorkerPool, MemoryPool, ChunkCache, ProgressTracker, StreamingCompressor
)

def dummy_compress(chunk: bytes) -> bytes:
    # Gerçek sıkıştırma yerine sadece chunk'ı döndür (test için)
    return chunk

def test_parallel_compress_speed(tmp_path):
    # 16MB'lık 16 adet chunk ile paralel hız testi
    chunk_size = 1024 * 1024
    num_chunks = 16
    data = [os.urandom(chunk_size) for _ in range(num_chunks)]
    pool = CompressionWorkerPool(max_workers=4)
    start = time.time()
    results = pool.parallel_compress([lambda d=d: dummy_compress(d) for d in data])
    elapsed = time.time() - start
    pool.shutdown()
    assert len(results) == num_chunks
    
    # ZeroDivisionError koruması ekle
    if elapsed > 0:
        speed = (chunk_size * num_chunks) / 1024 / 1024 / elapsed
        print(f"Parallel compress speed: {speed:.2f} MB/s")
        assert speed > 10  # Minimum referans hız
    else:
        # Çok hızlı işlemler için fallback
        print("Parallel compress speed: TOO_FAST_TO_MEASURE")
        assert True  # Test passed - operation was extremely fast

def test_memory_pool_efficiency():
    pool = MemoryPool(chunk_size=1024*1024, max_chunks=8)
    chunks = [pool.acquire() for _ in range(8)]
    for c in chunks:
        pool.release(c)
    assert pool.pool_size() == 8
    # Yeniden acquire/release ile memory reuse test edilir
    c = pool.acquire()
    pool.release(c)
    assert pool.pool_size() == 8

def test_chunk_cache_lru():
    cache = ChunkCache(max_size=4)
    for i in range(6):
        cache.put(f"k{i}", bytes([i]))
    assert len(cache) == 4
    assert "k0" not in cache  # LRU ilk çıkar
    assert "k5" in cache

def test_streaming_compressor(tmp_path):
    # 8MB'lık bir dosyayı streaming ile sıkıştırma simülasyonu
    input_file = tmp_path / "input.bin"
    output_file = tmp_path / "output.bin"
    with open(input_file, "wb") as f:
        f.write(os.urandom(8 * 1024 * 1024))
    progress = ProgressTracker(total=8)
    compressor = StreamingCompressor(chunk_size=1024*1024)
    compressor.compress_stream(str(input_file), str(output_file), dummy_compress, progress)
    assert os.path.getsize(output_file) == os.path.getsize(input_file)
    assert progress.is_done()

def test_memory_usage_benchmark():
    # Basit memory usage ölçümü (psutil ile)
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss
    pool = MemoryPool(chunk_size=1024*1024, max_chunks=16)
    chunks = [pool.acquire() for _ in range(16)]
    for c in chunks:
        pool.release(c)
    mem_after = process.memory_info().rss
    # Pool kullanımı ile memory artışı çok düşük olmalı
    assert (mem_after - mem_before) < 32 * 1024 * 1024  # 32MB'dan az artış
