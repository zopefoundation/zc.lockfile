##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import os
import errno
import logging
import time
logger = logging.getLogger("zc.lockfile")

class LockError(Exception):
    """Couldn't get a lock
    """

try:
    import fcntl
except ImportError:
    try:
        import msvcrt
    except ImportError:
        def _lock_file(file):
            raise TypeError('No file-locking support on this platform')
        def _unlock_file(file):
            raise TypeError('No file-locking support on this platform')

    else:
        # Windows
        def _lock_file(file):
            # Lock just the first byte
            try:
                msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
            except IOError:
                raise LockError("Couldn't lock %r" % file.name)

        def _unlock_file(file):
            try:
                file.seek(0)
                msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
            except IOError:
                raise LockError("Couldn't unlock %r" % file.name)

else:
    # Unix
    _flags = fcntl.LOCK_EX | fcntl.LOCK_NB

    def _lock_file(file):
        try:
            fcntl.flock(file.fileno(), _flags)
        except IOError:
            raise LockError("Couldn't lock %r" % file.name)

    def _unlock_file(file):
        fcntl.flock(file.fileno(), fcntl.LOCK_UN)

class LazyHostName(object):
    """Avoid importing socket and calling gethostname() unnecessarily"""
    def __str__(self):
        import socket
        return socket.gethostname()


class LockFile:

    _fp = None

    def __init__(self, path, content_template='{pid}'):
        self._path = path
        try:
            # Try to open for writing without truncation:
            fp = open(path, 'r+')
        except IOError:
            # If the file doesn't exist, we'll get an IO error, try a+
            # Note that there may be a race here. Multiple processes
            # could fail on the r+ open and open the file a+, but only
            # one will get the the lock and write a pid.
            fp = open(path, 'a+')

        try:
            _lock_file(fp)
        except:
            fp.close()
            raise

        # We got the lock, record info in the file.
        self._fp = fp
        fp.write(" %s\n" % content_template.format(pid=os.getpid(),
                                                   hostname=LazyHostName()))
        fp.truncate()
        fp.flush()

    def close(self):
        if self._fp is not None:
            _unlock_file(self._fp)
            self._fp.close()
            self._fp = None


class LockedContext(object):
    """ContextManager version of LockFile"""

    def __init__(self, name, content_template='{pid}', timeout=float("inf")):
        self.name = str(name)  # wrap in str() to allow pathlib usage
        self.content_template = content_template
        self.lock = None
        self.timeout = timeout

    def __enter__(self):
        lockname = self.name + ".lock"
        tick = 0.1
        iterations = self.timeout // tick + 1
        while iterations:
            try:
                self.lock = LockFile(lockname, self.content_template)
                return self._post_lock_operation()
            except LockError:
                logger.debug("Couldn't get lock - waiting...")
                time.sleep(tick)
                iterations -= 1
        raise LockError("Could not get lock before timeout expired")

    def _post_lock_operation(self):
        """Stub method for subclasses to extend if they want an action after
        getting the lock"""
        return self

    def __exit__(self, *args):
        """Default __exit__(). When extending, make sure to include this in a
        finally block"""
        self.lock.close()


class LockedFile(LockedContext):
    """ContextManager version of LockFile, which opens an associated file"""

    def __init__(self, name, mode, content_template='{pid}', timeout=float("inf")):
        super(LockedFile, self).__init__(
            name,
            content_template=content_template,
            timeout=timeout
        )
        self.mode = mode
        self.file = None

    def _post_lock_operation(self):
        """Overrides the default operation to open a file, then return the file"""
        self.file = open(self.name, self.mode)
        return self.file

    def __exit__(self, *args):
        try:
            return self.file.__exit__(*args)  # close the file
        finally:
            super(LockedFile, self).__exit__(*args)  # close the lock
