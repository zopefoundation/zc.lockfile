##############################################################################
#
# Copyright (c) 2004 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
import os, re, sys, unittest, doctest
import zc.lockfile, time, threading
from zope.testing import renormalizing, setupstack
from contextlib import contextmanager
try:
    from contextlib import nested
except ImportError:
    from contextlib import ExitStack

    @contextmanager
    def nested(*args):
        with ExitStack() as stack:
            yield tuple(stack.enter_context(cm) for cm in args)

import tempfile

checker = renormalizing.RENormalizing([
    # Python 3 adds module path to error class name.
    (re.compile("zc\.lockfile\.LockError:"),
     r"LockError:"),
    ])


class OsSocketMock(object):
    """Mock object for the os and socket standard library modules"""

    def getpid(self):
        return 123

    def gethostname(self):
        return 'myhostname'

os_socket_mock = OsSocketMock()


@contextmanager
def patch_object(module, object_name, mock_object):
    """Patch an object in a module and return original after block exits"""
    original = getattr(module, object_name, 'DOES NOT EXIST')
    setattr(module, object_name, mock_object)
    try:
        yield
    finally:
        if original == 'DOES NOT EXIST':
            delattr(module, object_name)
        else:
            setattr(module, object_name, original)


@contextmanager
def patch_module(module_name, mock_object):
    """Patch a module in sys.modules and zc.lockfile, and return the original"""
    module = __import__(module_name)
    sys.modules[module_name] = mock_object
    with patch_object(zc.lockfile, module_name, mock_object):
        try:
            yield
        finally:
            sys.modules[module_name] = module


def inc():
    while 1:
        try:
            lock = zc.lockfile.LockFile('f.lock')
        except zc.lockfile.LockError:
            continue
        else:
            break
    f = open('f', 'r+b')
    v = int(f.readline().strip())
    time.sleep(0.01)
    v += 1
    f.seek(0)
    f.write(('%d\n' % v).encode('ASCII'))
    f.close()
    lock.close()

def many_threads_read_and_write():
    r"""
    >>> with open('f', 'w+b') as file:
    ...     _ = file.write(b'0\n')
    >>> with open('f.lock', 'w+b') as file:
    ...     _ = file.write(b'0\n')

    >>> n = 50
    >>> threads = [threading.Thread(target=inc) for i in range(n)]
    >>> _ = [thread.start() for thread in threads]
    >>> _ = [thread.join() for thread in threads]
    >>> with open('f', 'rb') as file:
    ...     saved = int(file.read().strip())
    >>> saved == n
    True

    >>> os.remove('f')

    We should only have one pid in the lock file:

    >>> f = open('f.lock')
    >>> len(f.read().strip().split())
    1
    >>> f.close()

    >>> os.remove('f.lock')

    """

def pid_in_lockfile():
    r"""
    >>> import os, zc.lockfile
    >>> pid = os.getpid()
    >>> lock = zc.lockfile.LockFile("f.lock")
    >>> f = open("f.lock")
    >>> _ = f.seek(1)
    >>> f.read().strip() == str(pid)
    True
    >>> f.close()

    Make sure that locking twice does not overwrite the old pid:

    >>> lock = zc.lockfile.LockFile("f.lock")
    Traceback (most recent call last):
      ...
    LockError: Couldn't lock 'f.lock'

    >>> f = open("f.lock")
    >>> _ = f.seek(1)
    >>> f.read().strip() == str(pid)
    True
    >>> f.close()

    >>> lock.close()
    """


def hostname_in_lockfile():
    r"""
    # hostname is correctly written into the lock file when it's included in the
    # lock file content template
    >>> import zc.lockfile
    >>> with patch_module('socket', os_socket_mock):
    ...     lock = zc.lockfile.LockFile("f.lock", content_template='{hostname}')
    >>> f = open("f.lock")
    >>> _ = f.seek(1)
    >>> f.read().strip() == 'myhostname'
    True
    >>> f.close()

    Make sure that locking twice does not overwrite the old hostname:

    >>> lock = zc.lockfile.LockFile("f.lock", content_template='{hostname}')
    Traceback (most recent call last):
      ...
    LockError: Couldn't lock 'f.lock'

    >>> f = open("f.lock")
    >>> _ = f.seek(1)
    >>> f.read().strip() == 'myhostname'
    True
    >>> f.close()

    >>> lock.close()
    """


class LockFileContentFormatterTestCase(unittest.TestCase):
    """Tests for the LockFileContentFormatter string formatter class"""
    def test_lock_file_content_formatter(self):
        """{pid} and {hostname} become os.getpid() and socket.gethostname()"""
        with nested(patch_module('os', os_socket_mock),
                    patch_module('socket', os_socket_mock)):
            formatter = zc.lockfile.LockFileContentFormatter()
            result = formatter.format('pid={pid} hostname={hostname}')
            assert result == 'pid=123 hostname=myhostname', repr(result)


class LockFileParserFormatterTestCase(unittest.TestCase):
    """Tests for the LockFileParserFormatter string formatter class"""
    def test_lock_file_parser_formatter(self):
        """Fields become named regex groups, everything else is escaped"""
        formatter = zc.lockfile.LockFileParserFormatter()
        parsed = formatter.format(' {bam}.{foo!r}bar{baz} ')
        assert parsed == (r'\ (?P<bam>[a-zA-Z0-9.?-]+)'
                          r'\.(?P<foo>[a-zA-Z0-9.?-]+)'
                          r'bar(?P<baz>[a-zA-Z0-9.?-]+)\ '), repr(parsed)


class TestLogger(object):
    def __init__(self):
        self.log_entries = []

    def exception(self, msg, *args):
        self.log_entries.append((msg,) + args)


class LockFileLogEntryTestCase(unittest.TestCase):
    """Tests for logging in case of lock failure"""
    def setUp(self):
        self.here = os.getcwd()
        self.tmp = tempfile.mkdtemp()
        os.chdir(self.tmp)

    def tearDown(self):
        os.chdir(self.here)
        setupstack.rmtree(self.tmp)

    def test_log_entry(self):
        """PID and hostname are parsed and logged from lock file on failure"""
        test_logger = TestLogger()

        def lock(locked, before_closing):
            lock = None
            try:
                lock = zc.lockfile.LockFile('f.lock',
                                            content_template='{pid}/{hostname}')
            except Exception:
                pass
            locked.set()
            before_closing.wait()
            if lock is not None:
                lock.close()

        with nested(patch_module('os', os_socket_mock),
                    patch_module('socket', os_socket_mock),
                    patch_object(zc.lockfile, 'logger', test_logger)):
            first_locked = threading.Event()
            second_locked = threading.Event()
            thread1 = threading.Thread(target=lock,
                                       args=(first_locked, second_locked))
            thread2 = threading.Thread(target=lock,
                                       args=(second_locked, second_locked))
            thread1.start()
            first_locked.wait()
            assert not test_logger.log_entries
            thread2.start()
            thread1.join()
            thread2.join()
        expected = [('Error locking file %s; %s',
                     'f.lock',
                     'hostname=myhostname pid=123')]
        assert test_logger.log_entries == expected, test_logger.log_entries


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocFileSuite(
        'README.txt', checker=checker,
        setUp=setupstack.setUpDirectory, tearDown=setupstack.tearDown))
    suite.addTest(doctest.DocTestSuite(
        setUp=setupstack.setUpDirectory, tearDown=setupstack.tearDown,
        checker=checker))
    # Add doctests from zc/lockfile/__init__.py
    suite.addTest(doctest.DocTestSuite(zc.lockfile))
    # Add unittest test cases from this module
    suite.addTest(
        unittest.TestLoader().loadTestsFromModule(sys.modules[__name__]))
    return suite
