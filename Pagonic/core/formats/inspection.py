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


@dataclass(frozen=True)
class RiskDefinition:
    """Human-readable metadata for one inspection risk flag."""

    id: str
    title: str
    severity: str
    explanation: str
    recommended_action: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "id": self.id,
            "title": self.title,
            "severity": self.severity,
            "explanation": self.explanation,
            "recommended_action": self.recommended_action,
        }


RISK_CATALOG: Dict[str, RiskDefinition] = {
    ArchiveRisk.PATH_TRAVERSAL: RiskDefinition(
        id=ArchiveRisk.PATH_TRAVERSAL,
        title="Path traversal entry",
        severity="high",
        explanation="The entry contains '..' path segments that could try to escape the extraction directory.",
        recommended_action="Do not extract automatically. Inspect the archive source and use safe extraction only if you trust it.",
    ),
    ArchiveRisk.ABSOLUTE_PATH: RiskDefinition(
        id=ArchiveRisk.ABSOLUTE_PATH,
        title="POSIX absolute path",
        severity="high",
        explanation="The entry starts with '/', which is unsafe for direct extraction.",
        recommended_action="Treat the archive as unsafe for direct extraction. Use a sanitized target path.",
    ),
    ArchiveRisk.WINDOWS_DRIVE_PATH: RiskDefinition(
        id=ArchiveRisk.WINDOWS_DRIVE_PATH,
        title="Windows drive path",
        severity="high",
        explanation="The entry looks like a Windows drive path such as C:\\path\\file.",
        recommended_action="Do not extract directly. Use safe extraction so the drive prefix cannot control the target path.",
    ),
    ArchiveRisk.HIDDEN_FILE: RiskDefinition(
        id=ArchiveRisk.HIDDEN_FILE,
        title="Hidden filename",
        severity="low",
        explanation="The entry basename starts with '.', which may be easy to overlook in listings.",
        recommended_action="Review the hidden file before trusting or deploying the extracted contents.",
    ),
    ArchiveRisk.EMPTY_FILENAME: RiskDefinition(
        id=ArchiveRisk.EMPTY_FILENAME,
        title="Empty or invalid filename",
        severity="medium",
        explanation="The entry name is empty or contains only path control segments.",
        recommended_action="Review the archive manually and avoid automated extraction if the entry cannot be mapped safely.",
    ),
    ArchiveRisk.TOO_MANY_FILES: RiskDefinition(
        id=ArchiveRisk.TOO_MANY_FILES,
        title="Too many files",
        severity="high",
        explanation="The archive contains more entries than the configured safety limit.",
        recommended_action="Do not process automatically. Increase limits only for known-good archives in controlled environments.",
    ),
    ArchiveRisk.LARGE_UNCOMPRESSED_SIZE: RiskDefinition(
        id=ArchiveRisk.LARGE_UNCOMPRESSED_SIZE,
        title="Large uncompressed size",
        severity="high",
        explanation="The total uncompressed size is above the configured safety limit.",
        recommended_action="Avoid automatic extraction unless resource limits and the archive source are trusted.",
    ),
    ArchiveRisk.HIGH_COMPRESSION_RATIO: RiskDefinition(
        id=ArchiveRisk.HIGH_COMPRESSION_RATIO,
        title="High compression ratio",
        severity="high",
        explanation="An entry expands much more than its compressed size, which may indicate ZIP bomb behavior.",
        recommended_action="Do not extract automatically. Inspect in a constrained environment if analysis is required.",
    ),
    ArchiveRisk.UNSUPPORTED_COMPRESSION_METHOD: RiskDefinition(
        id=ArchiveRisk.UNSUPPORTED_COMPRESSION_METHOD,
        title="Unsupported compression method",
        severity="medium",
        explanation="The entry uses a ZIP compression method that Pagonic does not currently support.",
        recommended_action="Use a compatible tool for this archive or recreate the ZIP with STORE/DEFLATE.",
    ),
    ArchiveRisk.CRC_OR_STRUCTURE_ERROR: RiskDefinition(
        id=ArchiveRisk.CRC_OR_STRUCTURE_ERROR,
        title="CRC or structure error",
        severity="critical",
        explanation="The archive failed ZIP structure or CRC validation.",
        recommended_action="Reject the archive for automation and ask for a fresh copy from a trusted source.",
    ),
    ArchiveRisk.SUSPICIOUS_EXTENSION: RiskDefinition(
        id=ArchiveRisk.SUSPICIOUS_EXTENSION,
        title="Suspicious file extension",
        severity="medium",
        explanation="The entry has an extension commonly associated with executable or script content.",
        recommended_action="Review the file before execution or deployment. Do not treat it as harmless data.",
    ),
}


_RISK_SEVERITY = {risk_id: definition.severity for risk_id, definition in RISK_CATALOG.items()}
_RISK_CATALOG_ORDER = {risk_id: index for index, risk_id in enumerate(RISK_CATALOG)}

_RISK_ORDER = {"ok": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
_SUSPICIOUS_EXTENSIONS = {".bat", ".cmd", ".com", ".dll", ".exe", ".js", ".msi", ".ps1", ".scr", ".vbs"}


@dataclass
class ArchiveEntryReport:
    """Inspection data for one archive entry."""

    original_name: str
    safe_name: str
    compressed_size: int
    uncompressed_size: int
    compression_method: int
    crc32: int
    compression_ratio: float
    risk_flags: List[str] = field(default_factory=list)

    @property
    def filename(self) -> str:
        """Backward-compatible alias for older callers."""
        return self.original_name

    @property
    def safe_path(self) -> str:
        """Backward-compatible alias for older callers."""
        return self.safe_name

    def to_dict(self) -> Dict[str, Any]:
        """Return the stable JSON-compatible report shape for this entry."""
        return {
            "original_name": self.original_name,
            "normalized_name": self.safe_name,
            "safe_name": self.safe_name,
            "compressed_size": self.compressed_size,
            "uncompressed_size": self.uncompressed_size,
            "compression_method": self.compression_method,
            "crc32": f"{self.crc32:08x}",
            "compression_ratio": self.compression_ratio,
            "risk_flags": list(self.risk_flags),
            # Backward-compatible aliases for the early alpha report shape.
            "filename": self.original_name,
            "safe_path": self.safe_name,
        }


@dataclass
class ArchiveInspectionReport:
    """Structured inspection report for a ZIP archive."""

    archive_path: str
    file_count: int
    total_compressed_size: int
    total_uncompressed_size: int
    global_compression_ratio: float
    risk_level: str
    risk_flags: List[str] = field(default_factory=list)
    recommended_action: str = ""
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    entries: List[ArchiveEntryReport] = field(default_factory=list)

    @property
    def compression_ratio(self) -> float:
        """Backward-compatible alias for older callers."""
        return self.global_compression_ratio

    def to_dict(self) -> Dict[str, Any]:
        """Return the stable JSON-compatible archive report shape."""
        return {
            "archive_path": self.archive_path,
            "file_count": self.file_count,
            "total_compressed_size": self.total_compressed_size,
            "total_uncompressed_size": self.total_uncompressed_size,
            "global_compression_ratio": self.global_compression_ratio,
            "risk_level": self.risk_level,
            "risk_flags": list(self.risk_flags),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "recommended_action": self.recommended_action,
            "entries": [entry.to_dict() for entry in self.entries],
            # Backward-compatible alias for the early alpha report shape.
            "compression_ratio": self.global_compression_ratio,
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

    all_risks = _dedupe(report_risks + [risk for entry in entries for risk in entry.risk_flags])
    risk_level = _highest_risk_level(all_risks)
    return ArchiveInspectionReport(
        archive_path=str(zip_path),
        file_count=len(entries),
        total_compressed_size=total_compressed,
        total_uncompressed_size=total_uncompressed,
        global_compression_ratio=_ratio(total_uncompressed, total_compressed),
        risk_level=risk_level,
        risk_flags=all_risks,
        recommended_action=_recommended_action(risk_level, bool(errors)),
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
        original_name=info.filename,
        safe_name=_safe_archive_path(info.filename),
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


def _recommended_action(risk_level: str, has_errors: bool = False) -> str:
    if has_errors or risk_level == "critical":
        return "Reject this archive for automation and request a fresh copy from a trusted source."
    if risk_level == "high":
        return "Do not extract automatically. Review the archive and use safe extraction only in a controlled location."
    if risk_level == "medium":
        return "Review the reported risk flags before extraction or automation."
    if risk_level == "low":
        return "Archive is generally acceptable, but review low-risk warnings before trusting the contents."
    return "No inspection risks were detected. Safe extraction is acceptable under normal trust assumptions."


def _dedupe(values: List[str]) -> List[str]:
    seen = set()
    result = []
    ordered = sorted(values, key=_risk_sort_key)
    for value in ordered:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _risk_sort_key(value: str) -> int:
    return _RISK_CATALOG_ORDER.get(value, len(_RISK_CATALOG_ORDER))


def get_risk_definition(risk_id: str) -> RiskDefinition:
    """Return catalog metadata for a risk flag.

    Raises KeyError for unknown risk IDs to keep catalog lookups explicit.
    """
    return RISK_CATALOG[risk_id]


__all__ = [
    "ArchiveEntryReport",
    "ArchiveInspectionReport",
    "ArchiveRisk",
    "RiskDefinition",
    "RISK_CATALOG",
    "get_risk_definition",
    "inspect_archive",
]
