# -*- coding: utf-8 -*-
# Author: Douglas Creager <dcreager@dcreager.net>
# Modified: Andrew Mark
#
# Updates the package version number to reflect the git tag of the current commit.
#
# There are two normal use cases:
#  python setup.py sdist: Building a source distribution. This is expected to
#         take place in a folder tracked by git. The return value of "git --tags"
#         is taken as the version number, and this is stored in version_file
#         as part of the distribution.
#  python setup.py install: Here the version number is taken from the value
#         stored in version_file
#
# The file version_file should not be tracked. Doing so will lead to version
# recursion, since it is updated only after the latest version has been
# committed and tagged.
#
# To use this script, simply import it your setup.py file, and use the
# results of get_version() as your package version, and add the locally defined
# command 'sdist' as a cmdclass:
#
# from git_version import get_version, sdist
#
# setup(
#     version=get_git_version(),
#     cmdclass={"sdist": sdist },
#     .
#     .
# )
from __future__ import absolute_import, print_function, unicode_literals

__all__ = ("get_version",)

from distutils.command.sdist import sdist as _sdist
from subprocess import Popen, PIPE
import re

version_file = 'gdsCAD/_version.py'

def git_version():
    """Return the git tag of the current commit"""
    try:
        p = Popen(['git', 'describe', '--tags'],
                  stdout=PIPE, stderr=PIPE)
        p.stderr.close()
        line = p.stdout.readlines()[0].decode('utf-8')
        return line.strip()

    except:
        return None

def file_version():
    """Return the version number stored in _version.py"""
    try:
        f = open(version_file)
    except EnvironmentError:
        return None
    for line in f.readlines():
        mo = re.match("__version__ = '([^']+)'", line)
        if mo:
            ver = mo.group(1)
            return ver
    return None


VERSION_PY = """
# This version number is untracked and may not be up to date. 
# It is updated during source builds.

__version__ = "%s"
"""

def update_f_version(new_ver):
    """Change the version number stored in _version.py"""
    with open(version_file, "w") as f:
        f.write(VERSION_PY % new_ver)

class sdist(_sdist):
    """New sdist command that updates the version number stored in _version.py"""
    def run(self):
        version = get_version()        
        update_f_version(version)
        self.distribution.metadata.version = version
        return _sdist.run(self)

def get_version():
    # Read in the version that's currently in RELEASE-VERSION.
    f_version = file_version()

    # First try to get the current version using “git describe”.
    version = git_version()

    # If that doesn't work, fall back on the value that's in
    # RELEASE-VERSION.
    if version is None:
        version = f_version

    # If we still don't have anything, that's an error.
    if version is None:
        raise ValueError("Cannot find the version number!")

    # Finally, return the current version.
    return version


if __name__ == "__main__":
    print(get_version())
