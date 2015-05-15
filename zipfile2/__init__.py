from __future__ import absolute_import

try:
    from ._version import (full_version as __version__,
                           git_revision as __git_revision__,
                           is_released as __is_released__)
except ImportError:
    __version__ = __git_revision__ = "no-built"
    __is_released__ = False

from .common import TooManyFiles
from ._zipfile import ZipFile
from ._lean_zipfile import LeanZipFile

__all__ = [
    "__git_revision__", "__is_released__", "__version__", "LeanZipFile",
    "TooManyFiles", "ZipFile"
]
