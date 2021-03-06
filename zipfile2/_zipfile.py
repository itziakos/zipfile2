from __future__ import absolute_import

import os
import shutil
import stat
import string
import sys
import time
import zipfile

from .common import text_type


IS_ZIPFILE_OLD_STYLE_CLASS = sys.version_info[:3] < (2, 7, 4)
ZIP_SOFTLINK_ATTRIBUTE_MAGIC = 0xA1ED0000

#Enum choices for Zipfile.extractall preserve_permissions argument
PERMS_PRESERVE_NONE, PERMS_PRESERVE_SAFE, PERMS_PRESERVE_ALL = range(3)


def is_zipinfo_symlink(zip_info):
    """Return True if the given zip_info instance refers to a symbolic link."""
    return zip_info.external_attr == ZIP_SOFTLINK_ATTRIBUTE_MAGIC


class ZipFile(zipfile.ZipFile):
    """
    A ZipFile implementation that knows how to extract soft links and allows
    overriding target destination.

    This also support context management on 2.6.
    """
    def __init__(self, file, mode='r', compression=zipfile.ZIP_STORED,
                 allowZip64=True, low_level=False):
        """ Open the ZIP file.

        Parameters
        ----------
        file: str
            Filename
        mode: str
            'r' for read, 'w' for write, 'a' for append
        compression: int
            Which compression method to use.
        low_level: bool
            If False, will raise an error when adding an already existing
            archive.
        """
        if IS_ZIPFILE_OLD_STYLE_CLASS:
            zipfile.ZipFile.__init__(self, file, mode, compression, allowZip64)
        else:
            super(ZipFile, self).__init__(file, mode, compression, allowZip64)

        self.low_level = low_level

        # Set of filenames currently in file
        members = self.namelist()
        self._filenames_set = set(members)
        if len(self._filenames_set) != len(members) and not self.low_level:
            msg = ("Duplicate members in zip archive detected. If you "
                   "want to support this, use low_level=True.")
            raise ValueError(msg)

    def extract(self, member, path=None, pwd=None,
                preserve_permissions=PERMS_PRESERVE_NONE):
        if not isinstance(member, zipfile.ZipInfo):
            member = self.getinfo(member)

        if path is None:
            path = os.getcwd()
 
        return self._extract_member(member, path, pwd, preserve_permissions)
 
    def extractall(self, path=None, members=None, pwd=None,
                   preserve_permissions=PERMS_PRESERVE_NONE):
        """ Extract all members from the archive to the current working
        directory.

        Parameters
        -----------
        path: str
            path specifies a different directory to extract to.
        members: list
            is optional and must be a subset of the list returned by
            namelist().
        preserve_permissions: int
            controls whether permissions of zipped files are preserved or
            not. Default is PERMS_PRESERVE_NONE - do not preserve any
            permissions. Other options are to preserve safe subset of
            permissions PERMS_PRESERVE_SAFE or all permissions
            PERMS_PRESERVE_ALL.
        """
        if members is None:
            members = self.namelist()
 
        for zipinfo in members:
            self.extract(zipinfo, path, pwd, preserve_permissions)
 
    def extract_to(self, member, destination, path=None, pwd=None,
                   preserve_permissions=PERMS_PRESERVE_NONE):
        if not isinstance(member, zipfile.ZipInfo):
            member = self.getinfo(member)

        if path is None:
            path = os.getcwd()

        return self._extract_member_to(member, destination, path, pwd,
                                       preserve_permissions)

    def write(self, filename, arcname=None, compress_type=None):
        if arcname is None:
            arcname = filename
        arcname = os.path.normpath(os.path.splitdrive(arcname)[1])
        while arcname[0] in (os.sep, os.altsep):
            arcname = arcname[1:]

        st = os.lstat(filename)

        if stat.S_ISDIR(st.st_mode):
            arcname += '/'

        if arcname in self._filenames_set and not self.low_level:
            msg = "{0!r} is already in archive (as {1!r})".format(filename,
                                                                  arcname)
            raise ValueError(msg)
        elif stat.S_ISLNK(st.st_mode):
            mtime = time.localtime(st.st_mtime)
            date_time = mtime[0:6]

            zip_info = zipfile.ZipInfo(arcname, date_time)
            zip_info.create_system = 3
            zip_info.external_attr = ZIP_SOFTLINK_ATTRIBUTE_MAGIC
            self.writestr(zip_info, os.readlink(filename))
        else:
            if IS_ZIPFILE_OLD_STYLE_CLASS:
                zipfile.ZipFile.write(self, filename, arcname, compress_type)
            else:
                super(ZipFile, self).write(filename, arcname, compress_type)
            self._filenames_set.add(arcname)

    def writestr(self, zinfo_or_arcname, bytes, compress_type=None):
        if not isinstance(zinfo_or_arcname, zipfile.ZipInfo):
            arcname = zinfo_or_arcname
        else:
            arcname = zinfo_or_arcname.filename

        if arcname in self._filenames_set and not self.low_level:
            msg = "{0!r} is already in archive".format(arcname)
            raise ValueError(msg)
        else:
            self._filenames_set.add(arcname)
            if IS_ZIPFILE_OLD_STYLE_CLASS:
                zipfile.ZipFile.writestr(self, zinfo_or_arcname, bytes)
            else:
                super(ZipFile, self).writestr(zinfo_or_arcname, bytes,
                                              compress_type)

    # Overriden so that ZipFile.extract* support softlink
    def _extract_member(self, member, targetpath, pwd, preserve_permissions):
        return self._extract_member_to(member, member.filename,
                                       targetpath, pwd, preserve_permissions)

    def _extract_symlink(self, member, link_name, pwd=None):
        source = self.read(member).decode("utf8")
        if os.path.lexists(link_name):
            os.unlink(link_name)
        os.symlink(source, link_name)
        return link_name

    # This is mostly copied from the stdlib zipfile.ZipFile._extract_member,
    # extended to allow soft link support. This needed copying to allow arcname
    # to not be based on ZipInfo.arcname
    def _extract_member_to(self, member, arcname, targetpath, pwd,
                           preserve_permissions):
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
                                   if x not in ('', os.path.curdir,
                                                os.path.pardir))
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
        elif is_zipinfo_symlink(member):
            return self._extract_symlink(member, targetpath, pwd)
        else:
            source = self.open(member, pwd=pwd)
            try:
                with open(targetpath, "wb") as target:
                    shutil.copyfileobj(source, target)
            finally:
                source.close()

            if preserve_permissions in (PERMS_PRESERVE_SAFE, PERMS_PRESERVE_ALL):
                if preserve_permissions == PERMS_PRESERVE_ALL:
                    #preserve bits 0-11: sugrwxrwxrwx, this include
                    #sticky bit, uid bit, gid bit
                    mode = member.external_attr >> 16 & 0xFFF
                elif PERMS_PRESERVE_SAFE:
                    #preserve bits 0-8 only: rwxrwxrwx
                    mode = member.external_attr >> 16 & 0x1FF
                os.chmod(targetpath, mode)

            return targetpath

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
