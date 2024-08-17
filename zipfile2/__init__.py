from __future__ import absolute_import

try:
    from ._version import __version__,
except ImportError:
    __version__ = "no-built"

from .common import TooManyFiles
from ._zipfile import (
    PERMS_PRESERVE_NONE, PERMS_PRESERVE_SAFE, PERMS_PRESERVE_ALL, ZipFile)
from ._lean_zipfile import LeanZipFile
from zipfile import (
    ZIP64_LIMIT, ZIP_DEFLATED, ZIP_FILECOUNT_LIMIT, ZIP_MAX_COMMENT,
    ZIP_STORED)

__all__ = [
    "__version__",
    "LeanZipFile", "TooManyFiles", "ZipFile",
    "PERMS_PRESERVE_NONE", "PERMS_PRESERVE_SAFE",
    "PERMS_PRESERVE_ALL", "ZIP64_LIMIT", "ZIP_DEFLATED",
    "ZIP_FILECOUNT_LIMIT", "ZIP_MAX_COMMENT", "ZIP_STORED",
]
