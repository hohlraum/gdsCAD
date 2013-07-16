# -*- coding: utf-8 -*-
"""
Classes to define simple shapes.

Filled Objects
--------------
:class:`Rectangle`
    A filled rectangle
:class:`Disk`
    A filled circle
:class:`RegPolygon`
    A filled regular polygon
:class:`Label`
    Printing text

Unfilled Objects
----------------
:class:`Box`
    An unfilled rectangle
:class:`RegPolyline`
    An ufilled regular polygon
:class:`Circle`
    An unfilled circle


.. note::
    Copyright 2009-2012 Lucas Heitzmann Gabrielli
    
    Copyright 2013 Andrew G. Mark

    gdsCAD (based on gdspy) is released under the terms of the GNU GPL
    
"""

import numpy as np

import core


class Rectangle(core.Boundary):
    """
    Filled rectangular geometric object.

    :param point1: Coordinates of a corner of the rectangle.
    :param point2: Coordinates of the corner of the rectangle opposite to ``point1``.
    :param layer: The GDSII layer number for this element.
        Defaults to layer of 1st object, or core.default_layer.
    :param datatype: The GDSII datatype for this element (between 0 and 255).

    Examples::

        rectangle = shapes.Rectangle((0, 0), (10, 20))
        myCell.add(rectangle)
    """
    
    def __init__(self, point1, point2, layer=None, datatype=None):
        
        points = np.array([[point1[0], point1[1]], [point1[0], point2[1]], [point2[0], point2[1]], [point2[0], point1[1]]])        
        core.Boundary.__init__(self, points,  layer, datatype)        

    def __str__(self):
        return "Rectangle (({0[0]}, {0[1]}) to ({1[0]}, {1[1]}), layer {2}, datatype {3})".format(self.points[0], self.points[2], self.layer, self.datatype)

    def __repr__(self):
        return "Rectangle({2}, ({0[0]}, {0[1]}), ({1[0]}, {1[1]}), {3})".format(self.points[0], self.points[2], self.layer, self.datatype)


class Box(core.Path):
    """
    Unfilled rectangular geometric object.

    :param point1: Coordinates of a corner of the rectangle.
    :param point2: Coordinates of the corner of the rectangle opposite to ``point1``.
    :param width: The width of the line
    :param layer: The GDSII layer number for this element.
        Defaults to layer of 1st object, or core.default_layer.
    :param datatype: The GDSII datatype for this element (between 0 and 255).

    Examples::
        
        box = shapes.Box((0, 0), (10, 20), 0.5)
        myCell.add(box)
    """
    
    def __init__(self, point1, point2, width, layer=None, datatype=None):
        
        points = np.array([[point1[0], point1[1]], [point1[0], point2[1]], [point2[0], point2[1]], [point2[0], point1[1]], [point1[0], point1[1]]])        
        core.Path.__init__(self, points, width, layer, datatype)        

    def __str__(self):
        return "Box (({0[0]}, {0[1]}) to ({1[0]}, {1[1]}), layer {2}, datatype {3})".format(self.points[0], self.points[2], self.layer, self.datatype)

    def __repr__(self):
        return "Box ({2}, ({0[0]}, {0[1]}), ({1[0]}, {1[1]}), {3})".format(self.points[0], self.points[2], self.layer, self.datatype)


class Disk(core.Boundary):
    """
    A filled circle, or section of a circle

    :param center: Coordinates of the disk's center.
    :param radius: The radius of the disk
    :param inner_radius: The inner radius of the disk. If absent creates a solid disk.
    :param initial_angle: The starting angle of the sweep
    :param final_angle: The final angle of the sweep
    :param number_of_points: The number of line segments that the disk will be composed of
    :param layer: The GDSII layer number for this element.
        Defaults to layer of 1st object, or core.default_layer.
    :param datatype: The GDSII datatype for this element (between 0 and 255).

    Example::
        
        disk=shapes.Disk((-5,-5), 5)
        disk.show()    
    """


    def __init__(self, center, radius, inner_radius=0, initial_angle=0, final_angle=0, number_of_points=199, layer=None, datatype=None):

        self.center = center
        self.radius = radius

        if final_angle == initial_angle:
            final_angle += 360.0
            
        angles = np.linspace(initial_angle, final_angle, number_of_points).T * np.pi/180.

        points=np.vstack((np.cos(angles), np.sin(angles))).T * radius + np.array(center)

        if inner_radius != 0:
            points2 = np.vstack((np.cos(angles), np.sin(angles))).T * inner_radius + np.array(center)
            points=np.vstack((points, points2[::-1]))
        
        core.Boundary.__init__(self, points, layer, datatype)
        
    def __str__(self):
        return "Disk Boundary (center={}, radius={}, layer={}, datatype={})".format(self.center, self.radius, self.layer, self.datatype)
    
    
class Circle(core.Path):
    """
    An unfilled circular path or section or arc.

    :param center: Coordinates of the disk's center.
    :param radius: The radius of the disk.
    :param width: The width of the line.
    :param initial_angle: The starting angle of the sweep.
    :param final_angle: The final angle of the sweep.
    :param number_of_points: The number of line segments that the disk will be composed of.
    :param layer: The GDSII layer number for this element.
        Defaults to layer of 1st object, or core.default_layer.
    :param datatype: The GDSII datatype for this element (between 0 and 255).
    
    Example::
        
        circ=shapes.Circle((10,10), 10, 0.5)
        circ.show()
    """

    def __init__(self, center, radius, width, initial_angle=0, final_angle=0, number_of_points=199, layer=None, datatype=None):

        self.center = center
        self.radius = radius

        if final_angle == initial_angle:
            final_angle += 360.0
            
        angles = np.linspace(initial_angle, final_angle, number_of_points) * np.pi/180.

        points=np.vstack((np.cos(angles), np.sin(angles))).T * radius + np.array(center)

        core.Path.__init__(self, points, width, layer, datatype)


    def __str__(self):
        return "Circle Path ({} points, width {}, layer {}, datatype {})".format(len(self.points), self.width, self.layer, self.datatype)

class RegPolygon(core.Boundary):
    """
    An unfilled regular polgyon.

    :param center: Coordinates of the disk's center.
    :param length: The length of an edge.
    :param N: The number of sides
    :param layer: The GDSII layer number for this element.
        Defaults to layer of 1st object, or core.default_layer.
    :param datatype: The GDSII datatype for this element (between 0 and 255).
    
    Example::
        
        pent = shapes.RegPolygon((10,10), 10, 5)
        pent.show()
    """

    def __init__(self, center, length, N, layer=None, datatype=None):

        self.center = center
        self.length = length
        self.N = N

        angles = np.linspace(0, 360, N, endpoint=False) * np.pi/180.

        alpha = angles[1]
        radius = length / np.sin(alpha/2) /2.
        points=np.vstack((np.cos(angles), np.sin(angles))).T * radius + np.array(center)

        core.Boundary.__init__(self, points, layer, datatype)


    def __str__(self):
        return "RegPolygon Boundary ({} points, width {}, layer {}, datatype {})".format(len(self.points), self.width, self.layer, self.datatype)


class RegPolyline(core.Path):
    """
    An unfilled regular polgyon.

    :param center: Coordinates of the disk's center.
    :param length: The length of an edge.
    :param N: The number of sides
    :param width: The width of the line.
    :param layer: The GDSII layer number for this element.
        Defaults to layer of 1st object, or core.default_layer.
    :param datatype: The GDSII datatype for this element (between 0 and 255).
    
    Example::
        
        hex=shapes.RegPolylone((10,10), 10, 6, 0.5)
        hex.show()
    """

    def __init__(self, center, length, N, width, layer=None, datatype=None):

        self.center = center
        self.length = length
        self.N = N

        angles = np.linspace(0, 360, N, endpoint=False) * np.pi/180.

        alpha = angles[1]
        radius = length / np.sin(alpha/2) /2.
        points=np.vstack((np.cos(angles), np.sin(angles))).T * radius + np.array(center)

        core.Path.__init__(self, points, width, layer, datatype)


    def __str__(self):
        return "RegPolyine Path ({} points, width {}, layer {}, datatype {})".format(len(self.points), self.width, self.layer, self.datatype)


class Label(core.Elements):
    """
    Printing text string object.
    
    Each letter is formed by a series of polygons collected together as an
    Elements list.

    :param text: The text to be converted in geometric objects.
    :param size: Base size of each character.
    :param position: Text position (lower left corner).
    :param horizontal: If ``True``, the text is written from left to right;
      if ``False``, from top to bottom.
    :param angle: The angle of rotation of the text.
    :param layer: The GDSII layer number for this element.
        Defaults to layer of 1st object, or core.default_layer.
    :param datatype: The GDSII datatype for this element (between 0 and 255).

    Examples::
        
        text = shapes.Label('Sample text', 20, (-10, -100))
        text.show()
        myCell.add(text)
    """
    from font import _font

    def __init__(self, text, size, position=(0, 0), horizontal=True, angle=0, layer=None, datatype=None) :

        self.text=text
        self.position=position

        polygons = []
        posX = 0
        posY = 0
        text_multiplier = size / 9.0

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
                            polygon[ii] = (xp, yp)
                        polygons.append(np.array(polygon))
                if horizontal:
                    posX += 8
                else:
                    posY -= 11
        core.Elements.__init__(self, polygons, layer, datatype)
        self.rotate(angle)
        self.translate(position)

    def __str__(self):
        return "Text -\"{}\" layer={}".format(self.text, self.layer)

