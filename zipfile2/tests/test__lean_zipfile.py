from __future__ import absolute_import

import os.path
import shutil
import sys
import tempfile

if sys.version_info[:2] < (2, 7):
    import unittest2 as unittest
else:
    import unittest

from zipfile2 import TooManyFiles

from .._lean_zipfile import LeanZipFile

from .common import NOSE_EGG, NOSE_SPEC_DEPEND, VTK_EGG, ZIP_WITH_SOFTLINK


class TestLeanZipFile(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_simple(self):
        # Given
        path = NOSE_EGG

        # When/Then
        with self.assertRaises(TooManyFiles):
            with LeanZipFile(path, max_file_count=1) as z:
                for zinfo in z.get_zip_infos("Non-existing-file"):
                    pass

    def test_get_infos(self):
        # Given
        path = NOSE_EGG

        # When
        with LeanZipFile(path) as z:
            zinfos = list(z.get_zip_infos("EGG-INFO/spec/depend",
                                          "EGG-INFO/spec/summary"))

        # Then
        self.assertEqual(len(zinfos), 2)
        self.assertEqual(zinfos[0].filename, "EGG-INFO/spec/depend")
        self.assertEqual(zinfos[1].filename, "EGG-INFO/spec/summary")

    def test_read(self):
        # Given
        path = NOSE_EGG

        # When
        with LeanZipFile(path) as z:
            zinfo = list(z.get_zip_infos("EGG-INFO/spec/depend"))[0]
            data = z.read(zinfo)

        # Then
        self.assertEqual(data, NOSE_SPEC_DEPEND.encode())
