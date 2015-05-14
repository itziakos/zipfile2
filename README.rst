.. image:: https://travis-ci.org/cournape/zipfile2.png?branch=master
    :target: https://travis-ci.org/cournape/zipfile2

zipfile2 contains an improved ZipFile class that may be used as a 100 %
backward compatible replacement.

Improvements compared to upstream zipfile stdlib:

* Handling of symlinks (read and write)
* Compatible 2.6 onwards (including 3.x), include context manager
* Raises an exception by default when duplicate members are detected.

Incoming:

* Special class to limit number of members in an archive when unzipping,
  to avoid DDos attacks using dummy zipfiles.
