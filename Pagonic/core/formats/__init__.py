"""
Pagonic Format Handler System
----------------------------
This package provides the core format handling functionality for Pagonic.
"""

from .base import FormatHandler
from .errors import FormatError, ValidationError, CompressionError

__all__ = ['FormatHandler', 'FormatRegistry', 'FormatError', 'ValidationError', 'CompressionError']


def __getattr__(name):
    """Keep the generic registry out of lightweight ZIP imports."""
    if name != "FormatRegistry":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from .registry import FormatRegistry

    globals()[name] = FormatRegistry
    return FormatRegistry
