##############################################################################
#
# Copyright (c) Zope Corporation and Contributors.
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

version = '1.2.0'

import os
from setuptools import setup, find_packages
import sys

# Use unittest.mock in Python >= 3.3, or the mock package from PyPI on < 3.3
CONDITIONAL_TEST_REQUIREMENTS = ['mock'] if sys.version_info < (3, 3) else []

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

long_description=(
        read('README.txt')
        + '\n' +
        'Detailed Documentation\n'
        '**********************\n'
        + '\n' +
        read('src', 'zc', 'lockfile', 'README.txt')
        + '\n' +
        read('CHANGES.txt')
        + '\n' +
        'Download\n'
        '**********************\n'
        )

open('doc.txt', 'w').write(long_description)

setup(
    name = 'zc.lockfile',
    version=version,
    author = "Zope Foundation",
    author_email = "zope-dev@zope.org",
    description = "Basic inter-process locks",
    long_description=long_description,
    license = "ZPL 2.1",
    keywords = "lock",
    url='http://www.python.org/pypi/zc.lockfile',
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    namespace_packages = ['zc'],
    install_requires = 'setuptools',
    extras_require=dict(
        test=CONDITIONAL_TEST_REQUIREMENTS + [
            'zope.testing',
            ]),
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development',
       ],
    test_suite="zc.lockfile.tests.test_suite",
    tests_require=CONDITIONAL_TEST_REQUIREMENTS + [
        'zope.testing'],
    include_package_data = True,
    zip_safe=False,
    )
