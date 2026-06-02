# -*- coding: utf-8 -*-
"""
constants.py - ZIP Engine Configuration Constants

Bu modül ZIP işlemleri için kullanılan tüm sabit değerleri içerir.
Merkezi bir konumda tutularak kod tekrarını önler ve bakımı kolaylaştırır.

"""


class ZipConstants:
    """ZIP engine configuration constants."""

    # =========================================================================
    # File Size Thresholds
    # =========================================================================
    GB_THRESHOLD_2GB = 2 * 1024 ** 3      # 2GB - Large file threshold
    GB_THRESHOLD_4GB = 4 * 1024 ** 3      # 4GB - ZIP64 threshold
    MB_THRESHOLD_10MB = 10 * 1024 ** 2    # 10MB - Medium file threshold
    MB_THRESHOLD_100MB = 100 * 1024 ** 2  # 100MB - Streaming threshold

    # =========================================================================
    # Chunk Sizes (Memory-based)
    # =========================================================================
    CHUNK_SIZE_LARGE = 8 * 1024 ** 2    # 8MB - For systems with 16GB+ RAM
    CHUNK_SIZE_MEDIUM = 4 * 1024 ** 2   # 4MB - For systems with 8-16GB RAM
    CHUNK_SIZE_SMALL = 1 * 1024 ** 2    # 1MB - For systems with <8GB RAM
    CHUNK_SIZE_DEFAULT = 1 * 1024 ** 2  # 1MB - Default chunk size

    # =========================================================================
    # Compression Levels
    # =========================================================================
    DEFAULT_COMPRESSION_LEVEL = 6  # Balanced speed/ratio
    MIN_COMPRESSION_LEVEL = 1      # Fastest compression
    MAX_COMPRESSION_LEVEL = 9      # Best compression ratio

    # =========================================================================
    # Buffer Configuration
    # =========================================================================
    DEFAULT_BUFFER_SIZE = 64 * 1024       # 64KB default buffer
    MAX_BUFFER_SIZE = 16 * 1024 ** 2      # 16MB max buffer
    MIN_BUFFER_SIZE = 4 * 1024            # 4KB min buffer

    # =========================================================================
    # ZIP64 Limits
    # =========================================================================
    ZIP64_SIZE_LIMIT = 4 * 1024 ** 3      # 4GB - Standard ZIP limit
    ZIP64_FILE_COUNT_LIMIT = 65535        # 16-bit file count limit

    # =========================================================================
    # Performance Tuning
    # =========================================================================
    DEFAULT_THREAD_COUNT = 4              # Default parallel threads
    MAX_THREAD_COUNT = 16                 # Maximum threads
    PREFETCH_SIZE = 2 * 1024 ** 2         # 2MB prefetch for streaming


class CompressionStrategy:
    """Compression strategy constants."""

    Z_DEFAULT_STRATEGY = 0
    Z_FILTERED = 1
    Z_HUFFMAN_ONLY = 2
    Z_RLE = 3
    Z_FIXED = 4


class MemoryThresholds:
    """Memory-based thresholds for optimization."""

    LOW_MEMORY_GB = 4      # Low memory threshold
    MEDIUM_MEMORY_GB = 8   # Medium memory threshold
    HIGH_MEMORY_GB = 16    # High memory threshold
    VERY_HIGH_MEMORY_GB = 32  # Very high memory threshold
