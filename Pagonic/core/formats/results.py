"""Typed result contracts for the public ZIP APIs.

The runtime APIs continue to return ordinary dictionaries for compatibility.
These ``TypedDict`` definitions make their stable keys available to editors,
type checkers, and downstream integrations without adding a runtime wrapper.
"""

from typing import List, TypedDict


class FileInfo(TypedDict):
    """Metadata returned for one archive entry."""

    filename: str
    compressed_size: int
    uncompressed_size: int
    compression_method: int
    crc32: int


class ExtractionFailure(TypedDict):
    """Failure information for an entry that could not be extracted."""

    filename: str
    error: str


class ExtractionResult(TypedDict):
    """Result shape returned by ``ZipReader.extract_all``."""

    total_entries: int
    success: List[str]
    failed: List[ExtractionFailure]


class ArchiveInfo(TypedDict):
    """Aggregate metadata returned by ``ZipReader.get_archive_info``."""

    path: str
    file_count: int
    total_compressed_size: int
    total_uncompressed_size: int
    compression_ratio: float


class CompressionStats(TypedDict):
    """Statistics returned by ``ZipWriter.finalize``."""

    backend: str
    files_processed: int
    total_compressed_size: int
    total_uncompressed_size: int
    compression_ratio: float


__all__ = [
    "ArchiveInfo",
    "CompressionStats",
    "ExtractionFailure",
    "ExtractionResult",
    "FileInfo",
]
