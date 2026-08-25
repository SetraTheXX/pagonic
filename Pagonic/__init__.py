"""Pagonic security-aware ZIP inspection and extraction toolkit."""

__version__ = "0.3.0"
__author__ = "Pagonic contributors"

from .core.formats.base import FormatHandler

__all__ = [
    "FormatHandler",
    "ZipHandler",
    "ZipReader",
    "ZipWriter",
    "inspect_archive",
    "ArchiveEntryReport",
    "ArchiveInspectionReport",
    "ArchiveRisk",
    "RiskDefinition",
    "RISK_CATALOG",
    "get_risk_definition",
    "__version__",
]


_LAZY_EXPORTS = {
    "ZipHandler": ("Pagonic.core.formats.handlers.zip_handler", "ZipHandler"),
    "ZipReader": ("Pagonic.core.formats.zip_reader", "ZipReader"),
    "ZipWriter": ("Pagonic.core.formats.zip_writer", "ZipWriter"),
    "inspect_archive": ("Pagonic.core.formats.inspection", "inspect_archive"),
    "ArchiveEntryReport": ("Pagonic.core.formats.inspection", "ArchiveEntryReport"),
    "ArchiveInspectionReport": (
        "Pagonic.core.formats.inspection",
        "ArchiveInspectionReport",
    ),
    "ArchiveRisk": ("Pagonic.core.formats.inspection", "ArchiveRisk"),
    "RiskDefinition": ("Pagonic.core.formats.inspection", "RiskDefinition"),
    "RISK_CATALOG": ("Pagonic.core.formats.inspection", "RISK_CATALOG"),
    "get_risk_definition": ("Pagonic.core.formats.inspection", "get_risk_definition"),
}


def __getattr__(name):
    """Load public ZIP APIs only when a caller requests them."""
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    import importlib

    module_name, attribute_name = target
    value = getattr(importlib.import_module(module_name), attribute_name)
    globals()[name] = value
    return value
