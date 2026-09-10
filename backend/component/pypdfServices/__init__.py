# pdf_service/__init__.py
"""
PDF Service - Comprehensive pypdf wrapper
"""

from . import core
from . import text
from . import images
from . import annotations
from . import formHandling
from . import metadata
from . import pages
from . import attachments
from . import outlines
from . import content

__version__ = "1.0.0"

__all__ = [
    "core",
    "text",
    "images",
    "annotations",
    "formHandling",
    "metadata",
    "pages",
    "attachments",
    "outlines",
    "content"
]