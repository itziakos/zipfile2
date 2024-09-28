import os
import sys
import shutil
import unittest

HERE = os.path.dirname(__file__)
NOSE_EGG = os.path.join(HERE, "data", "nose.egg")
VTK_EGG = os.path.join(HERE, "data", "vtk.egg")
ZIP_WITH_SOFTLINK = os.path.join(HERE, "data", "zip_with_softlink.zip")
ZIP_WITH_DIRECTORY_SOFTLINK = os.path.join(
    HERE, "data", "zip_with_directory_softlink.zip")
ZIP_WITH_PERMISSIONS = os.path.join(HERE, "data", "zip_with_permissions.zip")
ZIP_WITH_SOFTLINK_AND_PERMISSIONS = os.path.join(
    HERE, "data", "zip_with_softlink_and_permissions.zip")

NOSE_SPEC_DEPEND = """\
metadata_version = '1.1'
name = 'nose'
version = '1.3.0'
build = 2

arch = 'amd64'
platform = 'darwin'
osdist = None
python = '2.7'
packages = []
"""

#####################################################
# Code copied from Python 3.11 test.support.os_helper

# Filename used for testing
if os.name == 'java':
    # Jython disallows @ in module names
    TESTFN_ASCII = '$test'
else:
    TESTFN_ASCII = '@test'

# Disambiguate TESTFN for parallel testing, while letting it remain a valid
# module name.
TESTFN_ASCII = "{}_{}_tmp".format(TESTFN_ASCII, os.getpid())

# TESTFN_UNICODE is a non-ascii filename
TESTFN_UNICODE = TESTFN_ASCII + "-\xe0\xf2\u0258\u0141\u011f"
if sys.platform == 'darwin':
    # In Mac OS X's VFS API file names are, by definition, canonically
    # decomposed Unicode, encoded using UTF-8. See QA1173:
    # http://developer.apple.com/mac/library/qa/qa2001/qa1173.html
    import unicodedata
    TESTFN_UNICODE = unicodedata.normalize('NFD', TESTFN_UNICODE)

# TESTFN_UNENCODABLE is a filename (str type) that should *not* be able to be
# encoded by the filesystem encoding (in strict mode). It can be None if we
# cannot generate such filename.
TESTFN_UNENCODABLE = None
if os.name == 'nt':
    # skip win32s (0) or Windows 9x/ME (1)
    if sys.getwindowsversion().platform >= 2:
        # Different kinds of characters from various languages to minimize the
        # probability that the whole name is encodable to MBCS (issue #9819)
        TESTFN_UNENCODABLE = TESTFN_ASCII + "-\u5171\u0141\u2661\u0363\uDC80"
        try:
            TESTFN_UNENCODABLE.encode(sys.getfilesystemencoding())
        except UnicodeEncodeError:
            pass
        else:
            print('WARNING: The filename %r CAN be encoded by the filesystem '
                  'encoding (%s). Unicode filename tests may not be effective'
                  % (TESTFN_UNENCODABLE, sys.getfilesystemencoding()))
            TESTFN_UNENCODABLE = None
# macOS and Emscripten deny unencodable filenames (invalid utf-8)
elif sys.platform not in {'darwin', 'emscripten', 'wasi'}:
    try:
        # ascii and utf-8 cannot encode the byte 0xff
        b'\xff'.decode(sys.getfilesystemencoding())
    except UnicodeDecodeError:
        # 0xff will be encoded using the surrogate character u+DCFF
        TESTFN_UNENCODABLE = TESTFN_ASCII \
            + b'-\xff'.decode(sys.getfilesystemencoding(), 'surrogateescape')
    else:
        # File system encoding (eg. ISO-8859-* encodings) can encode
        # the byte 0xff. Skip some unicode filename tests.
        pass

# FS_NONASCII: non-ASCII character encodable by os.fsencode(),
# or an empty string if there is no such character.
FS_NONASCII = ''
for character in (
    # First try printable and common characters to have a readable filename.
    # For each character, the encoding list are just example of encodings able
    # to encode the character (the list is not exhaustive).

    # U+00E6 (Latin Small Letter Ae): cp1252, iso-8859-1
    '\u00E6',
    # U+0130 (Latin Capital Letter I With Dot Above): cp1254, iso8859_3
    '\u0130',
    # U+0141 (Latin Capital Letter L With Stroke): cp1250, cp1257
    '\u0141',
    # U+03C6 (Greek Small Letter Phi): cp1253
    '\u03C6',
    # U+041A (Cyrillic Capital Letter Ka): cp1251
    '\u041A',
    # U+05D0 (Hebrew Letter Alef): Encodable to cp424
    '\u05D0',
    # U+060C (Arabic Comma): cp864, cp1006, iso8859_6, mac_arabic
    '\u060C',
    # U+062A (Arabic Letter Teh): cp720
    '\u062A',
    # U+0E01 (Thai Character Ko Kai): cp874
    '\u0E01',

    # Then try more "special" characters. "special" because they may be
    # interpreted or displayed differently depending on the exact locale
    # encoding and the font.

    # U+00A0 (No-Break Space)
    '\u00A0',
    # U+20AC (Euro Sign)
    '\u20AC',
):
    try:
        # If Python is set up to use the legacy 'mbcs' in Windows,
        # 'replace' error mode is used, and encode() returns b'?'
        # for characters missing in the ANSI codepage
        if os.fsdecode(os.fsencode(character)) != character:
            raise UnicodeError
    except UnicodeError:
        pass
    else:
        FS_NONASCII = character
        break

# Save the initial cwd
SAVEDCWD = os.getcwd()

# TESTFN_UNDECODABLE is a filename (bytes type) that should *not* be able to be
# decoded from the filesystem encoding (in strict mode). It can be None if we
# cannot generate such filename (ex: the latin1 encoding can decode any byte
# sequence). On UNIX, TESTFN_UNDECODABLE can be decoded by os.fsdecode() thanks
# to the surrogateescape error handler (PEP 383), but not from the filesystem
# encoding in strict mode.
TESTFN_UNDECODABLE = None
for name in (
    # b'\xff' is not decodable by os.fsdecode() with code page 932. Windows
    # accepts it to create a file or a directory, or don't accept to enter to
    # such directory (when the bytes name is used). So test b'\xe7' first:
    # it is not decodable from cp932.
    b'\xe7w\xf0',
    # undecodable from ASCII, UTF-8
    b'\xff',
    # undecodable from iso8859-3, iso8859-6, iso8859-7, cp424, iso8859-8, cp856
    # and cp857
    b'\xae\xd5'
    # undecodable from UTF-8 (UNIX and Mac OS X)
    b'\xed\xb2\x80', b'\xed\xb4\x80',
    # undecodable from shift_jis, cp869, cp874, cp932, cp1250, cp1251, cp1252,
    # cp1253, cp1254, cp1255, cp1257, cp1258
    b'\x81\x98',
):
    try:
        name.decode(sys.getfilesystemencoding())
    except UnicodeDecodeError:
        TESTFN_UNDECODABLE = os.fsencode(TESTFN_ASCII) + name
        break

if FS_NONASCII:
    TESTFN_NONASCII = TESTFN_ASCII + FS_NONASCII
else:
    TESTFN_NONASCII = None
TESTFN = TESTFN_NONASCII or TESTFN_ASCII

_can_symlink = None


def can_symlink():
    global _can_symlink
    if _can_symlink is not None:
        return _can_symlink
    # WASI / wasmtime prevents symlinks with absolute paths, see man
    # openat2(2) RESOLVE_BENEATH. Almost all symlink tests use absolute
    # paths. Skip symlink tests on WASI for now.
    src = os.path.abspath(TESTFN)
    symlink_path = src + "can_symlink"
    try:
        os.symlink(src, symlink_path)
        can = True
    except (OSError, NotImplementedError, AttributeError):
        can = False
    else:
        os.remove(symlink_path)
    _can_symlink = can
    return can


def skip_unless_symlink(test):
    """Skip decorator for tests that require functional symlink"""
    ok = can_symlink()
    msg = "Requires functional symlink implementation"
    return test if ok else unittest.skip(msg)(test)


def repeat_rmtree(*args, **kwargs):
    # Windows rmtree might fail the first time
    for _ in range(5):
        try:
            shutil.rmtree(*args, **kwargs)
        except Exception:
            pass
        else:
            break
