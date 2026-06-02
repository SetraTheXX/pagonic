"""
Security Module for ZIP Operations
==================================
Provides protection against:
- ZIP bomb attacks (decompression bombs)
- Path traversal attacks (directory traversal)
- Malicious file names
- Size limit violations
"""

from pathlib import Path
import zipfile
from typing import Optional

# Import errors - try relative first, then absolute
try:
    from .errors import SecurityError, ValidationError
except ImportError:
    from Pagonic.core.formats.errors import SecurityError, ValidationError


class ZipConstants:
    """Security-related constants for ZIP validation."""

    MAX_UNCOMPRESSED_SIZE = 10 * 1024 ** 3  # 10GB uncompressed limit
    MAX_COMPRESSION_RATIO = 10000  # 1:10000 compression ratio limit (ZIP bomb detection)
    # Note: Increased from 1000 to 10000 to prevent false positives on 
    # highly compressible text/repeated data. Real ZIP bombs typically
    # have ratios of 100,000:1 or higher.
    MAX_PATH_LENGTH = 256  # Maximum filename length
    MAX_FILES_IN_ZIP = 100000  # Maximum number of files in ZIP


def validate_zip_safety(zip_path: Path) -> None:
    """
    Validate ZIP file safety (ZIP bomb protection).

    Checks:
    1. Total uncompressed size doesn't exceed MAX_UNCOMPRESSED_SIZE
    2. Compression ratio for each file doesn't exceed MAX_COMPRESSION_RATIO
    3. Total number of files doesn't exceed MAX_FILES_IN_ZIP

    Args:
        zip_path: Path to ZIP file to validate

    Raises:
        SecurityError: If ZIP file fails security validation
        ValidationError: If ZIP file is corrupted or invalid
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            total_uncompressed = 0
            file_count = 0

            for info in zf.infolist():
                file_count += 1

                # Check total file count (billion laughs protection)
                if file_count > ZipConstants.MAX_FILES_IN_ZIP:
                    raise SecurityError(
                        f"ZIP file contains too many files: {file_count} files "
                        f"(limit: {ZipConstants.MAX_FILES_IN_ZIP})"
                    )

                # Check total uncompressed size
                total_uncompressed += info.file_size
                if total_uncompressed > ZipConstants.MAX_UNCOMPRESSED_SIZE:
                    raise SecurityError(
                        f"ZIP file exceeds uncompressed size limit: "
                        f"{total_uncompressed:,} bytes "
                        f"(limit: {ZipConstants.MAX_UNCOMPRESSED_SIZE:,} bytes)"
                    )

                # Check compression ratio (ZIP bomb detection)
                if info.file_size > 0 and info.compress_size > 0:
                    ratio = info.file_size / max(info.compress_size, 1)
                    if ratio > ZipConstants.MAX_COMPRESSION_RATIO:
                        raise SecurityError(
                            f"Suspicious compression ratio detected: "
                            f"{ratio:.1f}:1 for file '{info.filename}' "
                            f"(limit: {ZipConstants.MAX_COMPRESSION_RATIO}:1) - "
                            f"Possible ZIP bomb attack"
                        )

    except zipfile.BadZipFile as e:
        raise ValidationError(f"Invalid or corrupted ZIP file: {e}")
    except FileNotFoundError:
        raise ValidationError(f"ZIP file not found: {zip_path}")


def sanitize_path(file_path: str) -> str:
    """
    Prevent path traversal attacks by sanitizing file paths.

    Security measures:
    1. Extract basename only (remove directory components)
    2. Remove dangerous characters (.., /, \\)
    3. Validate filename length
    4. Reject hidden files (starting with .)
    5. Reject empty filenames

    Args:
        file_path: User-provided file path (potentially malicious)

    Returns:
        Sanitized filename (safe to use)

    Raises:
        ValidationError: If filename is invalid or dangerous
    """
    normalized_path = str(file_path).replace('\\', '/')
    filename = normalized_path.rsplit('/', 1)[-1]

    # Remove dangerous path separators and traversal patterns
    filename = filename.replace('..', '').replace('/', '').replace('\\', '')

    # Additional security: remove null bytes
    filename = filename.replace('\x00', '')

    # Validate length
    if len(filename) > ZipConstants.MAX_PATH_LENGTH:
        raise ValidationError(
            f"Filename too long: {len(filename)} characters "
            f"(limit: {ZipConstants.MAX_PATH_LENGTH})"
        )

    # Reject hidden files or empty names
    if not filename:
        raise ValidationError(f"Invalid or empty filename: '{file_path}'")

    if filename.startswith('.'):
        raise ValidationError(
            f"Hidden files not allowed: '{filename}' "
            f"(filenames starting with '.' are rejected)"
        )

    return filename


def secure_extract_path(zip_filename: str, target_dir: str) -> str:
    """
    Securely resolve extraction path to prevent Zip Slip attacks.
    
    This function prevents path traversal by:
    1. Normalizing the path to remove ../ and other traversal patterns
    2. Resolving the absolute path
    3. Verifying the resolved path is within the target directory
    
    Args:
        zip_filename: Filename from ZIP archive (potentially malicious)
        target_dir: Target extraction directory
    
    Returns:
        Safe absolute path for extraction
    
    Raises:
        SecurityError: If path would escape target directory
    """
    clean_name = str(zip_filename).replace('\\', '/')
    clean_name = clean_name.lstrip('/')
    
    # Replace Windows absolute paths (C:\) 
    if len(clean_name) >= 2 and clean_name[1] == ':':
        clean_name = clean_name[2:].lstrip('/')
    
    # Remove any .. components by rebuilding path
    parts = []
    for part in clean_name.split('/'):
        if part in ('', '.'):
            continue
        elif part == '..':
            # Don't allow going up - skip this component
            continue
        else:
            parts.append(part)
    
    if not parts:
        raise SecurityError(f"Invalid path after sanitization: '{zip_filename}'")
    
    safe_name = '/'.join(parts)
    
    # Resolve paths
    target_path = Path(target_dir).resolve()
    final_path = (target_path / safe_name).resolve()
    
    # CRITICAL: Verify the final path is within target directory
    try:
        final_path.relative_to(target_path)
    except ValueError:
        raise SecurityError(
            f"Path traversal detected! '{zip_filename}' would escape to '{final_path}'"
        )
    
    return str(final_path)


def validate_zip_structure(zip_path: Path) -> bool:
    """
    Validate ZIP file structure integrity.

    Uses zipfile.testzip() to verify:
    - ZIP file format is correct
    - All files can be extracted
    - CRC checksums are valid
    - No corrupted data

    Args:
        zip_path: Path to ZIP file to validate

    Returns:
        True if ZIP structure is valid

    Raises:
        ValidationError: If ZIP structure is corrupted or invalid
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # testzip() returns None if all files are OK, or name of first bad file
            bad_file = zf.testzip()
            if bad_file:
                raise ValidationError(
                    f"Corrupted file detected in ZIP: '{bad_file}'"
                )
        return True

    except zipfile.BadZipFile as e:
        raise ValidationError(f"Invalid ZIP file format: {e}")
    except FileNotFoundError:
        raise ValidationError(f"ZIP file not found: {zip_path}")


def is_safe_filename(filename: str) -> bool:
    """
    Check if filename is safe (no path traversal or special characters).

    Args:
        filename: Filename to check

    Returns:
        True if filename is safe, False otherwise
    """
    # Check for path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        return False

    # Check for null bytes
    if '\x00' in filename:
        return False

    # Check for hidden files
    if filename.startswith('.'):
        return False

    # Check length
    if len(filename) > ZipConstants.MAX_PATH_LENGTH:
        return False

    # Check not empty
    if not filename:
        return False

    return True


# Export all public functions and classes
__all__ = [
    'ZipConstants',
    'validate_zip_safety',
    'sanitize_path',
    'secure_extract_path',
    'validate_zip_structure',
    'is_safe_filename',
]
