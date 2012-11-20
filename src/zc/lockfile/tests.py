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
from zope.testing import setupstack
import os, sys, unittest, doctest
import zc.lockfile, time, threading


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
    f.write('%d\n' % v)
    f.close()
    lock.close()

def many_threads_read_and_write():
    r"""
    >>> open('f', 'w+b').write('0\n')
    >>> open('f.lock', 'w+b').write('0\n')

    >>> n = 50
    >>> threads = [threading.Thread(target=inc) for i in range(n)]
    >>> _ = [thread.start() for thread in threads]
    >>> _ = [thread.join() for thread in threads]
    >>> saved = int(open('f', 'rb').readline().strip())
    >>> saved == n
    True

    >>> os.remove('f')
    >>> os.remove('f.lock')
    """

def pid_in_lockfile():
    r"""
    >>> import os, zc.lockfile
    >>> pid = os.getpid()
    >>> lock = zc.lockfile.LockFile("f.lock")
    >>> open("f.lock").read().strip() == str(pid)
    True

    Make sure that locking twice does not overwrite the old pid:
    
    >>> lock = zc.lockfile.LockFile("f.lock")
    Traceback (most recent call last):
      ...
    LockError: Couldn't lock 'f.lock'
    >>> open("f.lock").read().strip() == str(pid)
    True
    """

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocFileSuite(
        'README.txt',
        setUp=setupstack.setUpDirectory, tearDown=setupstack.tearDown))
    suite.addTest(doctest.DocTestSuite(
        setUp=setupstack.setUpDirectory, tearDown=setupstack.tearDown))
    return suite
