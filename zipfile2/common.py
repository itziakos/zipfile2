import zipfile


class TooManyFiles(zipfile.BadZipfile):
    pass
