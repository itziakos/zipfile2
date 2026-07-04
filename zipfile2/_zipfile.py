import errno
import os
import shutil
import stat
import time
import zipfile
import warnings

from .common import PY311, metadata_encoding_warning

ZIP_SOFTLINK_ATTRIBUTE_MAGIC = 0xA1ED0000

# Enum choices for Zipfile.extractall preserve_permissions argument
PERMS_PRESERVE_NONE, PERMS_PRESERVE_SAFE, PERMS_PRESERVE_ALL = range(3)


# Use octal as it is the convention used in zipinfo.c (as found in e.g. apt-get
# source unzip)
_UNX_IFMT = 0o170000  # Unix file type mask
_UNX_IFLNK = 0o120000  # Unix symbolic link


def is_zipinfo_symlink(zip_info):
    """Return True if the given zip_info instance refers to a symbolic link."""
    mode = zip_info.external_attr >> 16
    return (mode & _UNX_IFMT) == _UNX_IFLNK


class ZipFile(zipfile.ZipFile):
    """
    A ZipFile implementation that knows how to extract soft links and allows
    overriding target destination.

    """
    def __init__(
            self, file, mode='r', compression=zipfile.ZIP_STORED,
            allowZip64=True, compresslevel=None, *, strict_timestamps=True,
            metadata_encoding=None, low_level=False):
        """Open the ZIP file.

        Parameters
        ----------
        file: str
            Filename
        mode: str
            The mode can be either read 'r', write 'w', exclusive create 'x',
            or append 'a'.
        compression: int
            ZIP_STORED (no compression), ZIP_DEFLATED (requires zlib),
            ZIP_BZIP2 (requires bz2) or ZIP_LZMA (requires lzma).
        allowZip64: bool
            if True ZipFile will create files with ZIP64 extensions
            when needed, otherwise it will raise an exception when
            this would be necessary.
        low_level: bool
            If False, will raise an error when adding an already existing
            archive.

        """
        if PY311:
            super(ZipFile, self).__init__(
                file, mode, compression, allowZip64, compresslevel,
                strict_timestamps=strict_timestamps,
                metadata_encoding=metadata_encoding)
        else:
            if metadata_encoding is not None:
                warnings.warn(metadata_encoding_warning)
            super(ZipFile, self).__init__(
                file, mode, compression, allowZip64, compresslevel,
                strict_timestamps=strict_timestamps)

        self.low_level = low_level

        # Set of filenames currently in file
        members = self.namelist()
        self._filenames_set = set(members)
        if len(self._filenames_set) != len(members) and not self.low_level:
            msg = ("Duplicate members in zip archive detected. If you "
                   "want to support this, use low_level=True.")
            raise ValueError(msg)

        self._invalid_path_parts = ('', os.path.curdir, os.path.pardir)


    def add_tree(self, directory, include_top=False):
        """ Zip the given directory into this archive, by walking into it.

        The archive names will be relative to the directory, e.g. for::

            <directory>/foo.txt
            <directory>/bar/foo.txt

        doing add_tree(<directory>) will give you a zipfile with the content::

            foo.txt
            bar/foo.txt
        """
        if include_top:
            base = os.path.basename(directory)
        else:
            base = "."

        for root, dirs, files in os.walk(directory):
            entries = [os.path.join(root, entry) for entry in dirs + files]
            for entry in entries:
                arcname = os.path.join(base, os.path.relpath(entry, directory))
                self.write(entry, arcname)

    def extract(
            self, member, path=None, pwd=None,
            preserve_permissions=PERMS_PRESERVE_NONE):

        if not isinstance(member, zipfile.ZipInfo):
            member = self.getinfo(member)

        if path is None:
            path = os.getcwd()
        else:
            path = os.fspath(path)

        return self._extract_member(member, path, pwd, preserve_permissions)

    def extractall(
            self, path=None, members=None, pwd=None,
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

        return self._extract_member_to(
            member, destination, path, pwd, preserve_permissions)

    def write(
            self, filename, arcname=None,
            compress_type=None, compresslevel=None):
        if arcname is None:
            arcname = filename
        st = os.lstat(filename)
        arcname = self._normalize_arcname(arcname)
        if stat.S_ISDIR(st.st_mode):
            arcname += '/'

        self._ensure_uniqueness(arcname)
        if stat.S_ISLNK(st.st_mode):
            mtime = time.localtime(st.st_mtime)
            date_time = mtime[0:6]

            zip_info = zipfile.ZipInfo(arcname, date_time)
            zip_info.create_system = 3
            zip_info.external_attr = ZIP_SOFTLINK_ATTRIBUTE_MAGIC
            self.writestr(zip_info, os.readlink(filename))
        else:
            super(ZipFile, self).write(
                filename, arcname, compress_type, compresslevel)
            self._filenames_set.add(arcname)

    def writestr(
            self, zinfo_or_arcname, data,
            compress_type=None, compresslevel=None):
        if not isinstance(zinfo_or_arcname, zipfile.ZipInfo):
            arcname = self._normalize_arcname(zinfo_or_arcname)
        else:
            arcname = zinfo_or_arcname.filename

        self._ensure_uniqueness(arcname)
        self._filenames_set.add(arcname)
        super(ZipFile, self).writestr(
            zinfo_or_arcname, data, compress_type, compresslevel)

    # Overriden so that ZipFile.extract* support softlink
    def _extract_member(self, member, targetpath, pwd, preserve_permissions):
        return self._extract_member_to(
            member, member.filename,
            targetpath, pwd, preserve_permissions)

    def _extract_symlink(self, member, link_name, rootpath):
        source = self.read(member).decode("utf8")
        source = self._sanitize_symlink(source, rootpath, member.is_dir())
        if os.path.lexists(link_name):
            os.unlink(link_name)
        os.symlink(source, link_name)
        return link_name

    # This is mostly copied from the stdlib
    # zipfile.ZipFile._extract_member, extended to allow soft link
    # support. This needed copying to allow arcname to not be based on
    # ZipInfo.arcname
    def _extract_member_to(self, member, arcname, targetpath, pwd,
                           preserve_permissions):
        """Extract the ZipInfo object 'member' to a physical
           file on the path targetpath.
        """
        isdir = member.is_dir()
        finalpath = self._sanitize_arcname(arcname, targetpath, isdir)

        # Create all upper directories if necessary.
        upperdirs = os.path.dirname(finalpath)
        if upperdirs and not os.path.exists(upperdirs):
            os.makedirs(upperdirs)

        if isdir:
            if not os.path.isdir(finalpath):
                os.mkdir(finalpath)
            return finalpath
        elif is_zipinfo_symlink(member):
            return self._extract_symlink(member, finalpath, targetpath)
        else:
            source = self.open(member, pwd=pwd)
            try:
                _unlink_if_exists(finalpath)
                with open(finalpath, "wb") as target:
                    shutil.copyfileobj(source, target)
            finally:
                source.close()

            if preserve_permissions in (
                    PERMS_PRESERVE_SAFE, PERMS_PRESERVE_ALL):
                if preserve_permissions == PERMS_PRESERVE_ALL:
                    # preserve bits 0-11: sugrwxrwxrwx, this include
                    # sticky bit, uid bit, gid bit
                    mode = member.external_attr >> 16 & 0xFFF
                elif PERMS_PRESERVE_SAFE:
                    # preserve bits 0-8 only: rwxrwxrwx
                    mode = member.external_attr >> 16 & 0x1FF
                os.chmod(finalpath, mode)
            return finalpath

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _ensure_uniqueness(self, arcname):
        if not self.low_level and arcname in self._filenames_set:
            msg = "{0!r} is already in archive".format(arcname)
            raise ValueError(msg)

    def _normalize_arcname(self, arcname):
        sep = os.sep
        altsep = os.sep
        arcname = os.path.normpath(os.path.splitdrive(arcname)[1])
        while arcname[0] in (sep, altsep):
            arcname = arcname[1:]
        # This is used to ensure paths in generated ZIP files always use
        # forward slashes as the directory separator, as required by the
        # ZIP format specification.
        if sep != "/" and sep in arcname:
            arcname = arcname.replace(sep, "/")

        return arcname

    def _sanitize_arcname(self, arcname, targetpath, isdir):
        sep = os.sep
        altsep = os.altsep
        arcname = arcname.replace('/', sep)
        if altsep:
            path = path.replace(altsep, sep)

        # interpret absolute pathname as relative, remove drive letter or
        # UNC path, redundant separators, "." and ".." components.
        arcname = os.path.splitdrive(arcname)[1]
        arcname = sep.join(
            x for x in arcname.split(sep)
            if x not in self._invalid_path_parts)

        if sep == '\\':
            # filter illegal characters on Windows
            arcname = self._sanitize_windows_name(arcname, sep)

        if not arcname and not isdir:
            raise ValueError("Empty filename.")

        arcname = os.path.join(targetpath, arcname)
        arcname = os.path.normpath(arcname)
        if os.path.commonpath([arcname, targetpath]) != targetpath:
            raise BadZipFile(f"{arcname} outside of {targetpath}")
        return arcname

    def _sanitize_symlink(self, source, targetpath, isdir):
        sep = os.sep
        altsep = os.altsep
        source = source.replace('/', sep)
        if altsep:
            source = source.replace(altsep, sep)

        if sep == '\\':
            # filter illegal characters on Windows
            source = self._sanitize_windows_name(source, sep)

        if not source and not isdir:
            raise ValueError("Empty filename.")

        sourcepath = os.path.join(targetpath, source)
        sourcepath = os.path.normpath(sourcepath)
        if os.path.commonpath([sourcepath, targetpath]) != targetpath:
            raise zipfile.BadZipFile(f"link to {sourcepath} outside of {targetpath}")
        return source


def _unlink_if_exists(p):
    try:
        os.unlink(p)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise
