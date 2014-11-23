# -*- coding: utf-8 -*-
"""
Classes to define simple shapes.

Filled Objects
--------------
:class:`Rectangle`
    A filled rectangle
:class:`Disk`
    A filled circle
:class:`Ellipse`
    A filled ellipse
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

import os
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

class Ellipse(core.Boundary):
    """
    A filled ellipse, or section of an ellipse

    :param center: Coordinates of the ellipse's center.
    :param radius_x: The radius of the ellipse along x
    :param radius_y: The radius of the ellipse along y
    :param inner_radius_x: The inner radius of the ellipse along x. If absent creates a solid ellipse.
    :param inner_radius_y: The inner radius of the ellipse along y. If absent creates a solid ellipse.
    :param initial_angle: The starting angle of the sweep
    :param final_angle: The final angle of the sweep
    :param number_of_points: The number of line segments that the ellipse will be composed of
    :param layer: The GDSII layer number for this element.
        Defaults to layer of 1st object, or core.default_layer.
    :param datatype: The GDSII datatype for this element (between 0 and 255).

    Example::
        
        ellipse=shapes.Ellipse((-5,-5), 2, 4)
        ellipse.show()
    """


    def __init__(self, center, radius_x, radius_y, inner_radius_x=0, inner_radius_y=0, initial_angle=0, final_angle=0, number_of_points=199, layer=None, datatype=None):

        self.center = center
        self.radius_x = radius_x
        self.radius_y = radius_y

        if final_angle == initial_angle:
            final_angle += 360.0
            
        angles = np.linspace(initial_angle, final_angle, number_of_points).T * np.pi/180.

        points=np.vstack((radius_x*np.cos(angles), radius_y*np.sin(angles))).T + np.array(center)

        
        if inner_radius_x != 0 and inner_radius_y != 0:
            points2 = np.vstack((inner_radius_x*np.cos(angles), inner_radius_y*np.sin(angles))).T + np.array(center)
            points=np.vstack((points, points2[::-1]))
        
        core.Boundary.__init__(self, points, layer, datatype)
        
    def __str__(self):
        return "Ellipse Boundary (center={}, radius_x={}, radius_y={}, layer={}, datatype={})".format(self.center, self.radius_x, self.radius_y, self.layer, self.datatype)

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

        angles = np.linspace(0, 360, N+1, endpoint=True) * np.pi/180.

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


class LineLabel(core.Elements):
    """
    Printing text string object as Line font.

    Each letter is formed by a series of lines collected together as an
    Elements list. The lines are Hershey vector fonts. The font is basically
    a collection of symbols, containing all kinds of font styles and symbols.

    The font itself is not a monotype and no guarantee is given on the height
    of the characters. But for normal characters, the height should always be
    within the specified size.

    Since the Hershey nearly as old as ASCII, it is unfortunately not ordered
    in these codes. The font itself also contains many styles, ranging from
    Cyrillic over Greek to Roman letters.

    For convenience, lookup tables from ASCII to symbol number are provided
    for several font styles. But note, that only a fraction of all available
    symbols are mapped to ASCII characters in these tables. You can always add
    a specific symbol by yourself, once you know its Hershey code.

    +-------------+--------------------------+
    | Table name  | Description              |
    +=============+==========================+
    | gothgbt     | Gothic English Triplex   |
    +-------------+--------------------------+
    | gothgrt     | Gothic German Triplex    |
    +-------------+--------------------------+
    | gothitt     | Gothic Italian Triplex   |
    +-------------+--------------------------+
    | greekc      | Greek Complex            |
    +-------------+--------------------------+
    | greekcs     | Greek Complex Small      |
    +-------------+--------------------------+
    | greekp      | Greek Plain              |
    +-------------+--------------------------+
    | greeks      | Greek Simplex            |
    +-------------+--------------------------+
    | cyrilc      | Cyrillic complex         |
    +-------------+--------------------------+
    | italicc     | Italic Complex           |
    +-------------+--------------------------+
    | italiccs    | Italic Complex Small     |
    +-------------+--------------------------+
    | italict     | Italic Triplex           |
    +-------------+--------------------------+
    | scriptc     | Script Complex           |
    +-------------+--------------------------+
    | scripts     | Script Simplex           |
    +-------------+--------------------------+
    | romanc      | Roman Complex            |
    +-------------+--------------------------+
    | romancs     | Roman Complex Small      |
    +-------------+--------------------------+
    | romand      | Roman Duplex             |
    +-------------+--------------------------+
    | romanp      | Roman Plain              |
    +-------------+--------------------------+
    | romans      | Roman Simplex            |
    +-------------+--------------------------+
    | romant      | Roman Triplex            |
    +-------------+--------------------------+

    :param text: The text to be converted in geometric objects.
    :param size: Base size of each character.
    :param position: Text position (lower left corner).
    :param style: The default name of ASCII lookup table.
        Defaults to (romans) Roman Simplex.
    :param horizontal: If ``True``, the text is written from left to right;
      if ``False``, from top to bottom.
    :param line_width: Line width of the text.
        Defaults to one 40th of the text size.
    :param layer: The GDSII layer number for this element.
        Defaults to layer of 1st object, or core.default_layer.
    :param datatype: The GDSII datatype for this element (between 0 and 255).

    Examples::

        text = shapes.LineLabel(20, (-10, -100))
        text.add_text('Sample text', 'romand')
        text.show()
        myCell.add(text)
    """

    _DEFAULT_CHAR_HEIGHT = 40.

    _hershey_table = dict()
    _hershey_ascii_lookup_table = dict()

    def __init__(self, text, size, position=(0, 0), style='romans', horizontal=True,
                 line_width=None, layer=None, datatype=None):
        if not len(self._hershey_table):
            self._load_hersey_table()

        self._scale = size / self._DEFAULT_CHAR_HEIGHT
        self._line_width = line_width if line_width else size/40.
        self._layer = layer
        self._datatype = datatype
        self._origin = position
        self._style = style
        self._horizontal = horizontal
        self._symbols = list()
        self._symbol_pos = list(position)

        core.Elements.__init__(self)

        self.add_text(text, style)

    def _load_hersey_table(self):
        """
        Load the hersey table.

        This modifies a static class variable thus avoiding to
        read the Hersey table multiple times.
        """
        self._hershey_table.clear()

        path, _ = os.path.split(__file__)
        fname = os.path.join(path, 'resources', 'hershey', 'hershey')

        # Read lines and correct newlines
        lines = []
        append_next_line = False
        vertices_count = 0
        target_vertices_count = 0
        for line in open(fname, 'r').readlines():
            line = line.rstrip('\n')

            # Skip empty lines
            if not len(line):
                continue

            if vertices_count == target_vertices_count:
                # New entry begins here
                target_vertices_count = int(line[5:8]) * 2
                vertices_count = len(line[8:])
                lines.append(line)
            else:
                assert vertices_count < target_vertices_count, 'Got more vertices then specified'
                vertices_count += len(line)
                lines[-1] += line

        # Parse the lines we have just read
        for line in lines:
            # Skip empty lines
            if not len(line):
                continue

            char_id = int(line[:5])
            n_vertices = int(line[5:8])

            left, right = [ord(c) - ord('R') for c in line[8:10]]
            vertices = line[10:]
            assert len(vertices) % 2 == 0, 'Number coordinates needs to be even since it comes in pairs'

            # Convert ascii coordinates to true paths
            strokes = list()
            current_stroke = list()
            for coordinate in zip(vertices[::2], vertices[1::2]):
                if coordinate[0] == ' ' and coordinate[1] == 'R':
                    strokes.append(np.array(current_stroke, dtype=np.int))
                    current_stroke = list()
                    continue

                tmp_coords = [ord(coordinate[i]) - ord('R') for i in (0, 1)]
                tmp_coords[1] = -tmp_coords[1]
                current_stroke.append(tmp_coords)

            strokes.append(np.array(current_stroke, dtype=np.int))

            self._hershey_table[char_id] = {'strokes': strokes, 'left_pos': left, 'right_pos': right}

    def _load_hersey_ascii_lookup_table(self, table_name):
        """
        Load an ASCII lookup table for the given font name.

        This modifies a static class variable thus avoiding to read the
        lookup table multiple times.

        :param table_name: The table name of the lookup table.
        """
        path, _ = os.path.split(__file__)
        fname = os.path.join(path, 'resources', 'hershey', '%s.hmp' % table_name)

        to_ascii = dict()
        from_ascii = dict()

        current_code = 32
        for line in open(fname, 'r').readlines():
            for definition in line.rstrip().split():
                # Either one number or a range of number is specified
                if not '-' in definition:
                    to_ascii[int(definition)] = current_code
                    from_ascii[current_code] = int(definition)
                    current_code += 1
                else:
                    start, stop = [int(x) for x in definition.split('-')]
                    for i in range(start, stop+1):
                        to_ascii[i] = current_code
                        from_ascii[current_code] = i
                        current_code += 1

        self._hershey_ascii_lookup_table[table_name] = {'to_ascii': to_ascii, 'from_ascii': from_ascii}

    def _add_single_symbol(self, symbol):
        """
        Internal function which adds one single symbol

        :param symbol: Symbol code
        """
        # Keep track of symbols to know what we have painted here
        self._symbols.append(symbol)

        assert symbol in self._hershey_table, 'This symbol is not in the Hershey table'
        symbol = self._hershey_table[symbol]

        for stroke in symbol['strokes']:
            if not len(stroke):
                continue
            scaled_stroke = (stroke + [0, self._DEFAULT_CHAR_HEIGHT/2]) * self._scale
            stroke_path = core.Path(scaled_stroke, self._line_width, self.layer,
                                    pathtype=2, datatype=self.datatype)
            stroke_path.translate([self._symbol_pos[0] - symbol['left_pos'] * self._scale,
                                   self._symbol_pos[1]])
            self.add(stroke_path)

        if self._horizontal:
            self._symbol_pos[0] += (symbol['right_pos'] - symbol['left_pos']) * self._scale
        else:
            self._symbol_pos[0] = self._origin[0]
            self._symbol_pos[1] -= self._DEFAULT_CHAR_HEIGHT * self._scale

    def add_symbol(self, symbol):
        """
        Add one or more symbols to the label.

        :param symbol: The integer symbol code as specified in the
            Hershey sign table.
        """
        if hasattr(symbol, '__iter__'):
            for x in symbol:
                self._add_single_symbol(x)
        else:
            self._add_single_symbol(symbol)

    def add_text(self, text, style=None):
        """
        Add text to the label.

        The corresponding symbol codes are automatically looked in
        the specified lookup table.

        :param text: The text to be converted in geometric objects.
        :param style: The name of the lookup table.
            Defaults to the style passed during the creation of this
            object.
        """

        style = style if style else self._style

        if style not in self._hershey_ascii_lookup_table:
            self._load_hersey_ascii_lookup_table(style)

        lookup_table = self._hershey_ascii_lookup_table[style]['from_ascii']
        for char in str(text):
            if char == '\n':
                self._symbol_pos[0] = self._origin[0]
                self._symbol_pos[1] -= self._DEFAULT_CHAR_HEIGHT * self._scale
                continue

            ascii_value = ord(char)
            if ascii_value in lookup_table:
                self._add_single_symbol(lookup_table[ascii_value])

    def __str__(self):
        text = ''
        for symbol in self._symbols:
            ascii_found = False
            for table in self._hershey_ascii_lookup_table.values():
                if symbol in table['to_ascii']:
                    ascii_found = True
                    text += chr(table['to_ascii'][symbol])
                    break

            if not ascii_found:
                text += '{%i}' % symbol

        return "VectorText -\"{}\" layer={}".format(text, self.layer)
