"""
Pagonic Path Utilities - Cross-Platform Path Handling
=====================================================
Provides path normalization and sanitization for ZIP archives.

Day 18-20: Phase 2 Unicode & Path Handling implementation.

Features:
- Cross-platform path normalization (Windows/Linux)
- Drive letter stripping
- Directory traversal prevention
- UTF-8 path support
"""

import os
from pathlib import Path
from typing import Optional


class PagonicPathPolicy:
    """Pagonic internal path normalization rules for ZIP archives.
    
    All paths inside Pagonic archives follow these rules:
    - Always use forward slash (/) as separator
    - No absolute paths (strip leading / or drive letters)
    - No directory traversal (..)
    - Maximum path length: 255 characters
    """
    
    SEPARATOR = '/'
    MAX_PATH_LENGTH = 255
    
    @staticmethod
    def normalize(path: str) -> str:
        """Normalize path for ZIP archive (preserves directory structure).
        
        Transforms:
        - Windows: C:\\foo\\bar → foo/bar
        - Linux: /foo/bar → foo/bar
        - Traversal: ../safe-name -> safe-name
        
        Args:
            path: Raw filesystem path
            
        Returns:
            Normalized archive path
        """
        if not path:
            return ''
        
        # 1. Normalize separators (backslash → forward slash)
        normalized = path.replace('\\', '/')
        
        # 2. Strip drive letters (C:, D:, etc.)
        if len(normalized) > 1 and normalized[1] == ':':
            normalized = normalized[2:]
        
        # 3. Strip UNC paths (//server/share → server/share)
        while normalized.startswith('//'):
            normalized = normalized[2:]
        
        # 4. Strip leading/trailing slashes
        normalized = normalized.strip('/')
        
        # 5. Remove directory traversal (..)
        parts = []
        for part in normalized.split('/'):
            if part == '..':
                continue  # Skip traversal
            if part == '.':
                continue  # Skip current dir
            if part:  # Skip empty parts
                parts.append(part)
        
        # 6. Reconstruct
        result = '/'.join(parts)
        
        # 7. Enforce length limit
        if len(result) > PagonicPathPolicy.MAX_PATH_LENGTH:
            result = result[:PagonicPathPolicy.MAX_PATH_LENGTH]
        
        return result
    
    @staticmethod
    def is_safe_path(path: str, target_dir: str) -> bool:
        """Check if extracted path is safe (no directory traversal).
        
        Prevents attacks like: ../../../etc/passwd
        
        Args:
            path: Path from ZIP archive
            target_dir: Extraction target directory
            
        Returns:
            True if path is safe, False if traversal detected
        """
        # Normalize both paths
        target_abs = os.path.abspath(target_dir)
        full_path = os.path.abspath(os.path.join(target_dir, path))
        
        # Check if resolved path is within target
        return full_path.startswith(target_abs)
    
    @staticmethod
    def join_archive_path(*parts: str) -> str:
        """Join path parts using archive separator (/).
        
        Args:
            *parts: Path components to join
            
        Returns:
            Joined archive path
        """
        return '/'.join(p.strip('/') for p in parts if p)


def normalize_archive_path(path: str) -> str:
    """Convenience function for path normalization.
    
    Args:
        path: Raw path to normalize
        
    Returns:
        Normalized archive path
    """
    return PagonicPathPolicy.normalize(path)


def is_safe_extraction_path(path: str, target_dir: str) -> bool:
    """Convenience function for path safety check.
    
    Args:
        path: Path from archive
        target_dir: Extraction target
        
    Returns:
        True if safe
    """
    return PagonicPathPolicy.is_safe_path(path, target_dir)
