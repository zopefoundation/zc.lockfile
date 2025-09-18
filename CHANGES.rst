Change History
***************

4.0 (unreleased)
================

- Replace ``pkg_resources`` namespace with PEP 420 native namespace.

- Add support for Python 3.12, 3.13.

- Drop support for Python 3.7, 3.8.


3.0.post1 (2023-02-28)
======================

- Add ``python_requires`` to ``setup.py`` to prevent installing on not
  supported old Python versions.


3.0 (2023-02-23)
================

- Add support for Python 3.9, 3.10, 3.11.

- Drop support for Python 2.7, 3.5, 3.6.

- Drop support for deprecated ``python setup.py test``.


2.0 (2019-08-08)
================

- Extracted new ``SimpleLockFile`` that removes implicit behavior
  writing to the lock file, and instead allows a subclass to define
  that behavior.
  (`#15 <https://github.com/zopefoundation/zc.lockfile/issues/15>`_)

- ``SimpleLockFile`` and thus ``LockFile`` are now new-style classes.
  Any clients relying on ``LockFile`` being an old-style class will
  need to be adapted.

- Drop support for Python 3.4.

- Add support for Python 3.8b3.


1.4 (2018-11-12)
================

- Claim support for Python 3.6 and 3.7.

- Drop Python 2.6 and 3.3.


1.3.0 (2018-04-23)
==================

- Stop logging failure to acquire locks. Clients can do that if they wish.

- Claim support for Python 3.4 and 3.5.

- Drop Python 3.2 support because pip no longer supports it.

1.2.1 (2016-06-19)
==================

- Fixed: unlocking and locking didn't work when a multiprocessing
  process was running (and presumably other conditions).

1.2.0 (2016-06-09)
==================

- Added the ability to include the hostname in the lock file content.

- Code and ReST markup cosmetics.
  [alecghica]

1.1.0 (2013-02-12)
==================

- Added Trove classifiers and made setup.py zest.releaser friendly.

- Added Python 3.2, 3.3 and PyPy 1.9 support.

- Removed Python 2.4 and Python 2.5 support.

1.0.2 (2012-12-02)
==================

- Fixed: the fix included in 1.0.1 caused multiple pids to be written
  to the lock file

1.0.1 (2012-11-30)
==================

- Fixed: when there was lock contention, the pid in the lock file was
  lost.

  Thanks to Daniel Moisset reporting the problem and providing a fix
  with tests.

- Added test extra to declare test dependency on ``zope.testing``.

- Using Python's ``doctest`` module instead of depreacted
  ``zope.testing.doctest``.

1.0.0 (2008-10-18)
==================

- Fixed a small bug in error logging.

1.0.0b1 (2007-07-18)
====================

- Initial release
