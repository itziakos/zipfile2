import pathlib
import unittest
import tempfile

from .common import ZIP_SLIP, ZIP_SLIP_WIN, repeat_rmtree
from zipfile2 import ZipFile


class TestZipSlip(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.addCleanup(repeat_rmtree, self.tempdir)

    def test_zip_slip(self):
        # Given
        path = ZIP_SLIP

        # When
        with ZipFile(path) as zp:
            zp.extractall(self.tempdir)

        # Then
        self.assertFalse(
            pathlib.Path('/tmp/evil.txt').exists(),
            msg="/tmp/evil.txt file found")
