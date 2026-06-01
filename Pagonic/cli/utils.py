"""
CLI Utility Functions
=====================
Helper functions for the Pagonic CLI.
"""

from typing import Union


def format_size(size_bytes: Union[int, float]) -> str:
    """
    Format byte size to human-readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string like "1.5 MB" or "256 KB"
    
    Examples:
        >>> format_size(1024)
        '1.0 KB'
        >>> format_size(1048576)
        '1.0 MB'
        >>> format_size(1073741824)
        '1.0 GB'
    """
    if size_bytes < 0:
        return "Invalid"
    
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} B"
    
    return f"{size:.1f} {units[unit_index]}"


def format_time(seconds: float) -> str:
    """
    Format seconds to human-readable time string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string like "1.5s" or "2m 30s"
    
    Examples:
        >>> format_time(0.5)
        '0.50s'
        >>> format_time(90)
        '1m 30s'
    """
    if seconds < 0:
        return "Invalid"
    
    if seconds < 60:
        return f"{seconds:.2f}s"
    
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    
    if minutes < 60:
        return f"{minutes}m {remaining_seconds}s"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    return f"{hours}h {remaining_minutes}m"


def format_ratio(original: int, compressed: int) -> str:
    """
    Calculate and format compression ratio.
    
    Args:
        original: Original size in bytes
        compressed: Compressed size in bytes
        
    Returns:
        Formatted ratio like "45.2%" or "N/A"
    """
    if original <= 0:
        return "N/A"
    
    if compressed <= 0:
        return "100%"
    
    ratio = (1 - compressed / original) * 100
    
    if ratio < 0:
        return f"-{abs(ratio):.1f}%"  # Expansion
    
    return f"{ratio:.1f}%"


def validate_compression_level(level: int) -> int:
    """
    Validate and clamp compression level to valid range.
    
    Args:
        level: Requested compression level
        
    Returns:
        Valid compression level (0-9)
    """
    if level < 0:
        return 0
    if level > 9:
        return 9
    return level


# Quick test
if __name__ == "__main__":
    print("Testing CLI Utils...")
    
    # Test format_size
    assert format_size(0) == "0 B"
    assert format_size(1024) == "1.0 KB"
    assert format_size(1048576) == "1.0 MB"
    print(" format_size works")
    
    # Test format_time
    assert format_time(0.5) == "0.50s"
    assert format_time(90) == "1m 30s"
    print(" format_time works")
    
    # Test format_ratio
    assert format_ratio(100, 50) == "50.0%"
    assert format_ratio(0, 50) == "N/A"
    print(" format_ratio works")
    
    print("\n All CLI utils tests passed!")
