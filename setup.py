# -*- coding: utf-8 -*-

from setuptools import setup
from git_version import sdist, get_version
import os.path
import glob

setup(
    name='gdsCAD',
    version = get_version(),
    author='Andrew G. Mark',
    author_email='mark@is.mpg.de',
    url='https://github.com/hohlraum/gdsCAD',
    platforms = 'All',
    license='GNU GPLv3',
    description='A simple Python package for creating or reading GDSII layout files.',
    long_description=open('README.txt').read(),
    cmdclass={"sdist": sdist },
    packages=['gdsCAD'],
    package_dir={'gdsCAD': 'gdsCAD'},
    package_data = {'gdsCAD': ['resources/ALIGNMENT.GDS', 'resources/hershey/*']},
    classifiers = ['Development Status :: 3 - Alpha',
        'Intended Audience :: Education',
        'Intended Audience :: Manufacturing',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)'
        ]
)