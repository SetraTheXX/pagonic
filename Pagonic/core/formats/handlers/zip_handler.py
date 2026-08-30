"""Compatibility adapter for the historical ``ZipHandler`` API.

New code should use :class:`ZipReader`, :class:`ZipWriter`, and the inspection
service directly.  This module keeps the small handler contract used by older
callers while routing archive work through those public components.
"""

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import FormatHandler
from ..errors import CompressionError, SecurityError, ValidationError
from ..zip_reader import ZipReader
from ..zip_writer import ZipWriter

logger = logging.getLogger(__name__)
HANDLER_VERSION = "0.5.0"


class ZipHandler(FormatHandler):
    """Backward-compatible adapter around the public ZIP reader and writer."""

    name = "zip"
    extensions = [".zip"]
    can_compress = True
    can_decompress = True

    def __init__(self) -> None:
        """Initialize compatibility settings without the old performance stack."""
        self.chunk_size = 8192
        self.compression_level = 6
        self.parallel_workers = 4
        self.memory_limit = 128 * 1024 * 1024
        self.cache_size = 16 * 1024 * 1024
        self.adaptive_compression = True
        self._compression_level = self.compression_level
        self._chunk_size = 1024 * 1024

        # These names remain for callers that inspected the old handler state.
        # They describe compatibility metadata, not active acceleration paths.
        self._optimization_settings = {
            "use_compression_hints": True,
            "enable_streaming_mode": True,
            "adaptive_chunk_size": True,
            "crc32_vectorization": False,
            "parallel_compression": False,
            "compression_prediction": False,
            "delegates_to_public_api": True,
        }
        self._zip_optimizations = self._optimization_settings

    def _get_tuned_chunk_size(self, file_size: int) -> int:
        """Return a deterministic compatibility chunk size."""
        if file_size < 1024 * 1024:
            return 64 * 1024
        if file_size < 100 * 1024 * 1024:
            return 1024 * 1024
        return 4 * 1024 * 1024

    def _get_compression_level(self, file_path: str) -> int:
        """Return the historical extension-based level hint."""
        if not self.adaptive_compression:
            return self.compression_level
        extension = Path(file_path).suffix.lower()
        if extension in {".txt", ".json", ".xml", ".html", ".css", ".js"}:
            return 9
        if extension in {".jpg", ".png", ".mp3", ".mp4", ".zip", ".rar"}:
            return 1
        return self.compression_level

    def _get_tuned_compression_level(self, file_path: str) -> int:
        """Compatibility alias for the old tuning helper."""
        return self._get_compression_level(file_path)

    def _get_adaptive_chunk_size(self, options: Any = None) -> int:
        """Return a bounded chunk size without reading machine-specific state."""
        if isinstance(options, dict) and "chunk_size" in options:
            return int(options["chunk_size"])
        if isinstance(options, int):
            return self._get_tuned_chunk_size(options)
        return self._chunk_size

    def _get_enhanced_chunk_size(self, file_size: int) -> int:
        """Compatibility alias for the removed enhanced buffer tuner."""
        return self._get_tuned_chunk_size(file_size)

    def _get_enhanced_pooled_buffer(
        self, size: int, buffer_type: str = "general"
    ) -> bytearray:
        """Provide a plain buffer for callers of the retired pool API."""
        del buffer_type
        return bytearray(max(0, int(size)))

    def _return_enhanced_pooled_buffer(
        self, buffer: bytearray, buffer_type: str = "general"
    ) -> None:
        """Retained no-op for the removed process-wide buffer pool."""
        del buffer, buffer_type

    def _get_parallel_workers_count(self, file_count: int, total_size: int) -> int:
        """Return the historical workload hint without starting worker threads."""
        if file_count < 10 or total_size < 10 * 1024 * 1024:
            return 1
        return min(self.parallel_workers, 2 if file_count < 100 else self.parallel_workers)

    def _get_adaptive_mmap_threshold(self, options: Optional[Dict[str, Any]] = None) -> int:
        """Return the configured mmap threshold, if supplied."""
        if options and "mmap_threshold" in options:
            return int(options["mmap_threshold"])
        return 128 * 1024 * 1024

    def _select_extraction_strategy(
        self, file_size: int, options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Keep the old strategy query compatible while using ``ZipReader``."""
        options = options or {}
        if options.get("force_classic"):
            return "classic"
        if options.get("use_mmap") or file_size >= self._get_adaptive_mmap_threshold(options):
            return "mmap"
        return "classic"

    def _should_use_zip64(self, total_size: int, file_count: int) -> bool:
        """Return whether classic ZIP limits would be exceeded."""
        return total_size > 4 * 1024 * 1024 * 1024 or file_count > 65535

    def compress(
        self,
        files: List[str],
        output: str,
        options: Optional[Dict[str, Any]] = None,
        progress_callback=None,
    ) -> Dict[str, Any]:
        """Compress files through :class:`ZipWriter`."""
        if not files:
            raise ValidationError("No files provided for compression")

        options = options or {}
        level = options.get("compression_level", self._compression_level)
        writer = ZipWriter(output, compression_level=level)
        existing_files = [path for path in files if os.path.exists(path)]

        for file_path in existing_files:
            if os.path.isdir(file_path):
                writer.add_directory(file_path)
            else:
                writer.add_file(file_path)

        if progress_callback is None:
            return writer.finalize()

        def notify(current: int, total: int) -> None:
            filename = existing_files[min(max(current - 1, 0), len(existing_files) - 1)] if existing_files else ""
            try:
                progress_callback(current, total, filename)
            except TypeError:
                progress_callback(current, total)

        return writer.finalize(notify)

    def decompress(
        self,
        archive: str,
        target_dir: str,
        options: Optional[Dict[str, Any]] = None,
        use_parallel: bool = False,
    ) -> Dict[str, Any]:
        """Extract through :class:`ZipReader` while preserving old result keys."""
        if not isinstance(archive, (str, os.PathLike)):
            return self._error_result("Archive path must be a valid string")
        if not isinstance(target_dir, (str, os.PathLike)):
            return self._error_result("Target directory must be a valid string")

        archive_path = str(archive)
        target_path = str(target_dir)
        if not os.path.exists(archive_path):
            return self._error_result(f"Archive file not found: {archive_path}")
        if not os.access(archive_path, os.R_OK):
            return self._error_result(f"Cannot read archive file: {archive_path}")

        options = options or {}
        if use_parallel or options.get("use_parallel"):
            logger.warning(
                "ZipHandler parallel extraction is retired; using ZipReader instead"
            )

        try:
            reader = ZipReader(archive_path)
            return reader.extract_all(
                target_path,
                use_mmap=bool(options.get("use_mmap")),
            )
        except SecurityError as exc:
            return self._error_result(f"Security validation failed: {exc}")
        except ValidationError as exc:
            return self._error_result(f"ZIP validation failed: {exc}")
        except (CompressionError, OSError, ValueError) as exc:
            return self._error_result(f"ZIP decompression failed: {exc}")

    @staticmethod
    def _error_result(message: str) -> Dict[str, Any]:
        return {
            "total_entries": 0,
            "success": [],
            "failed": [],
            "error": message,
        }

    def validate(self, file_path: str) -> bool:
        """Perform the historical shallow ZIP signature check."""
        try:
            if not os.path.exists(file_path):
                return False
            with open(file_path, "rb") as stream:
                return stream.read(4).startswith(b"PK")
        except (OSError, IOError):
            return False

    def get_metadata(self, archive: str) -> Dict[str, Any]:
        """Return compatibility metadata without legacy performance diagnostics."""
        return {
            "format": "zip",
            "handler": "ZipHandler",
            "version": HANDLER_VERSION,
            "status": "available",
            "compatibility": True,
            "delegates_to": {
                "compress": "ZipWriter",
                "decompress": "ZipReader",
            },
            "optimization_settings": dict(self._optimization_settings),
        }

    def get_compression_ratio(self, archive: Optional[str] = None) -> float:
        """Return compressed/uncompressed size for an existing archive."""
        if not archive or not os.path.exists(archive):
            return 0.0
        try:
            info = ZipReader(str(archive)).get_archive_info()
            return float(info["compression_ratio"])
        except (OSError, ValidationError, SecurityError, ValueError):
            return 0.0

    def compress_file(
        self,
        input_file_path: str,
        output_file_path: str,
        optimization_level: str = "balanced",
        enable_optimization: bool = True,
    ) -> Dict[str, Any]:
        """Compatibility single-file compression entry point."""
        del optimization_level, enable_optimization
        started = time.perf_counter()
        try:
            stats = self.compress([input_file_path], output_file_path)
            stats.update(
                {
                    "success": True,
                    "duration": max(time.perf_counter() - started, 0.0),
                    "method_used": "ZipWriter compatibility delegation",
                }
            )
            return stats
        except (CompressionError, ValidationError, OSError) as exc:
            return {"success": False, "error": str(exc)}

    def compress_file_with_threading(
        self,
        input_file_path: str,
        output_file_path: str,
        thread_count: int = 4,
        chunk_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Compatibility wrapper; no unverified threading claim is made."""
        del thread_count, chunk_size
        result = self.compress_file(input_file_path, output_file_path)
        result["threading_enabled"] = False
        result["method_used"] = "ZipWriter compatibility delegation"
        return result

    def compress_file_adaptive_memory(self, input_file_path: str, output_file_path: str, **kwargs) -> Dict[str, Any]:
        """Compatibility wrapper for the removed adaptive-memory path."""
        del kwargs
        return self.compress_file(input_file_path, output_file_path)

    def compress_file_adaptive_memory_enhanced(self, input_file_path: str, output_file_path: str, **kwargs) -> Dict[str, Any]:
        """Compatibility wrapper for the removed enhanced-memory path."""
        del kwargs
        return self.compress_file(input_file_path, output_file_path)


def register_zip_handler() -> ZipHandler:
    """Register and return the compatibility handler instance."""
    from ..registry import FormatRegistry

    handler = ZipHandler()
    FormatRegistry().register_handler(handler)
    return handler
