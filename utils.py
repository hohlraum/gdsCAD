# -*- coding: utf-8 -*-
########################################################################
##                                                                      ##
##    Copyright 2009-2012 Lucas Heitzmann Gabrielli                      ##
##                                                                      ##
##    This file is part of gdspy.                                          ##
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

import numpy as np
from core import (Cell, CellReference, CellArray)

def translate(pts, v):
    """
    Translate a 2D vector, or a sequence of 2D vectors by the given vector

    Params:
        pts: a 2D vector, or a sequence of 2D vectors
        v: 2D vector by which to translate the pts

    Returns:
        A numpy array of the translated vectors        
    """

    return np.array(pts)+np.array(v)


def rotate(pts, theta, origin=(0,0)):
    """
    Rotate a 2D vector, or a sequence of 2D vectors by given angle

    Params:
        theta: angle by which to rotate points
        pts: a 2D vector, or a sequence of 2D vectors
        origin: optional, pt about which to perform the rotation

    Returns:
        A numpy array of the rotated vectors        
    """

    pts=np.array(pts)
    ang = theta * np.pi/180
    m=np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]])

    if isinstance(origin, str) and origin.lower()=='com':
        origin=pts.mean(0)
    else:    
        origin=np.array(origin)
#    print 'origin:',origin

#    print 'pts-origin', np.array(pts)-origin
#    print 'm', m
#    print 'm.(pts-origin)', m.dot(np.array(pts)-origin)
    return m.dot((np.array(pts)-origin).T).T+origin

def reflect(pts, axis, origin=(0,0)):
    """
    Reflect a 2D vector, or a sequence of 2D vectors in the x or y axis

    Params:
        pts: a 2D vector, or a sequence of 2D vectors
        axis: string 'x' or 'y' indcating which axis in which to make the refln
        origin: optional, pt about which to perform the rotation

    Returns:
        A numpy array of the reflected vectors        

    Sequences of points are reversed to maintain the same sense as the
    original sequence.    

    """

    if axis=='x':
        return scale(pts, [1,-1], origin)
    elif axis=='y':
        return scale(pts, [-1,1], origin)
    else:
        raise ValueError('Unknown axis %s'%str(axis))


def scale(pts, k, origin=(0,0)):
    """
    Scale the pt or sequence of pts by the factor k
    
    The factor k can be a scalar or 2D vector allowing non-uniform scaling
    Optional origin can be a 2D vector or 'COM' indicating that scaling should
    be made about the pts centre of mass.
    
    Sequences of points are reversed if necessary to maintain the
    same sense as the original sequence.    
    
    """
    pts=np.array(pts)
    if isinstance(origin, str) and origin.lower()=='com':
        origin=pts.mean(0)
    else:    
        origin=np.array(origin)
        
    k=np.array(k)
    
    if (k.prod()>=0) or k.shape==(2,): #even parity or single point
        return (pts-origin)*k+origin
    else:
        return ((pts-origin)*k+origin)[::-1]


def split_layers(cells, old_layers):
    """
    Make two copies of the cell, split according to the layer of the artwork
    
    TODO: Include labels as well
      
    returns a pair of new cells
    """
    
#    if isinstance(cells, core.Layout):
#        new_cell=Cell('Layout')
#        if len(cells)==1:
#            new_cell.elements=[cells[cells.keys()[0]]]
#        else:
#            for c in cells.values():
#                new_cell.add(c)
#        1/0    
#
#        cells=new_cell

    subA=cells.deepcopy()
    subB=cells.deepcopy()

    #identify all art in subA that should be removed        
    blacklist=set()
    deps=subA.get_dependencies(True)
    print 'DEPENDENCY LIST HAS LENGTH: ',len(deps)
    for e in deps:
        if not isinstance(e, (Cell, CellReference, CellArray)):
            if e.layer in old_layers:
                blacklist.add(e)

    #remove references to removed art
    for c in deps:
        if isinstance(c, Cell):
            c.elements=[e for e in c.elements if e not in blacklist]
    
    #clean heirarchy
    subA.prune()
            
    #identify all art in subB that should be removed        
    blacklist=set()
    deps=subB.get_dependencies(True)
    for e in deps:
        if not isinstance(e, (Cell, CellReference, CellArray)):
            if e.layer not in old_layers:
                blacklist.add(e)

    #remove references to removed art
    for c in deps:
        if isinstance(c, Cell):
            c.elements=[e for e in c.elements if e not in blacklist]
            
    #clean heirarchy
    subB.prune()
    
    return (subA, subB)


def relayer(cell, old_layers, new_layer):
    """
    Find all elements in old_layers and move them to new_layer
    
    Returns a new cell        
    """


    new_cell=cell.deepcopy()

    #change layer of art
    for e in new_cell.get_dependencies(True):        
        if not isinstance(e, (Cell, CellReference, CellArray)):
            if e.layer in old_layers:
                e.layer=new_layer

    return new_cell


def dark_layers(layers):
    """
    Return a list of all active dark layers (i.e. layers with art on either the dark or clear layer of a pair)
    
    """

    d_layers=set()
    for l in layers:
        if l%2 == 1:
            d_layers.add(l)
        else:
            d_layers.add(l-1)

    return list(d_layers)
