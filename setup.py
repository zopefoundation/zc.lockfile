import os
from setuptools import setup, find_packages

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
        'Download\n'
        '**********************\n'
        )

open('doc.txt', 'w').write(long_description)

name = "zc.lockfile"
setup(
    name = name,
    version = "1.0.0b1",
    author = "Jim Fulton",
    author_email = "jim@zope.com",
    description = "Basic inter-process locks",
    long_description=long_description,
    license = "ZPL 2.1",
    keywords = "lock",
    url='http://www.python.org/pypi/'+name,

    packages = find_packages('src'),
    package_dir = {'': 'src'},
    namespace_packages = ['zc'],
    install_requires = 'setuptools',
    include_package_data = True,
    zip_safe=False,
    classifiers = [
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
       ],
    )
