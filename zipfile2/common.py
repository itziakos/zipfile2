import sys
import zipfile


PYTHON_VERSION = sys.version_info[:2]
PY312 = PYTHON_VERSION >= (3, 12)
PY311 = PYTHON_VERSION >= (3, 11)


class TooManyFiles(zipfile.BadZipfile):
    pass


metadata_encoding_warning = 'Python < 3.11 does not support the metadata_encoding'  # noqa
