from __future__ import absolute_import

import os
import shutil
import string
import zipfile

from six import text_type


ZIP_SOFTLINK_ATTRIBUTE_MAGIC = 0xA1ED0000


def is_zipinfo_symlink(zip_info):
    """Return True if the given zip_info instance refers to a symbolic link."""
    return zip_info.external_attr == ZIP_SOFTLINK_ATTRIBUTE_MAGIC


class ZipFile(zipfile.ZipFile):
    """
    A ZipFile implementation that knows how to extract soft links and allows
    overriding target destination.

    This also support context management on 2.6.
    """

    def extract_to(self, member, destination, path=None, pwd=None):
        if not isinstance(member, zipfile.ZipInfo):
            member = self.getinfo(member)

        if path is None:
            path = os.getcwd()

        return self._extract_member_to(member, destination, path, pwd)

    # Overriden so that ZipFile.extract* support softlink
    def _extract_member(self, member, targetpath, pwd):
        return self._extract_member_to(member, member.filename, targetpath, pwd)

    def _extract_symlink(self, member, link_name, pwd=None):
        source = self.read(member).decode("utf8")
        if os.path.lexists(link_name):
            os.unlink(link_name)
        os.symlink(source, link_name)
        return link_name

    # This is mostly copied from the stdlib zipfile.ZipFile._extract_member,
    # extended to allow soft link support. This needed copying to allow arcname
    # to not be based on ZipInfo.arcname
    def _extract_member_to(self, member, arcname, targetpath, pwd):
        """Extract the ZipInfo object 'member' to a physical
           file on the path targetpath.
        """
        # build the destination pathname, replacing
        # forward slashes to platform specific separators.
        arcname = arcname.replace('/', os.path.sep)

        if os.path.altsep:
            arcname = arcname.replace(os.path.altsep, os.path.sep)
        # interpret absolute pathname as relative, remove drive letter or
        # UNC path, redundant separators, "." and ".." components.
        arcname = os.path.splitdrive(arcname)[1]
        arcname = os.path.sep.join(x for x in arcname.split(os.path.sep)
                                   if x not in ('', os.path.curdir, os.path.pardir))
        if os.path.sep == '\\':
            # filter illegal characters on Windows
            illegal = ':<>|"?*'
            if isinstance(arcname, text_type):
                table = dict((ord(c), ord('_')) for c in illegal)
            else:
                table = string.maketrans(illegal, '_' * len(illegal))
            arcname = arcname.translate(table)
            # remove trailing dots
            arcname = (x.rstrip('.') for x in arcname.split(os.path.sep))
            arcname = os.path.sep.join(x for x in arcname if x)

        targetpath = os.path.join(targetpath, arcname)
        targetpath = os.path.normpath(targetpath)

        # Create all upper directories if necessary.
        upperdirs = os.path.dirname(targetpath)
        if upperdirs and not os.path.exists(upperdirs):
            os.makedirs(upperdirs)

        if member.filename[-1] == '/':
            if not os.path.isdir(targetpath):
                os.mkdir(targetpath)
            return targetpath

        if is_zipinfo_symlink(member):
            return self._extract_symlink(member, targetpath, pwd)
        else:
            source = self.open(member, pwd=pwd)
            try:
                with open(targetpath, "wb") as target:
                    shutil.copyfileobj(source, target)
            finally:
                source.close()

            return targetpath

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
