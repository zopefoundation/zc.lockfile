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
import re
import string
import errno
import logging
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
        # File is automatically unlocked on close
        pass


class LockFileContentFormatter(string.Formatter):
    """Replace {pid} with os.getpid(), {hostname} with socket.gethostname()

    E.g. if you call ``LockFileContentFormatter().format('{pid};{hostname}')``,
    you get back something like ``'123;myhostname'``.

    Only imports the ``socket`` standard library module when actually needed for
    maximum backwards compatibility.

    If any exception occurs, uses the string ``'UNKNOWN'`` for the pid and/or
    hostname.

    """
    def get_value(self, key, args, kwargs):
        try:
            if key == 'pid':
                return os.getpid()
            elif key == 'hostname':
                import socket
                return socket.gethostname()
            else:
                return super(LockFileContentFormatter, self).get_value(
                    key, args, kwargs)
        except Exception:
            return 'UNKNOWN'


class LockFileParserFormatter(string.Formatter):
    r"""Replace fields with named regex groups and escape other text

    >>> LockFileParserFormatter().format('.{field}?')
    '\\.(?P<field>[a-zA-Z0-9.?-]+)\\?'

    """
    def parse(self, format_string):
        parsed = super(LockFileParserFormatter, self).parse(format_string)
        for literal_text, field_name, format_spec, conversion in parsed:
            yield re.escape(literal_text), field_name, format_spec, None

    def get_value(self, key, args, kwargs):
        return r'(?P<{}>[a-zA-Z0-9.?-]+)'.format(key)


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
            fp.seek(1)
            content = fp.read().strip()
            # parse pid and/or hostname from the lock file
            parse_template = LockFileParserFormatter().format(content_template)
            match = re.search(parse_template, content)
            if match:
                values_str = ' '.join(
                    '{0}={1}'.format(name, value[:20])
                    for name, value in match.groupdict().items())
            else:
                # lock file doesn't match the given format; just log what
                # zc.lockfile originally did in similar situations
                values_str = 'pid=UNKNOWN'
            fp.close()
            logger.exception("Error locking file %s; %s", path, values_str)
            raise

        # write pid and/or hostname into the lock file
        content = LockFileContentFormatter().format(content_template)
        self._fp = fp
        fp.write(" %s\n" % content)
        fp.truncate()
        fp.flush()

    def close(self):
        if self._fp is not None:
            _unlock_file(self._fp)
            self._fp.close()
            self._fp = None
