"""Pagonic security-aware ZIP inspection and extraction toolkit."""

__version__ = "0.3.0"
__author__ = "Pagonic contributors"

from .core.formats.base import FormatHandler
from .core.formats.handlers.zip_handler import ZipHandler

__all__ = ["FormatHandler", "ZipHandler", "__version__"]
