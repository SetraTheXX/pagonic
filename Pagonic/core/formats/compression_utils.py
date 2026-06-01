# -*- coding: utf-8 -*-
"""
compression_utils.py - ZIP Compression Utility Functions

Bu modül ZIP sıkıştırma işlemleri için yardımcı fonksiyonları içerir.
zip_handler.py'den çıkarılarak modüler bir yapıya kavuşturulmuştur.

Created: 2026-01-09 (Phase 1 - Day 5)
"""

import logging
import zlib
from typing import Optional, Dict, Any, Tuple

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from .constants import ZipConstants, MemoryThresholds
from .simd_crc32 import fast_crc32

# Logging setup
logger = logging.getLogger(__name__)


# =============================================================================
# CRC32 Functions
# =============================================================================

def calculate_crc32(data: bytes, initial: int = 0) -> int:
    """
    Calculate CRC32 checksum with SIMD acceleration if available.
    
    Args:
        data: Data to calculate CRC32 for
        initial: Initial CRC32 value (default 0)
        
    Returns:
        int: CRC32 checksum value
    """
    return fast_crc32(data, initial)


def calculate_crc32_streaming(file_handle, chunk_size: int = None) -> int:
    """
    Calculate CRC32 for a file using streaming (memory efficient).
    
    Args:
        file_handle: Open file handle in binary mode
        chunk_size: Chunk size for reading (default: auto-selected)
        
    Returns:
        int: CRC32 checksum of the file
    """
    if chunk_size is None:
        chunk_size = select_chunk_size()
    
    crc = 0
    while True:
        chunk = file_handle.read(chunk_size)
        if not chunk:
            break
        crc = zlib.crc32(chunk, crc)
    
    return crc & 0xFFFFFFFF


# =============================================================================
# Memory Management Functions
# =============================================================================

def get_available_memory_gb() -> float:
    """
    Get available system memory in GB.
    
    Returns:
        float: Available memory in GB
    """
    if PSUTIL_AVAILABLE:
        return psutil.virtual_memory().available / (1024 ** 3)
    else:
        # Fallback: Assume 8GB available
        return 8.0


def get_total_memory_gb() -> float:
    """
    Get total system memory in GB.
    
    Returns:
        float: Total memory in GB
    """
    if PSUTIL_AVAILABLE:
        return psutil.virtual_memory().total / (1024 ** 3)
    else:
        # Fallback: Assume 16GB total
        return 16.0


def select_chunk_size(ram_gb: float = None) -> int:
    """
    Adaptive chunk size selection based on available RAM.
    
    Args:
        ram_gb: RAM amount in GB (auto-detected if None)
        
    Returns:
        int: Optimal chunk size in bytes
    """
    if ram_gb is None:
        ram_gb = get_total_memory_gb()

    if ram_gb >= MemoryThresholds.HIGH_MEMORY_GB:
        return ZipConstants.CHUNK_SIZE_LARGE
    elif ram_gb >= MemoryThresholds.MEDIUM_MEMORY_GB:
        return ZipConstants.CHUNK_SIZE_MEDIUM
    else:
        return ZipConstants.CHUNK_SIZE_SMALL


def select_buffer_size(file_size: int, available_memory_bytes: int = None) -> int:
    """
    Select optimal buffer size based on file size and available memory.
    
    Args:
        file_size: Size of file to process
        available_memory_bytes: Available memory (auto-detected if None)
        
    Returns:
        int: Optimal buffer size in bytes
    """
    if available_memory_bytes is None:
        available_memory_bytes = int(get_available_memory_gb() * 1024 ** 3)
    
    # Use at most 10% of available memory for buffer
    max_buffer = min(available_memory_bytes // 10, ZipConstants.MAX_BUFFER_SIZE)
    
    # Use at least the minimum buffer size
    buffer_size = max(ZipConstants.MIN_BUFFER_SIZE, min(file_size, max_buffer))
    
    return buffer_size


# =============================================================================
# Compression Level Functions
# =============================================================================

def validate_compression_level(level: int) -> int:
    """
    Validate and clamp compression level to valid range (1-9).
    
    Args:
        level: Requested compression level
        
    Returns:
        int: Valid compression level (clamped to 1-9)
    """
    return max(
        ZipConstants.MIN_COMPRESSION_LEVEL,
        min(ZipConstants.MAX_COMPRESSION_LEVEL, level)
    )


def select_compression_level(file_size: int, speed_priority: bool = False) -> int:
    """
    Select optimal compression level based on file size and priority.
    
    Args:
        file_size: Size of file in bytes
        speed_priority: True for faster compression, False for better ratio
        
    Returns:
        int: Recommended compression level
    """
    if speed_priority:
        # Speed priority: Use lower compression levels
        if file_size > ZipConstants.GB_THRESHOLD_2GB:
            return 1  # Fastest for very large files
        elif file_size > ZipConstants.MB_THRESHOLD_100MB:
            return 3  # Fast for large files
        else:
            return 5  # Moderate for normal files
    else:
        # Ratio priority: Use higher compression levels
        if file_size > ZipConstants.GB_THRESHOLD_2GB:
            return 6  # Balanced for very large files
        elif file_size > ZipConstants.MB_THRESHOLD_100MB:
            return 7  # Good compression for large files
        else:
            return 9  # Best compression for normal files


# =============================================================================
# ZIP64 Detection Functions
# =============================================================================

def should_use_zip64(total_size: int, file_count: int) -> bool:
    """
    Determine if ZIP64 format is required.
    
    ZIP64 is needed when:
    - Total uncompressed size exceeds 4GB
    - File count exceeds 65535
    
    Args:
        total_size: Total uncompressed size in bytes
        file_count: Number of files in archive
        
    Returns:
        bool: True if ZIP64 should be used
    """
    return (total_size > ZipConstants.ZIP64_SIZE_LIMIT or
            file_count > ZipConstants.ZIP64_FILE_COUNT_LIMIT)


def estimate_compressed_size(original_size: int, compression_level: int = 6) -> int:
    """
    Estimate compressed size based on typical compression ratios.
    
    Args:
        original_size: Original file size in bytes
        compression_level: Compression level (1-9)
        
    Returns:
        int: Estimated compressed size in bytes
    """
    # Typical compression ratios by level (approximate)
    ratio_map = {
        1: 0.85,  # ~15% compression
        2: 0.75,
        3: 0.65,
        4: 0.55,
        5: 0.50,
        6: 0.45,  # Default - ~55% compression
        7: 0.42,
        8: 0.40,
        9: 0.38,  # Best - ~62% compression
    }
    
    ratio = ratio_map.get(compression_level, 0.45)
    return int(original_size * ratio)


# =============================================================================
# Smart Compression Functions (Phase 2 - Day 21)
# =============================================================================

def calculate_entropy(data: bytes) -> float:
    """Calculate Shannon entropy of data.
    
    Entropy indicates randomness/compressibility:
    - 0.0 = Highly repetitive (very compressible)
    - 1.0 = Completely random (incompressible)
    
    Args:
        data: Sample data to analyze
        
    Returns:
        float: Normalized entropy (0.0 to 1.0)
    """
    import math
    
    if not data:
        return 0.0
    
    # Count byte frequencies
    freq = [0] * 256
    for byte in data:
        freq[byte] += 1
    
    # Calculate Shannon entropy
    entropy = 0.0
    length = len(data)
    for count in freq:
        if count > 0:
            p = count / length
            entropy -= p * math.log2(p)
    
    # Normalize to 0-1 (max entropy is 8 bits)
    return entropy / 8.0


def smart_select_compression_level(file_path: str, file_size: int, 
                                   sample_data: bytes = None) -> int:
    """Smart compression level selection using 3-factor analysis.
    
    Factors:
    1. Extension (50% weight) - Known file types
    2. Entropy (30% weight) - Sample randomness
    3. Size (20% weight) - File size thresholds
    
    Args:
        file_path: Path to file
        file_size: Size of file in bytes
        sample_data: Optional first 4KB sample for entropy analysis
        
    Returns:
        int: Recommended compression level (0-9)
    """
    import os
    
    ext = os.path.splitext(file_path)[1].lower()
    
    # Pre-compressed formats - STORE only
    pre_compressed = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.mp4', '.mp3',
                      '.zip', '.rar', '.7z', '.gz', '.bz2', '.xz'}
    if ext in pre_compressed:
        return 0  # STORE mode
    
    # High compressibility text formats
    high_compress = {'.txt', '.json', '.xml', '.html', '.css', '.js', '.md',
                     '.csv', '.log', '.yaml', '.yml'}
    if ext in high_compress:
        return 9  # Maximum compression
    
    # Source code - good compression
    source_code = {'.py', '.c', '.cpp', '.h', '.java', '.rs', '.go', '.ts',
                   '.rb', '.php', '.swift', '.kt'}
    if ext in source_code:
        return 7  # Good compression
    
    # Use entropy if sample data provided
    if sample_data:
        entropy = calculate_entropy(sample_data)
        
        if entropy > 0.9:
            # Very random (encrypted/compressed) - use STORE
            return 0
        elif entropy > 0.7:
            # Moderately random - light compression
            return 3
        elif entropy < 0.3:
            # Highly repetitive - maximum compression
            return 9
    
    # Size-based fallback
    if file_size < 1024 * 1024:  # <1MB
        return 6  # Fast for small files
    elif file_size < 100 * 1024 * 1024:  # <100MB
        return 5  # Balanced
    else:
        return 3  # Fast for large files


def adaptive_compress(data: bytes, level: int = 6) -> Tuple[bytes, int]:
    """Compress data with automatic fallback to STORE mode.
    
    Detects negative compression (where compressed size > original)
    and automatically falls back to STORE mode.
    
    Args:
        data: Raw data to compress
        level: Compression level (1-9)
        
    Returns:
        Tuple of (compressed_data, method) where method is:
        - 0 = STORE (uncompressed)
        - 8 = DEFLATE (compressed)
    """
    if level == 0:
        return data, 0  # STORE mode requested
    
    # Try compression
    compressed = zlib.compress(data, level)
    
    # Negative compression check (2% tolerance)
    if len(compressed) >= len(data) * 0.98:
        logger.debug("Negative compression detected, using STORE mode "
                    f"({len(data)} -> {len(compressed)} bytes)")
        return data, 0  # STORE mode
    
    return compressed, 8  # DEFLATE


def get_file_entropy_sample(file_path: str, sample_size: int = 4096) -> float:
    """Get entropy of a file by sampling first N bytes.
    
    Args:
        file_path: Path to file
        sample_size: Bytes to sample (default 4KB)
        
    Returns:
        float: Entropy of sample (0.0 to 1.0)
    """
    try:
        with open(file_path, 'rb') as f:
            sample = f.read(sample_size)
        return calculate_entropy(sample)
    except (IOError, OSError):
        return 0.5  # Unknown - assume medium entropy


# =============================================================================
# File Type Detection
# =============================================================================

def is_compressible_file(filename: str) -> bool:
    """
    Check if a file type is likely to benefit from compression.
    
    Args:
        filename: Name of file to check
        
    Returns:
        bool: True if file should be compressed
    """
    # Already compressed formats - skip compression
    incompressible_extensions = {
        '.zip', '.rar', '.7z', '.gz', '.bz2', '.xz',
        '.jpg', '.jpeg', '.png', '.gif', '.webp', '.mp4',
        '.mp3', '.aac', '.flac', '.ogg', '.avi', '.mkv',
        '.pdf', '.docx', '.xlsx', '.pptx'
    }
    
    ext = filename.lower()
    for incomp_ext in incompressible_extensions:
        if ext.endswith(incomp_ext):
            return False
    
    return True


def get_optimal_strategy_for_file(filename: str, file_size: int) -> Dict[str, Any]:
    """
    Get optimal compression strategy for a specific file.
    
    Args:
        filename: Name of file
        file_size: Size of file in bytes
        
    Returns:
        Dict containing compression parameters
    """
    is_compressible = is_compressible_file(filename)
    
    if not is_compressible:
        return {
            'compression_level': 0,  # Store only
            'chunk_size': ZipConstants.CHUNK_SIZE_LARGE,
            'use_threading': False,
            'reason': 'Already compressed file type'
        }
    
    # Large file optimization
    if file_size > ZipConstants.GB_THRESHOLD_2GB:
        return {
            'compression_level': 6,
            'chunk_size': ZipConstants.CHUNK_SIZE_LARGE,
            'use_threading': True,
            'use_mmap': True,
            'reason': 'Large file - using mmap and threading'
        }
    
    # Medium file optimization
    if file_size > ZipConstants.MB_THRESHOLD_100MB:
        return {
            'compression_level': 6,
            'chunk_size': ZipConstants.CHUNK_SIZE_MEDIUM,
            'use_threading': True,
            'use_mmap': False,
            'reason': 'Medium file - using threading'
        }
    
    # Small file - standard compression
    return {
        'compression_level': ZipConstants.DEFAULT_COMPRESSION_LEVEL,
        'chunk_size': ZipConstants.CHUNK_SIZE_DEFAULT,
        'use_threading': False,
        'use_mmap': False,
        'reason': 'Small file - standard compression'
    }


# =============================================================================
# Performance Statistics
# =============================================================================

def calculate_compression_ratio(original_size: int, compressed_size: int) -> float:
    """
    Calculate compression ratio.
    
    Args:
        original_size: Original file size
        compressed_size: Compressed file size
        
    Returns:
        float: Compression ratio (e.g., 2.5 means 2.5:1 compression)
    """
    if compressed_size == 0:
        return 0.0
    return original_size / compressed_size


def format_size(size_bytes: int) -> str:
    """
    Format byte size to human-readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Human-readable size (e.g., "1.5 GB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def get_compression_stats(original_size: int, compressed_size: int, 
                         elapsed_time: float) -> Dict[str, Any]:
    """
    Get comprehensive compression statistics.
    
    Args:
        original_size: Original file size
        compressed_size: Compressed file size
        elapsed_time: Time taken for compression
        
    Returns:
        Dict with compression statistics
    """
    ratio = calculate_compression_ratio(original_size, compressed_size)
    savings = original_size - compressed_size
    savings_percent = (savings / original_size * 100) if original_size > 0 else 0
    throughput = original_size / elapsed_time if elapsed_time > 0 else 0
    
    return {
        'original_size': original_size,
        'compressed_size': compressed_size,
        'original_size_formatted': format_size(original_size),
        'compressed_size_formatted': format_size(compressed_size),
        'ratio': ratio,
        'savings_bytes': savings,
        'savings_percent': savings_percent,
        'elapsed_seconds': elapsed_time,
        'throughput_bytes_per_sec': throughput,
        'throughput_formatted': format_size(int(throughput)) + '/s'
    }
