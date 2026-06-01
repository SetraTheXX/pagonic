"""
Pagonic GUI Workers Package
===========================
QThread workers for compression and extraction (non-blocking UI).
"""

from .compression import CompressionWorker
from .extraction import ExtractionWorker

__all__ = ['CompressionWorker', 'ExtractionWorker']
