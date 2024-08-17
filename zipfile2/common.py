import zipfile
import platform

PYTHON_VERSION = tuple(map(int, platform.python_version_tuple()))
PY312 = PYTHON_VERSION >= (3, 12, 0)


class TooManyFiles(zipfile.BadZipfile):
    pass
