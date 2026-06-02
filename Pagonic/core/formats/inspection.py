"""
ZIP archive inspection reports.

This module records path, size, compression, and structure risks without
extracting archive contents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List
import zipfile

try:
    from .security import ZipConstants
    from .zip_structs import CompressionMethods
except ImportError:
    from Pagonic.core.formats.security import ZipConstants
    from Pagonic.core.formats.zip_structs import CompressionMethods


class ArchiveRisk:
    """Stable risk flag names used by inspection reports."""

    PATH_TRAVERSAL = "path_traversal"
    ABSOLUTE_PATH = "absolute_path"
    WINDOWS_DRIVE_PATH = "windows_drive_path"
    HIDDEN_FILE = "hidden_file"
    EMPTY_FILENAME = "empty_filename"
    TOO_MANY_FILES = "too_many_files"
    LARGE_UNCOMPRESSED_SIZE = "large_uncompressed_size"
    HIGH_COMPRESSION_RATIO = "high_compression_ratio"
    UNSUPPORTED_COMPRESSION_METHOD = "unsupported_compression_method"
    CRC_OR_STRUCTURE_ERROR = "crc_or_structure_error"
    SUSPICIOUS_EXTENSION = "suspicious_extension"


_RISK_SEVERITY = {
    ArchiveRisk.CRC_OR_STRUCTURE_ERROR: "critical",
    ArchiveRisk.PATH_TRAVERSAL: "high",
    ArchiveRisk.ABSOLUTE_PATH: "high",
    ArchiveRisk.WINDOWS_DRIVE_PATH: "high",
    ArchiveRisk.TOO_MANY_FILES: "high",
    ArchiveRisk.LARGE_UNCOMPRESSED_SIZE: "high",
    ArchiveRisk.HIGH_COMPRESSION_RATIO: "high",
    ArchiveRisk.UNSUPPORTED_COMPRESSION_METHOD: "medium",
    ArchiveRisk.SUSPICIOUS_EXTENSION: "medium",
    ArchiveRisk.HIDDEN_FILE: "low",
    ArchiveRisk.EMPTY_FILENAME: "medium",
}

_RISK_ORDER = {"ok": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
_SUSPICIOUS_EXTENSIONS = {".bat", ".cmd", ".com", ".dll", ".exe", ".js", ".msi", ".ps1", ".scr", ".vbs"}


@dataclass
class ArchiveEntryReport:
    """Inspection data for one archive entry."""

    filename: str
    safe_path: str
    compressed_size: int
    uncompressed_size: int
    compression_method: int
    crc32: int
    compression_ratio: float
    risk_flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filename": self.filename,
            "safe_path": self.safe_path,
            "compressed_size": self.compressed_size,
            "uncompressed_size": self.uncompressed_size,
            "compression_method": self.compression_method,
            "crc32": f"{self.crc32:08x}",
            "compression_ratio": self.compression_ratio,
            "risk_flags": list(self.risk_flags),
        }


@dataclass
class ArchiveInspectionReport:
    """Structured inspection report for a ZIP archive."""

    archive_path: str
    file_count: int
    total_compressed_size: int
    total_uncompressed_size: int
    compression_ratio: float
    risk_level: str
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    entries: List[ArchiveEntryReport] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "archive_path": self.archive_path,
            "file_count": self.file_count,
            "total_compressed_size": self.total_compressed_size,
            "total_uncompressed_size": self.total_uncompressed_size,
            "compression_ratio": self.compression_ratio,
            "risk_level": self.risk_level,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "entries": [entry.to_dict() for entry in self.entries],
        }


def inspect_archive(zip_path: str | Path) -> ArchiveInspectionReport:
    """Inspect a ZIP archive without extracting it."""
    entries: List[ArchiveEntryReport] = []
    warnings: List[str] = []
    errors: List[str] = []
    report_risks: List[str] = []

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_file:
            infos = zip_file.infolist()
            if len(infos) > ZipConstants.MAX_FILES_IN_ZIP:
                report_risks.append(ArchiveRisk.TOO_MANY_FILES)
                warnings.append(f"Archive contains too many files: {len(infos)}")

            bad_file = zip_file.testzip()
            if bad_file:
                report_risks.append(ArchiveRisk.CRC_OR_STRUCTURE_ERROR)
                errors.append(f"CRC or structure error detected in '{bad_file}'")

            entries = [_inspect_entry(info) for info in infos]
    except (zipfile.BadZipFile, OSError) as exc:
        errors.append(f"Invalid or unreadable ZIP archive: {exc}")
        report_risks.append(ArchiveRisk.CRC_OR_STRUCTURE_ERROR)

    total_compressed = sum(entry.compressed_size for entry in entries)
    total_uncompressed = sum(entry.uncompressed_size for entry in entries)
    if total_uncompressed > ZipConstants.MAX_UNCOMPRESSED_SIZE:
        report_risks.append(ArchiveRisk.LARGE_UNCOMPRESSED_SIZE)
        warnings.append(f"Archive exceeds uncompressed size limit: {total_uncompressed}")

    all_risks = report_risks + [risk for entry in entries for risk in entry.risk_flags]
    return ArchiveInspectionReport(
        archive_path=str(zip_path),
        file_count=len(entries),
        total_compressed_size=total_compressed,
        total_uncompressed_size=total_uncompressed,
        compression_ratio=_ratio(total_uncompressed, total_compressed),
        risk_level=_highest_risk_level(all_risks),
        warnings=warnings,
        errors=errors,
        entries=entries,
    )


def _inspect_entry(info: zipfile.ZipInfo) -> ArchiveEntryReport:
    risk_flags = _analyze_archive_path(info.filename)
    ratio = _ratio(info.file_size, info.compress_size)

    if info.file_size > 0 and info.compress_size > 0 and ratio > ZipConstants.MAX_COMPRESSION_RATIO:
        risk_flags.append(ArchiveRisk.HIGH_COMPRESSION_RATIO)
    if not CompressionMethods.is_supported(info.compress_type):
        risk_flags.append(ArchiveRisk.UNSUPPORTED_COMPRESSION_METHOD)
    if Path(_safe_basename(info.filename)).suffix.lower() in _SUSPICIOUS_EXTENSIONS:
        risk_flags.append(ArchiveRisk.SUSPICIOUS_EXTENSION)

    return ArchiveEntryReport(
        filename=info.filename,
        safe_path=_safe_archive_path(info.filename),
        compressed_size=info.compress_size,
        uncompressed_size=info.file_size,
        compression_method=info.compress_type,
        crc32=info.CRC,
        compression_ratio=ratio,
        risk_flags=_dedupe(risk_flags),
    )


def _analyze_archive_path(filename: str) -> List[str]:
    normalized = str(filename).replace("\\", "/")
    parts = normalized.split("/")
    risks: List[str] = []

    if not normalized or all(part in ("", ".", "..") for part in parts):
        risks.append(ArchiveRisk.EMPTY_FILENAME)
    if normalized.startswith("/"):
        risks.append(ArchiveRisk.ABSOLUTE_PATH)
    if len(normalized) >= 2 and normalized[1] == ":":
        risks.append(ArchiveRisk.WINDOWS_DRIVE_PATH)
    if any(part == ".." for part in parts):
        risks.append(ArchiveRisk.PATH_TRAVERSAL)
    if _safe_basename(filename).startswith("."):
        risks.append(ArchiveRisk.HIDDEN_FILE)

    return _dedupe(risks)


def _safe_archive_path(filename: str) -> str:
    normalized = str(filename).replace("\\", "/")
    if len(normalized) >= 2 and normalized[1] == ":":
        normalized = normalized[2:]
    parts = [part for part in normalized.lstrip("/").split("/") if part not in ("", ".", "..")]
    return "/".join(parts)


def _safe_basename(filename: str) -> str:
    return str(filename).replace("\\", "/").rsplit("/", 1)[-1]


def _ratio(uncompressed_size: int, compressed_size: int) -> float:
    if uncompressed_size <= 0:
        return 0.0
    return uncompressed_size / max(compressed_size, 1)


def _highest_risk_level(risks: List[str]) -> str:
    level = "ok"
    for risk in risks:
        candidate = _RISK_SEVERITY.get(risk, "low")
        if _RISK_ORDER[candidate] > _RISK_ORDER[level]:
            level = candidate
    return level


def _dedupe(values: List[str]) -> List[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


__all__ = ["ArchiveEntryReport", "ArchiveInspectionReport", "ArchiveRisk", "inspect_archive"]
