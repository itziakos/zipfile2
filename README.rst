zipfile2 contains an improved ZipFile class that may be used as a
backward compatible replacement.

Improvements compared to upstream zipfile stdlib:

* Handling of symlinks (read and write)
* Raises an exception by default when duplicate members are detected.
* Special class `LeanZipFile` to avoid using too much memory when handling
  zip files with a large number of members. Contrary to the stdlib
  ZipFile, it does not create the list of all archives when opening the
  file. This can save 100s of MB for zipfiles with a large number of
  members.
