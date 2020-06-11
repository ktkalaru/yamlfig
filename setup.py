#!/usr/bin/env python
"""Configure packaging."""

from __future__ import print_function, absolute_import
import os
import re
from setuptools import setup, find_packages

############################################################################
# Packages-specific configuration
############################################################################
NAME = 'yamlfig'

VERSION_FILE = 'src/yamlfig/__version__.py'
DESCRIPTION_FILE = 'src/yamlfig/__init__.py'
LONG_DESCRIPTION_FILE = 'README.md'
LONG_DESCRIPTION_TYPE = 'text/markdown'

AUTHOR = 'ktkalaru'
AUTHOR_EMAIL = 'ktkalaru+{0}@gmail.com'.format(NAME)

URL = 'https://github.com/{0}/{1}'.format(AUTHOR, NAME)

LICENSE = 'MIT'
PLATFORMS = ['any']
KEYWORDS = ['config-file', 'validation', 'yaml']

# Ref: https://pypi.python.org/pypi?%3Aaction=list_classifiers
CLASSIFIERS = [
    # 'Development Status :: 1 - Planning',
    # 'Development Status :: 2 - Pre-Alpha',
    # 'Development Status :: 3 - Alpha',
    # 'Development Status :: 4 - Beta',
    'Development Status :: 5 - Production/Stable',
    # 'Development Status :: 6 - Mature,
    # 'Development Status :: 7 - Inactive

    'License :: OSI Approved :: MIT License',

    'Intended Audience :: Developers',

    'Operating System :: OS Independent',

    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',

    'Topic :: Software Development :: Libraries',
    'Topic :: Text Processing :: Markup'
]

PACKAGES = find_packages(where='src')
PACKAGES_DIR = {'': 'src'}
CONSOLE_SCRIPTS = []
GUI_SCRIPTS = []

PACKAGE_DATA = ['__files__/*']

# Ref: https://packaging.python.org/en/latest/requirements.html
INSTALL_REQUIRES = ['pyyaml']
PYTHON_REQUIRES = '>=2.7, !=3.0, !=3.1, !=3.2, !=3.3, !=3.4, <4'

EXTRAS_REQUIRE = {}


############################################################################
def main():
    """Marshall global variables into arguments to setup."""
    version, _ = read_version(VERSION_FILE)
    description = read_docstring_line(DESCRIPTION_FILE)
    long_description = read_file(LONG_DESCRIPTION_FILE)
    setup(
        name=NAME,
        version=version,
        description=description,
        long_description=long_description,
        long_description_content_type=LONG_DESCRIPTION_TYPE,

        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        url=URL,

        license=LICENSE,
        platforms=PLATFORMS,
        keywords=KEYWORDS,
        classifiers=CLASSIFIERS,
        packages=PACKAGES,
        package_dir=PACKAGES_DIR,

        package_data={NAME: PACKAGE_DATA},

        entry_points={
            'console_scripts': CONSOLE_SCRIPTS,
            'gui_scripts': GUI_SCRIPTS
        },

        install_requires=INSTALL_REQUIRES,
        python_requires=PYTHON_REQUIRES,
        extras_require=EXTRAS_REQUIRE

    )


def read_file(filename):
    """Read file and return contents as string."""
    with open(os.path.join(os.path.dirname(__file__), filename)) as handle:
        buf = handle.read()
    return buf


def read_version(versionpath):
    """Read version string from file and return version and shortver."""
    # pylint: disable=exec-used
    buf = read_file(versionpath)
    for line in buf.splitlines():
        match = re.search(r'^\s*__version__\s*=\s*([\'\"])(.+?)\1\s*$', line)
    if not match:
        raise ValueError('Could not find version in {0}'.format(versionpath))
    version = match.group(2)
    majver, minver = version.split('.')[0:2]
    shortver = '.'.join([majver, minver])
    return version, shortver


def read_docstring_line(docstrfile):
    """Read the first line of the first docstring encountered."""
    buf = read_file(docstrfile)
    match = re.search(r'(?s)(\'\'\'|\"\"\")(.+?)\1', buf)
    if not match:
        raise ValueError('Could not find docstring in {0}'.format(docstrfile))
    docstr = match.group(2)
    docstrlines = docstr.splitlines()
    firstline = docstrlines.pop(0)
    while firstline.isspace():
        firstline = docstrlines.pop(0)
    firstline = firstline.lstrip().rstrip()
    return firstline


main()
