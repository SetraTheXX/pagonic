"""
SIMD Memory Copy ve Alignment Modülü
====================================

Bu modül, büyük buffer'lar için platforma özel hızlı memory copy (memcpy) ve alignment fonksiyonları sağlar.
Amaç: Paralel extraction ve decompression path'lerinde maksimum memory throughput elde etmek.
"""

import platform
import ctypes
import numpy as np
from typing import Union

# Platform detection
def is_x86():
    arch = platform.machine().lower()
    return 'x86' in arch or 'amd64' in arch or 'i386' in arch

def is_arm():
    arch = platform.machine().lower()
    return 'arm' in arch or 'aarch64' in arch

# Hızlı memory copy (SIMD veya numpy ile)
def fast_memcpy(dst: Union[bytearray, memoryview], src: Union[bytes, bytearray, memoryview], size: int) -> None:
    """
    Platforma özel hızlı memory copy fonksiyonu.
    - x86: numpy.copyto veya ctypes.memmove
    - ARM: numpy.copyto veya ctypes.memmove
    - Fallback: Python slice assignment
    """
    try:
        # Numpy ile hızlı copy (en hızlısı çoğu platformda)
        np.copyto(np.frombuffer(dst, dtype=np.uint8, count=size), np.frombuffer(src, dtype=np.uint8, count=size))
        return
    except Exception:
        pass
    try:
        # ctypes ile low-level memcpy
        dst_ptr = (ctypes.c_char * size).from_buffer(dst)
        src_ptr = (ctypes.c_char * size).from_buffer_copy(src)
        ctypes.memmove(dst_ptr, src_ptr, size)
        return
    except Exception:
        pass
    # Fallback: Python slice assignment
    dst[:size] = src[:size]

# Alignment helper (ör. 16/32/64 byte alignment)
def align_address(addr: int, alignment: int = 32) -> int:
    """Verilen adresi yukarıya doğru alignment'a yuvarlar."""
    return (addr + (alignment - 1)) & ~(alignment - 1)

# Test fonksiyonu
def test_fast_memcpy():
    import time
    size = 10 * 1024 * 1024  # 10MB
    src = bytearray([1] * size)
    dst = bytearray(size)
    t0 = time.perf_counter()
    fast_memcpy(dst, src, size)
    t1 = time.perf_counter()
    assert dst == src, "fast_memcpy failed!"
    print(f"fast_memcpy 10MB: {t1-t0:.6f} s")

if __name__ == "__main__":
    test_fast_memcpy() 