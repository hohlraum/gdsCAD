# -*- coding: utf-8 -*-

import os.path
import glob

#from distutils.core import setup
from setuptools import setup, find_packages

setup(
    name='gdsCAD',
    version='0.3.1',
    author='Andrew G. Mark',
    author_email='mark@is.mpg.de',
    packages=['gdsCAD'],
    url='https://github.com/hohlraum/gdsCAD',
    platforms = 'All',
    license='GNU GPLv3',
    description='A simple Python package for creating or reading GDSII layout files.',
    long_description=open('README.txt').read(),
    include_package_data=True,
#    package_data = [('gdsCAD', ['gdsCAD/ALIGNMENT.GDS',]),
#                  (os.path.join('gdsCAD', 'hershey'), glob.glob(os.path.join('gdsCAD', 'hershey', '*')))],
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