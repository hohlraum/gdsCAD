# -*- coding: utf-8 -*-
########################################################################
##                                                                      ##
##    Copyright 2009-2012 Lucas Heitzmann Gabrielli                      ##
##    Copyright 2013      Andrew G. Mark                                                                      ##
##
##    This file is part of gdsCAD.                                          ##
##                                                                      ##
##    gdspy is free software: you can redistribute it and/or modify it  ##
##    under the terms of the GNU General Public License as published      ##
##    by the Free Software Foundation, either version 3 of the          ##
##    License, or any later version.                                      ##
##                                                                      ##
##    gdspy is distributed in the hope that it will be useful, but      ##
##    WITHOUT ANY WARRANTY; without even the implied warranty of          ##
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the      ##
##    GNU General Public License for more details.                      ##
##                                                                      ##
##    You should have received a copy of the GNU General Public          ##
##    License along with gdspy.  If not, see                              ##
##    <http://www.gnu.org/licenses/>.                                      ##
##                                                                      ##
########################################################################


import core
import shapes
import utils
import templates

__all__ = ['core', 'shapes', 'templates', 'utils'] 
__author__ = 'Andrew G. Mark'

try:
    from _version import __version__ as v
    __version__ = v
    del v
except ImportError:
    __version__ = "UNKNOWN"