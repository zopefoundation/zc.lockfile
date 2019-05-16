Lock file support
=================

The ZODB lock_file module provides support for creating file system
locks.  These are locks that are implemented with lock files and
OS-provided locking facilities.  To create a lock, instantiate a
LockFile object with a file name:

    >>> import zc.lockfile
    >>> lock = zc.lockfile.LockFile('lock')

If we try to lock the same name, we'll get a lock error:

    >>> import zope.testing.loggingsupport
    >>> handler = zope.testing.loggingsupport.InstalledHandler('zc.lockfile')
    >>> try:
    ...     zc.lockfile.LockFile('lock')
    ... except zc.lockfile.LockError:
    ...     print("Can't lock file")
    Can't lock file

.. We don't log failure to acquire.

    >>> for record in handler.records: # doctest: +ELLIPSIS
    ...     print(record.levelname+' '+record.getMessage())

To release the lock, use it's close method:

    >>> lock.close()

The lock file is not removed.  It is left behind:

    >>> import os
    >>> os.path.exists('lock')
    True

Of course, now that we've released the lock, we can create it again:

    >>> lock = zc.lockfile.LockFile('lock')
    >>> lock.close()

.. Cleanup

    >>> import os
    >>> os.remove('lock')

Hostname in lock file
=====================

In a container environment (e.g. Docker), the PID is typically always
identical even if multiple containers are running under the same operating
system instance.

Clearly, inspecting lock files doesn't then help much in debugging. To identify
the container which created the lock file, we need information about the
container in the lock file. Since Docker uses the container identifier or name
as the hostname, this information can be stored in the lock file in addition to
or instead of the PID.

Use the ``content_template`` keyword argument to ``LockFile`` to specify a
custom lock file content format:

    >>> lock = zc.lockfile.LockFile('lock', content_template='{pid};{hostname}')
    >>> lock.close()

If you now inspected the lock file, you would see e.g.:

    $ cat lock
     123;myhostname

Context Managers
================

This module also implements two Context Managers, in addition to the primitives
discussed above. The first just gets and releases a lock file, with a timeout.

    >>> with zc.lockfile.LockedContext('description', timeout=rough_seconds):
    ...    do_something()

The lock will always be released when you exit this scope. If timeout is not
given, it is assumed you wish to wait forever. It should be noted that this
Context Manager will always add '.lock' to the end of any filename you give it.
This is to allow for compatibility with its subclass:

    >>> with zc.lockfile.LockedFile('filename.ext', 'r') as f:
    ...    do_something()

This Context Manager associates a file with a lock. It supports all file modes
and operations, in addition to the lock templates and timeouts supported above.
