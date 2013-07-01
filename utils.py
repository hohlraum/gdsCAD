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
from core import (Cell, CellReference, CellArray,
                  ElementBase, Elements, ReferenceBase)

def translate(obj, v):
    """
    Translate an object 2D vector, or a sequence of 2D vectors by the given vector

    Params:
        obj: a 2D vector, or a sequence of 2D vectors
        v: 2D vector by which to translate the pts

    Returns:
        A numpy array of the translated vectors        
    """

    if isinstance(obj, (ElementBase, Elements)):
        obj=obj.copy()
        obj.translate(v)
        return obj

    return np.array(obj)+np.array(v)


def rotate(obj, theta, origin=(0,0)):
    """
    Rotate an object by given angle

    Params:
        pts: a geometric object, 2D vector, or a sequence of 2D vectors
        theta: angle by which to rotate points in deg
        origin: optional, pt about which to perform the rotation

    Returns:
        A numpy array of the rotated vectors        
    """
    if isinstance(obj, (ElementBase, Elements)):
        obj=obj.copy()
        obj.rotate(theta, origin)
        return obj

    pts=np.array(obj)
    ang = theta * np.pi/180
    m=np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]])

    if isinstance(origin, str) and origin.lower()=='com':
        origin=pts.mean(0)
    else:    
        origin=np.array(origin)

    return m.dot((np.array(pts)-origin).T).T+origin

def reflect(obj, axis, origin=(0,0)):
    """
    Reflect an object in the x or y axis

    Params:
        obj: a geometric object, 2D vector, or a sequence of 2D vectors
        axis: string 'x' or 'y' indcating which axis in which to make the refln
        origin: optional, pt about which to perform the rotation

    Returns:
        A numpy array of the reflected vectors        

    Sequences of points are reversed to maintain the same sense as the
    original sequence.    

    """
    if isinstance(obj, (ElementBase, Elements)):
        obj=obj.copy()
        obj.reflect(obj, axis, origin)
        return obj


    if axis=='x':
        return scale(obj, [1,-1], origin)
    elif axis=='y':
        return scale(obj, [-1,1], origin)
    else:
        raise ValueError('Unknown axis %s'%str(axis))


def scale(obj, k, origin=(0,0)):
    """
    Scale the pt or sequence of pts by the factor k
    
    The factor k can be a scalar or 2D vector allowing non-uniform scaling
    Optional origin can be a 2D vector or 'COM' indicating that scaling should
    be made about the pts centre of mass.
    
    Sequences of points are reversed if necessary to maintain the
    same sense as the original sequence.    
    
    """
    if isinstance(obj, (ElementBase, Elements)):
        obj=obj.copy()
        obj.scale(obj, k, origin)
        return obj

    pts=np.array(obj)
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
    for c in [subA]+deps:
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
    for c in [subB]+deps:
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


#===========================================
#functions below here probably no longer work

def chop(polygon, position, axis):
    """
    Slice polygon at a given position along a given axis.
    
    Parameters
    ----------
    polygon : array-like[N][2]
        Coordinates of the vertices of the polygon.
    position : number
        Position to perform the slicing operation along the specified
        axis.
    axis : 0 or 1
        Axis along which the polygon will be sliced.
    
    Returns
    -------
    out : tuple[2]
        Each element is a list of polygons (array-like[N][2]).    The first
        list contains the polygons left before the slicing position, and
        the second, the polygons left after that position.
    """
    out_polygons = ([], [])
    polygon = list(polygon)
    while polygon[-1][axis] == position:
        polygon = [polygon[-1]] + polygon[:-1]
    cross = list(numpy.sign(numpy.array(polygon)[:, axis] - position))
    bnd = ([], [])
    i = 0
    while i < len(cross):
        if cross[i - 1] * cross[i] < 0:
            if axis == 0:
                polygon.insert(i, [position, polygon[i - 1][1] + (position - polygon[i - 1][0]) * float(polygon[i][1] - polygon[i - 1][1]) / (polygon[i][0] - polygon[i - 1][0])])
            else:
                polygon.insert(i, [polygon[i - 1][0] + (position - polygon[i - 1][1]) * float(polygon[i][0] - polygon[i - 1][0]) / (polygon[i][1] - polygon[i - 1][1]), position])
            cross.insert(i, 0)
            bnd[1 * (cross[i + 1] > 0)].append(i)
            i += 2
        elif cross[i] == 0:
            j = i + 1
            while cross[j] == 0:
                j += 1
            if cross[i - 1] * cross[j] < 0:
                bnd[1 * (cross[j] > 0)].append(j - 1)
            i = j + 1
        else:
            i += 1
    if len(bnd[0]) == 0:
        out_polygons[1 * (numpy.sum(cross) > 0)].append(polygon)
        return out_polygons
    bnd = (numpy.array(bnd[0]), numpy.array(bnd[1]))
    bnd = (list(bnd[0][numpy.argsort(numpy.array(polygon)[bnd[0], 1 - axis])]),
           list(bnd[1][numpy.argsort(numpy.array(polygon)[bnd[1], 1 - axis])]))
    cross = numpy.ones(len(polygon), dtype=int)
    cross[bnd[0]] = -2
    cross[bnd[1]] = -1
    i = 0
    while i < len(polygon):
        if cross[i] > 0 and polygon[i][axis] != position:
            start = i
            side = 1 * (polygon[i][axis] > position)
            out_polygons[side].append([polygon[i]])
            cross[i] = 0
            nxt = i + 1
            if nxt == len(polygon):
                nxt = 0
            boundary = True
            while nxt != start:
                out_polygons[side][-1].append(polygon[nxt])
                if cross[nxt] > 0:
                    cross[nxt] = 0
                if cross[nxt] < 0 and boundary:
                    j = bnd[cross[nxt] + 2].index(nxt)
                    nxt = bnd[-cross[nxt] - 1][j]
                    boundary = False
                else:
                    nxt += 1
                    if nxt == len(polygon):
                        nxt = 0
                    boundary = True
        i += 1
    return out_polygons


def slice(layer, objects, position, axis, datatype=0):
    """
    Slice polygons and polygon sets at given positions along an axis.

    Parameters
    ----------
    layer : integer, list
        The GDSII layer numbers for the elements between each division.  If
        the number of layers in the list is less than the number of divided
        regions, the list is repeated.
    objects : ``Polygon``, ``PolygonSet``, or list
        Operand of the slice operation.  If this is a list, each element
        must be a ``Polygon``, ``PolygonSet``, ``CellReference``,
        ``CellArray``, or an array-like[N][2] of vertices of a polygon.
    position : number or list of numbers
        Positions to perform the slicing operation along the specified
        axis.
    axis : 0 or 1
        Axis along which the polygon will be sliced.
    datatype : integer
        The GDSII datatype for the resulting element (between 0 and 255).

    Returns
    -------
    out : list[N] of PolygonSet
        Result of the slicing operation, with N = len(positions) + 1.  Each
        PolygonSet comprises all polygons between 2 adjacent slicing
        positions, in crescent order.

    Examples
    --------
    >>> ring = gdspy.Round(1, (0, 0), 10, inner_radius = 5)
    >>> result = gdspy.slice(1, ring, [-7, 7], 0)
    >>> cell.add(result[1])
    """
    if (layer.__class__ != [].__class__):
        layer = [layer]
    if (objects.__class__ != [].__class__):
        objects = [objects]
    if (position.__class__ != [].__class__):
        position = [position]
    position.sort()
    result = [[] for i in range(len(position) + 1)]
    polygons = []
    for obj in objects:
        if isinstance(obj, Boundary):
            polygons.append(obj.points)
        elif isinstance(obj, Elements):
            polygons += obj.polygons
        elif isinstance(obj, CellReference) or isinstance(obj, CellArray):
            polygons += obj.get_polygons()
        else:
            polygons.append(obj)
    for i, p in enumerate(position):
        nxt_polygons = []
        for pol in polygons:
            (pol1, pol2) = chop(pol, p, axis)
            result[i] += pol1
            nxt_polygons += pol2
        polygons = nxt_polygons
    result[-1] = polygons
    for i in range(len(result)):
        result[i] = Elements(layer[i % len(layer)], result[i], datatype)
    return result


def boolean(layer, objects, operation, max_points=199, datatype=0, eps=1e-13):
    """
    Execute any boolean operation on polygons and polygon sets.

    Parameters
    ----------
    layer : integer
        The GDSII layer number for the resulting element.
    objects : array-like
        Operands of the boolean operation. Each element of this array must
        be a ``Polygon``, ``PolygonSet``, ``CellReference``, ``CellArray``,
        or an array-like[N][2] of vertices of a polygon.
    operation : function
        Function that accepts as input ``len(objects)`` integers.  Each
        integer represents the incidence of the corresponding ``object``.
        The function must return a bool or integer (interpreted as bool).
    max_points : integer
        If greater than 4, fracture the resulting polygons to ensure they
        have at most ``max_points`` vertices. This is not a tessellating
        function, so this number should be as high as possible. For
        example, it should be set to 199 for polygons being drawn in GDSII
        files.
    datatype : integer
        The GDSII datatype for the resulting element (between 0 and 255).
    eps : positive number
        Small number to be used as tolerance in intersection and overlap
        calculations.

    Returns
    -------
    out : PolygonSet
        Result of the boolean operation.

    Notes
    -----
    Since ``operation`` receives a list of integers as input, it can be
    somewhat more general than boolean operations only. See the examples
    below.

    Because of roundoff errors there are a few cases when this function
    can cause segmentation faults. If that happens, increasing the value
    of ``eps`` might help.

    Examples
    --------
    >>> circle = gdspy.Round(0, (0, 0), 10)
    >>> triangle = gdspy.Round(0, (0, 0), 12, number_of_points=3)
    >>> bad_poly = gdspy.L1Path(1, (0, 0), '+y', 2,
            [6, 4, 4, 8, 4, 5, 10], [-1, -1, -1, 1, 1, 1])
    >>> union = gdspy.boolean(1, [circle, triangle],
            lambda cir, tri: cir or tri)
    >>> intersection = gdspy.boolean(1, [circle, triangle],
            lambda cir, tri: cir and tri)
    >>> subtraction = gdspy.boolean(1, [circle, triangle],
            lambda cir, tri: cir and not tri)
    >>> multi_xor = gdspy.boolean(1, [badPath], lambda p: p % 2)
    """
    polygons = []      
    indices = [0]
    special_function = False
    for obj in objects:
        if isinstance(obj, ElementBase):
            polygons.append(obj.points)
            indices.append(indices[-1] + 1)
        elif isinstance(obj, Elements):
            special_function = True
            polygons += obj.polygons
            indices.append(indices[-1] + len(obj.polygons))
        elif isinstance(obj, CellReference) or isinstance(obj, CellArray):
            special_function = True
            a = obj.get_polygons()
            polygons += a
            indices.append(indices[-1] + len(a))
        else:
            polygons.append(obj)
            indices.append(indices[-1] + 1)
    if special_function:
        result = boolext.clip(polygons, lambda *p: operation(*[sum(p[indices[ia]:indices[ia + 1]]) for ia in range(len(indices) - 1)]), eps)
    else:
        result = boolext.clip(polygons, operation, eps)
    return None if result is None else Elements(layer, result, datatype, False).fracture(max_points)
