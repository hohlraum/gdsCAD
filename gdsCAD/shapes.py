# -*- coding: utf-8 -*-
"""
Classes to define simple shapes.

.. note::
    Copyright 2009-2012 Lucas Heitzmann Gabrielli
    
    Copyright 2013 Andrew G. Mark

    gdsCAD (based on gdspy) is released under the terms of the GNU GPL
    
"""

import numpy as np
from core import Boundary, Path, Elements


class Rectangle(Boundary):
    """
    Filled rectangular geometric object.

    Parameters
    ----------
    layer : integer
        The GDSII layer number for this element.
    point1 : array-like[2]
        Coordinates of a corner of the rectangle.
    point2 : array-like[2]
        Coordinates of the corner of the rectangle opposite to ``point1``.
    datatype : integer
        The GDSII datatype for this element (between 0 and 255).

    Examples
    --------
    >>> rectangle = gdspy.Rectangle(1, (0, 0), (10, 20))
    >>> myCell.add(rectangle)
    """
    
    def __init__(self, layer, point1, point2, datatype=0):
        
        points = np.array([[point1[0], point1[1]], [point1[0], point2[1]], [point2[0], point2[1]], [point2[0], point1[1]]])        
        Boundary.__init__(self, layer, points, datatype)        

    def __str__(self):
        return "Rectangle (({0[0]}, {0[1]}) to ({1[0]}, {1[1]}), layer {2}, datatype {3})".format(self.points[0], self.points[2], self.layer, self.datatype)

    def __repr__(self):
        return "Rectangle({2}, ({0[0]}, {0[1]}), ({1[0]}, {1[1]}), {3})".format(self.points[0], self.points[2], self.layer, self.datatype)


class Box(Path):
    """
    Unfilled rectangular geometric object.

    Parameters
    ----------
    layer : integer
        The GDSII layer number for this element.
    point1 : array-like[2]
        Coordinates of a corner of the rectangle.
    point2 : array-like[2]
        Coordinates of the corner of the rectangle opposite to ``point1``.
    datatype : integer
        The GDSII datatype for this element (between 0 and 255).

    Examples
    --------
    >>> rectangle = gdspy.Rectangle(1, (0, 0), (10, 20))
    >>> myCell.add(rectangle)
    """
    
    def __init__(self, layer, point1, point2, width, datatype=0):
        
        points = np.array([[point1[0], point1[1]], [point1[0], point2[1]], [point2[0], point2[1]], [point2[0], point1[1]], [point1[0], point1[1]]])        
        Path.__init__(self, layer, points, width, datatype)        

    def __str__(self):
        return "Box (({0[0]}, {0[1]}) to ({1[0]}, {1[1]}), layer {2}, datatype {3})".format(self.points[0], self.points[2], self.layer, self.datatype)

    def __repr__(self):
        return "Box ({2}, ({0[0]}, {0[1]}), ({1[0]}, {1[1]}), {3})".format(self.points[0], self.points[2], self.layer, self.datatype)


class Disk(Boundary):
    """
    A filled circle, or section of a circle
    
    """


    def __init__(self, layer, center, radius, inner_radius=0, initial_angle=0, final_angle=0, number_of_points=199, max_points=199, datatype=0):

        if final_angle == initial_angle:
            final_angle += 360.0
            
        angles = np.linspace(initial_angle, final_angle, number_of_points).T * np.pi/180.

        points=np.vstack((np.cos(angles), np.sin(angles))).T * radius + np.array(center)

        if inner_radius != 0:
            points2 = np.vstack((np.cos(angles), np.sin(angles))).T * inner_radius + np.array(center)
            points=np.vstack((points, points2[::-1]))
        
        Boundary.__init__(self, layer, points, datatype)

class Circle(Path):
    """
    An unfilled circular path or section or arc.
    """

    def __init__(self, layer, center, radius, width, initial_angle=0, final_angle=0, number_of_points=199, max_points=199, datatype=0):


        if final_angle == initial_angle:
            final_angle += 360.0
            
        angles = np.linspace(initial_angle, final_angle, number_of_points) * np.pi/180.

        points=np.vstack((np.cos(angles), np.sin(angles))).T * radius + np.array(center)

        Path.__init__(self, layer, points, width, datatype)


    def __str__(self):
        return "Circle Path ({} points, layer {}, datatype {})".format(len(self.points), self.layer, self.datatype)


class Label(Elements):
    """
    Polygonal text object. Printed as art.
    
    Each letter is formed by a series of polygons.

    Parameters
    ----------
    layer : integer
        The GDSII layer number for these elements.
    text : string
        The text to be converted in geometric objects.
    size : number
        Base size of each character.
    position : array-like[2]
        Text position (lower left corner).
    horizontal : bool
        If ``True``, the text is written from left to right; if ``False``,
        from top to bottom.
    angle : number
        The angle of rotation of the text.
    datatype : integer
        The GDSII datatype for this element (between 0 and 255).

    Examples
    --------
    >>> text = gdspy.Text(8, 'Sample text', 20, (-10, -100))
    >>> myCell.add(text)
    """
    from font import _font

    def __init__(self, layer, text, size, position=(0, 0), horizontal=True, angle=0, datatype=0) :
        polygons = []
        posX = 0
        posY = 0
        text_multiplier = size / 9.0
        if angle == 0:
            ca = 1
            sa = 0
        else:
            ca = np.cos(angle)
            sa = np.sin(angle)
        for jj in range(len(text)):
            if text[jj] == '\n':
                if horizontal:
                    posY -= 11
                    posX = 0
                else:
                    posX += 8
                    posY = 0
            elif text[jj] == '\t':
                if horizontal:
                    posX = posX + 32 - (posX + 8) % 32
                else:
                    posY = posY - 11 - (posY - 22) % 44
            else:
                if Label._font.has_key(text[jj]):
                    for p in Label._font[text[jj]]:
                        polygon = p[:]
                        for ii in range(len(polygon)):
                            xp = text_multiplier * (posX + polygon[ii][0])
                            yp = text_multiplier * (posY + polygon[ii][1])
                            polygon[ii] = (position[0] + xp * ca - yp * sa, position[1] + xp * sa + yp * ca)
                        polygons.append(np.array(polygon))
                if horizontal:
                    posX += 8
                else:
                    posY -= 11
        Elements.__init__(self, layer, polygons, datatype)

    def __str__(self):
        return "Text ({} polygons, {} vertices, layers {}, datatypes {})".format(len(self.polygons), sum([len(p) for p in self.polygons]), self.layer, self.adattype)

