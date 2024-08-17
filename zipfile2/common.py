import sys
import zipfile


PYTHON_VERSION = sys.version_info[:2]
PY312 = PYTHON_VERSION >= (3, 12)


class TooManyFiles(zipfile.BadZipfile):
    pass
