.. image:: https://travis-ci.org/cournape/zipfile2.png?branch=master
    :target: https://travis-ci.org/cournape/zipfile2

zipfile2 contains an improved ZipFile class that may be used as a 100 %
backward compatible replacement.

Improvements compared to upstream zipfile stdlib:

* Handling of symlinks
* Compatible 2.6 onwards (including 3.x)

Incoming:

* Raises an exception by default when writing an already existing archive
* Special class to limit number of members in an archive when unzipping,
  to avoid DDos attacks using dummy zipfiles.
