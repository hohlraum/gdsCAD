# -*- coding: utf-8 -*-
"""
The primary geometry elements, layout and organization classes.

The objects found here are intended to correspond directly to elements found in
the GDSII specification.

The fundamental gdsCAD object is the Layout, which contains all the information
to be sent to the mask shop. A Layout can contain multiple Cells which in turn
contain references to other Cells, or contain drawing geometry.

:class:`Layout`
    The container holding all design data (GDSII: LIBRARY)
:class:`Cell`
    A collection of drawing elements, and/or references to other Cells
    (GDSII: STRUCTURE)
**Primitive Elements:**
    These can all be added to a cell. Only :class:`Boundary` and :class:`Path`
    are drawing elements.
    
    * :class:`Boundary`: A filled polygon (GDSII: BOUNDARY)    
    * :class:`Path`: An unfilled polygonal line (GDSII: PATH)
    * :class:`Text`: Non-printing labelling text (GDSII: TEXT)
    * :class:`CellReference`: A simple reference to another Cell (GDSII: SREF)
    * :class:`CellArray`: A reference to another cell to be copied multiple
      times (GDSII: AREF)    
    * :class:`Elements`: A listlike collection of Boundary or Path drawing elements
      (no GDSII equivalent)


.. note::
    Copyright 2009-2012 Lucas Heitzmann Gabrielli
    
    Copyright 2013 Andrew G. Mark

    gdsCAD (based on gdspy) is released under the terms of the GNU GPL
    
"""
from __future__ import print_function
from __future__ import absolute_import


import sys
import struct
import numbers
import inspect
import datetime
import warnings
import numpy as np
import copy
import pdb
import string
import os.path

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches
    import matplotlib.text
    import matplotlib.lines
    import matplotlib.transforms as transforms
    import matplotlib.cm
    import shapely.geometry
    import descartes
except ImportError as err:
    warnings.warn(str(err) + '. It will not be possible to display designs.')

try:
    import dxfgrabber
except ImportError as err:
    warnings.warn(str(err) + '. It will not be possible to import DXF artwork.')

if sys.version > '3':
    long = int

default_layer = 1
default_datatype = 0

def _show(self):
    """
    Display the object
    
    :returns: the display Axes.
    
    """
    ax = plt.gca()
    ax.set_aspect('equal')
    ax.margins(0.1)    

    textbox = []    
    
    artists=self.artist()
    for a in artists:
        a.set_transform(a.get_transform() + ax.transData)
        if isinstance(a, matplotlib.patches.Patch):
            ax.add_patch(a)
        elif isinstance(a, matplotlib.lines.Line2D):
            ax.add_line(a)
        else:
            ax.add_artist(a)
            textbox.append(a.get_position())
    
    if textbox:        
        textbox = np.array(textbox)
        ax.update_datalim_numerix(textbox[:,0], textbox[:,1])

    ax.autoscale(True)
    plt.show()
    
    return ax



class BooleanOps(object):
    """
    Boolean operations base class.
    """

    @staticmethod
    def _shapely2gds(shape):
        """
        Convert a shapely Polygon or Multipolygon to a gdsCAD Boundary or Elements.
        """
        msg = 'A boolean op has resulted in interior voids. These will be lost.'
        if isinstance(shape, shapely.geometry.MultiPolygon):
            for g in shape:
                if g.interiors:
                    warnings.warn(msg)                    
            return Elements([Boundary(g.exterior) for g in shape])
        else:
            if shape.interiors:
                warnings.warn(msg)                    
                
            return Boundary(shape.exterior)    

    def __and__(self, other):
        """
        The intersection between two drawing elements.        
        """

        new = self.shape.intersection(other.shape)

        return self._shapely2gds(new)

    def __or__(self, other):
        """
        The union between two drawing elements.

        # How do we decide what the attributes (layer, datatype, etc) should be
        """        
        new = self.shape.union(other.shape)

        return self._shapely2gds(new)

    def __sub__(self, other):
        """
        The difference between two drawing elements.

        TODO: This does not deal with interior voids.
        """
        new = self.shape.difference(other.shape)

        return self._shapely2gds(new)

    def __xor__(self, other):
        """
        The symmetric difference between two drawing elements.

        TODO: This does not deal with interior voids.
        """
        new = self.shape.symmetric_difference(other.shape)

        return self._shapely2gds(new)


class ElementBase(BooleanOps, object):
    """
    Base class for geometric elements. Other drawing elements derive from this.
    """
    @staticmethod
    def _layer_properties(layer):
        # Default colors from previous versions
        colors = ['k', 'r', 'g', 'b', 'c', 'm', 'y']
        colors += matplotlib.cm.gist_ncar(np.linspace(0.98, 0, 15))
        color = colors[layer % len(colors)]
        return {'color': color}

    def __init__(self, points, dtype=np.float32):
        self._points = np.array(points, dtype=dtype)
        self._bbox = None

    @property
    def points(self):
        return self._points

    @points.setter
    def points(self, points, dtype=np.float32):
        """
        Change points for this object.

        :returns: self
        """
        self._points = np.array(points, dtype=dtype)
        self._bbox = None
        return self

    @property
    def laydat(self):
        return (self.layer, self.datatype)
    
    @laydat.setter
    def laydat(self, new_laydat):
        self._layer = new_laydat[0]
        self._datatype = new_laydat[1]

    def copy(self, suffix=None):
        """
        Make a copy of this element.
        
        :param suffix: Ignored
        """
        return copy.deepcopy(self)
       
    def translate(self, displacement):
        """
        Translate this object.

        :param displacment:  The vector by which to displace this object.
        :returns: self
            
        The transformation acts in place.
        """
        self._points += np.array(displacement)
        self._bbox = None
        return self
            
    def rotate(self, angle, center=(0, 0)):
        """
        Rotate this object.
        
        :param angle: The angle of rotation (in deg).        
        :param center: Center point for the rotation.        
        :returns: self

        The optional center point can be specified by a 2D vector or the string 'com'
        for center of mass.

        The transformation acts in place.
        """

        ang = angle * np.pi/180
        m=np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]])
    
        if isinstance(center, str) and center.lower()=='com':
            center=self.points.mean(0)
        else:    
            center=np.array(center)
    
        self._points = m.dot((self.points-center).T).T+center
        self._bbox = None
        return self    


    def reflect(self, axis, origin=(0,0)):
        """
        Reflect this object in the x or y axis
    
        :param axis: 'x' or 'y' indicating which axis in which to make the refln
        :param origin: A point which will remain invariant on reflection
        :returns: self
        
        Optional origin can be a 2D vector or 'COM' indicating that scaling should
        be made about the pts centre of mass.

        The transformation acts in place.

        """
        if axis=='x':
            self.scale([1,-1], origin)
        elif axis=='y':
            self.scale([-1,1], origin)
        else:
            raise ValueError('Unknown axis %s'%str(axis))
    
        return self    
   
    def scale(self, k, origin=(0,0)):
        """
        Scale this object by the factor k

        :param k: the value by which to scale the object
        :param origin: the point about which to make the scaling
        :returns: self
        
        The factor k can be a scalar or 2D vector allowing non-uniform scaling.
        Optional origin can be a 2D vector or 'COM' indicating that scaling should
        be made about the pts centre of mass.

        The transformation acts in place.
        
        """
        if isinstance(origin, str) and origin.lower()=='com':
            origin=self.points.mean(0)
        else:    
            origin=np.array(origin)
            
        k=np.array(k)
        
        self._points=(self.points-origin)*k+origin
        self._bbox = None
        return self    

    @property
    def bounding_box(self):
        """
        Return the bounding box containing the polygon
        """

        if self._bbox is not None:
            return self._bbox.copy()

        bb = np.zeros([2,2])
        bb[0,0] = self._points[:,0].min()
        bb[0,1] = self._points[:,1].min()
        bb[1,0] = self._points[:,0].max()
        bb[1,1] = self._points[:,1].max()

        self._bbox = bb
        return bb
        

class Boundary(ElementBase):
    """
    A filled, closed polygonal geometric object.

    :param points: Coordinates of the vertices of the polygon.
    :param layer: The GDSII layer number for this element
        Defaults to core.default_layer.
    :param datatype: The GDSII datatype for this element (between 0 and 255).
    :param verbose: If False, warnings about the number of vertices of the
        polygon will be suppressed.
    
    .. note::
        This is a direct equivalent to the Boundary element found in the GDSII
        specification.    
    
    The last point should not be equal to the first (polygons are
    automatically closed).
    
    The official GDSII specification supports only a maximum of 199 vertices per
    polygon.

    Examples::
        triangle_pts = [(0, 40), (15, 40), (10, 50)]
        triangle = gdsCAD.core.Boundary(triangle_pts)
        myCell.add(triangle)
    """
    
    show=_show
    
    def __init__(self, points, layer=None, datatype=None, laydat=None, verbose=False, dtype=np.float32) :
        points = np.asarray(points, dtype=dtype)
        if (points[0] != points[-1]).any():
            points = np.concatenate((points, [points[0]]))

        ElementBase.__init__(self, points)

        if verbose and 8191 >= self.points.shape[0] > 199:
            warnings.warn("[GDSPY] A polygon with more than 199 points was created "
                          "(not officially supported by the GDSII format).", stacklevel=2)
        if verbose and self.points.shape[0] > 8191:
            warnings.warn("[GDSPY] A polygon with more than 8191 points was created."
                          "Multiple XY required which is an unofficial GDSII extension.", stacklevel=2)

        ## Enable specifying (layer, datatype) with laydat tuple
        if laydat:
            (layer, datatype) = laydat

        if layer is None:
            self.layer = default_layer
        else:
            self.layer = layer

        if datatype is None:
            self.datatype = default_datatype
        else:
            self.datatype = datatype

    def __repr__(self):
        return self.__class__.__name__ + \
            "(laydat=({},{}), num_pts={})".format(self.layer, self.datatype, len(self.points))

    def __str__(self):
        return self.__class__.__name__ + \
            "(laydat=({},{}), points={})".format(self.layer, self.datatype, self.points.tolist())

    def area(self):
        """
        Calculates the area of the element.
        """
        return self.shape.area

    def centroid(self):
        """
        Calculates the centroid of the element.

        :returns: The tuple (x, y) of element's centroid
        """
        centroid = self.shape.centroid
        return (centroid.x, centroid.y)

    def is_ccw(self):
        """
        Returns True if coordinates are in counter-clockwise order
        """
        points = self.points.tolist()
        return sum((points[i+1][0]-points[i][0])*(points[i+1][1]+points[i][1]) for i in range(len(points)-1)) < 0

    def to_ccw(self):
        """
        Fixes coordinates to be in counter-clockwise order
        """
        if not self.is_ccw():
            self.points = list(reversed(self.points.tolist()))

    def to_gds(self, multiplier): 
        """
        Convert this object to a GDSII element.
        
        :param multiplier: A number that multiplies all dimensions written in the GDSII
            element.
        
        :returns: The GDSII binary string that represents this object.
        """
        gds_coordinates = np.array(np.round(self._points * multiplier), dtype='>i4')

        nr_points = gds_coordinates.shape[0]
        export_pos = 0

        data = struct.pack('>' + 4 *'HH', 4, 0x0800, 6, 0x0D02, self.layer, 6, 0x0E02, self.datatype)

        # Export coordinates, if there are more than 8191 points split it into several XY entries
        # This is an unofficial but very common extension of the GDSII protocol.
        while export_pos < gds_coordinates.shape[0]:
            entry_points = min(8191, nr_points - export_pos)
            data_size = 4 + 8 * entry_points

            data += struct.pack('>HH', data_size, 0x1003)
            data += gds_coordinates[export_pos:export_pos+entry_points].tostring()

            export_pos += entry_points

        data += struct.pack('>HH', 4, 0x1100)
        return data

    def to_path(self, width=1.0, pathtype=0):
        """
        Convert this Boundary to a Path
        
        :param width: The width of the line
        :param pathtype:  The endpoint style
        """
        
        return Path(self.points, width=width, layer=self.layer,
                    datatype=self.datatype, pathtype=pathtype, verbose=False,
                    dtype=self.points.dtype)

    def artist(self):
        """
        Return a list of matplotlib artists to draw this object        
        """
        return [matplotlib.patches.Polygon(self.points, closed=True, lw=0, **self._layer_properties(self.layer))]

    @property
    def shape(self):
        """
        A shapely polygon representation of the boundary
        """
        s = shapely.geometry.asPolygon(self._points)
        s.laydat = self.laydat
        return s


class Path(ElementBase):
    """
    An unfilled, unclosed polygonal line of fixed width.

    :param points: Coordinates of the vertices of the polygon.
    :param width: The width of the line
    :param layer: The GDSII layer number for this element.
        Defaults to core.default_layer.
    :param datatype: The GDSII datatype for this element (between 0 and 255).
    :param pathtype:  The endpoint style
    
    .. note::
        This is a direct equivalent to the Path element found in the GDSII
        specification.    
    
    Paths are not automatically closed. The official GDSII specification
    supports only a maximum of 199 vertices per path.

    
    The style of endcaps is specificed by pathtype:

    ====  =================================   
    ====  =================================   
    0     Square ended paths
    1     Round ended
    2     Square ended, extended 1/2 width
    4     Variable length extensions
    ====  =================================   
    

    Examples::
        
        arrow_pts = [(0, 40), (15, 40), (10, 50)]
        arrow = gdsCAD.core.Path(arrow_pts)
        myCell.add(arrow)
    """
    show=_show

    def __init__(self, points, width=1.0, layer=None, datatype=None, laydat=None, pathtype=0, verbose=False, dtype=np.float32):
        ElementBase.__init__(self, points, dtype=dtype)


        if verbose and self.points.shape[0] > 199:
            warnings.warn("[GDSPY] A Path with more than 199 points was created "
                          "(not officially supported by the GDSII format).", stacklevel=2)

        if self.points.shape[0] > 8191:
            raise ValueError('Paths with more than 8191 not supported by GDSII')

        self.width=width
        self.pathtype=pathtype

        ## Enable specifying (layer, datatype) with laydat tuple
        if laydat:
            (layer, datatype) = laydat

        if layer is None:
            self.layer = default_layer
        else:
            self.layer = layer

        if datatype is None:
            self.datatype = default_datatype
        else:
            self.datatype = datatype

    def __repr__(self):
        return self.__class__.__name__ + \
            "(laydat=({},{}), width={}, pathtype={}, num_pts={})".format(self.layer, self.datatype, self.width, self.pathtype, len(self.points))

    def __str__(self):
        return self.__class__.__name__ + \
            "(laydat=({},{}), width={}, pathtype={}, points={})".format(self.layer, self.datatype, self.width, self.pathtype, self.points.tolist())

    def area(self):
        """
        Calculates the area of the element.
        """
        return self.shape.area

    def centroid(self):
        """
        Calculates the centroid of the element.

        :returns: The tuple (x, y) of element's centroid
        """
        centroid = self.shape.centroid
        return (centroid.x, centroid.y)

    def to_gds(self, multiplier): 
        """
        Convert this object to a GDSII element.
        
        :param multiplier : A number that multiplies all dimensions written
            in the GDSII element.
        
        :returns: The GDSII binary string that represents this object.
        """

        gds_coordinates = np.array(np.round(self._points * multiplier), dtype='>i4')

        data = struct.pack('>12H', 4, 0x0900, 6, 0x0D02, self.layer, 6, 0x0E02, self.datatype, 6, 0x2102, self.pathtype, 8)
        data += struct.pack('>HL2H', 0x0F03, int(round(self.width * multiplier)), 4 + 8 * gds_coordinates.shape[0], 0x1003)
        data += gds_coordinates.tostring()
        return data + struct.pack('>2H', 4, 0x1100)

    def to_boundary(self):
        """
        Convert this Path to a Boundary.
        
        Open paths will be closed as boundaries.
        """
  
        return Boundary(self.points, layer=self.layer, datatype=self.datatype, 
                    verbose=False, dtype=self.points.dtype)


    def artist(self, color=None):
        """
        Return a list of matplotlib artists to draw this object        

        Paths are rendered by first converting them to a shapely polygon
        and then converting this to a descartes polgyonpatch. This generates
        a path whose line width scales with the drawing size.

        """
        
        cap_style = {0:2, 1:1, 2:3}
        points=[tuple(p) for p in self.points]
        lines = shapely.geometry.LineString(points)
        poly = lines.buffer(self.width/2., cap_style=cap_style[self.pathtype], join_style=2, mitre_limit=np.sqrt(2))

        return [descartes.PolygonPatch(poly, lw=0, **self._layer_properties(self.layer))]

    @property
    def shape(self):
        """
        A shapely polygon representation of the boundary
        """
        cap_style = {0:2, 1:1, 2:3} 
        points=[tuple(p) for p in self.points]
        line = shapely.geometry.asLineString(points)
        s = line.buffer(self.width/2., cap_style=cap_style[self.pathtype], join_style=2, mitre_limit=np.sqrt(2))
        s.laydat = self.laydat
        return s


class Text(ElementBase):
    """
    A non-printing text label    
       
    :param text: The text of this label.
    :param position: Text anchor position.
    :param anchor: Position of the anchor relative to the text.
    :param rotation: Angle of rotation of the label (in *degrees*).
    :param magnification: Magnification factor for the label.
    :param layer: The GDSII layer number for this element.
        Defaults to core.default_layer.
    :param datatype: The GDSII texttype for the label (between 0 and 63).

    .. note::
        This is a direct equivalent to the Text element found in the GDSII
        specification. With the caveat that the GDSII texttype record is mapped
        to the datatype attribute in gdsCAD.
   

    Text that can be used to label parts of the geometry or display
    messages. The text does not create additional geometry, it's meant for
    display and labeling purposes only.


    Examples::
        
        txt = gdspy.Text('Sample label', (10, 0), 'sw')
        myCell.add(txt)
    """

    _anchor = {'nw':0,  'top left':0,      'upper left':0,   'tl':0,
               'n':1,   'top center':1,    'upper center':1, 'tc':1,
               'ne':2,  'top right':2,     'upper right':2,  'tr':2,
               'w':4,   'middle left':4,                     'cl':4,
               'o':5,   'middle center':5,                   'cc':5,
               'e':6,   'middle right':6,                    'cr':6,
               'sw':8,  'bottom left':8,   'lower left':8,   'bl':8,
               's':9,   'bottom center':9, 'lower center':9, 'bc':9,
               'se':10, 'bottom right':10, 'lower right':10, 'br':10}

    show = _show

    def __init__(self, text, position, anchor='o', rotation=None,
                 magnification=None, layer=None, datatype=None, laydat=None,
                 x_reflection=None, dtype=np.float32):
        ElementBase.__init__(self, position, dtype=dtype)
        self.text = text
        self.anchor = Text._anchor[anchor.lower()]
        self.rotation = rotation
        self.x_reflection = x_reflection
        self.magnification = magnification

        ## Enable specifying (layer, datatype) with laydat tuple
        if laydat:
            (layer, datatype) = laydat

        if layer is None:
            self.layer = default_layer
        else:
            self.layer = layer

        if datatype is None:
            self.datatype = default_datatype
        else:
            self.datatype = datatype

    def __repr__(self):
        text = self.text[:10] + '...' if len(self.text)>10 else ''
        return self.__class__.__name__ + \
            "(\"{}\", posn={}, laydat=({},{}), anchor={}, rot={}, mag={}, x_refl={})".format(text, self.points.tolist(), self.layer, self.datatype, self.anchor, self.rotation, self.magnification, self.x_reflection)

    def __str__(self):
        return self.__class__.__name__ + \
            "(\"{}\", posn={}, laydat=({},{}), anchor={}, rot={}, mag={}, x_refl={})".format(self.text, self.points.tolist(), self.layer, self.datatype, self.anchor, self.rotation, self.magnification, self.x_reflection)

    def area(self):
        """
        The area of the element.
        
        For text this is always 0, since it is non-printing.
        """
        return 0

    def to_gds(self, multiplier):
        """
        Convert this text to a GDSII element.

        :param multiplier: A number that multiplies all dimensions written
            in the GDSII structure.
        
        :returns: The GDSII binary string that represents this label.
        """
        text = self.text
        if len(text)%2 != 0:
            text = text + '\0'
        data = struct.pack('>11h', 4, 0x0C00, 6, 0x0D02, self.layer, 6, 0x1602, self.datatype, 6, 0x1701, self.anchor)
        if not (self.rotation is None and self.magnification is None):
            word = 0
            values = b''
            if not (self.magnification is None):
                word += 0x0004
                values += struct.pack('>2h', 12, 0x1B05) + _eight_byte_real(self.magnification)
            if not (self.rotation is None):
                word += 0x0002
                values += struct.pack('>2h', 12, 0x1C05) + _eight_byte_real(self.rotation)
            data += struct.pack('>2hH', 6, 0x1A01, word) + values
        return data + struct.pack('>2h2l2h', 12, 0x1003, int(round(self.points[0] * multiplier)), int(round(self.points[1] * multiplier)), 4 + len(text), 0x1906) + text.encode('ascii') + struct.pack('>2h', 4, 0x1100)

    def rotate(self, angle, center=(0, 0)):
        """
        Rotate this object.
        
        :param angle: The angle of rotation (in deg).
        :param center: Center point for the rotation.        
        :returns: self
            
        The transformation acts in place.
        """
        if self.rotation is None:
            self.rotation = angle
        else:
            self.rotation += angle
        ElementBase.rotate(self, angle, center)

        return self    

    def reflect(self, axis, origin=(0,0)):
        """
        Reflect this object in the x or y axis
    
        :param axis: 'x' or 'y' indcating which axis in which to make the refln
        :param origin:  A point which will remain invariant on reflection
        :returns: self
        Optional origin can be a 2D vector or 'COM' indicating that scaling should
        be made about the pts centre of mass.

        The transformation acts in place.

        """
        if self.x_reflection is None:
            self.x_reflection = True
        else:
            self.x_reflection ^= True
        
        ElementBase.reflect(self, axis, origin)

        if axis=='y':
            self.rotate(180, origin)
        return self    

    @property
    def bounding_box(self):
        """
        Return the bounding box containing the Text
        
        It's not really clear how this should work, but for the moment
        it only returns the point of insertion        
        """
        bb = np.array((self.points, self.points))
        return bb

    def artist(self):
        """
        Return a list of matplotlib artists for drawing this object
        
        .. warning::
            
            Does not properly handle rotations or scaling
        """

        return [matplotlib.text.Text(self.points[0], self.points[1], self.text, **self._layer_properties(self.layer))]


class Elements(BooleanOps, object):
    """ 
    A list-like collection of Boundary and/or Path objects.

    :param obj : List containing the coordinates of the vertices of each polygon.
        Or a list of already defined elements.
    :param layer: The GDSII layer number for this element.
        Defaults to layer of 1st object, or core.default_layer.
    :param datatype: The GDSII datatype for this element (between 0 and 255).
    :param obj_type: Specify whether to interpret the list of point arrays
        as boundaries, or paths
    
    The class :class:`Elements` is intended to simplify geometric transformations on several
    drawing elements at once. There is no GDSII equivalent. Elements is not
    a substitute for :class:`Cell`. In particular, multiple Elements added to
    a design cannot be added by reference. Each instance will be seperately
    written to the file.
    
    There are many different ways of initializing an Elements list. The simplest
    is to call it with no parameters i.e. Elements() and then add elements. One
    list of elements can be added to another. The individual objects in the first
    Elements list will be added to the second so that the list is flat.

    All elements in the list share the same layer and datatype. Changing the
    layer or datatype for the Elements list changes it for all contained
    elements

    Elements can be indexed using simple indexing::
        
        print elist[1]

    Elements can be used as an iterator::
        
        for el in elist:
            print el

    Examples::
        
        square_pts=[[0,0], [1,0], [1,1], [0,1]]
        triangle_pts=[[1,0], [2,0], [2,2]]

        square=Boundary(square_pts)
        triangle=Path(triangle_pts, width=0.5)

        # Create an empty list and fill it later
        elist=Elements()
        elist.add(square)
        elist.add(triangle)

        # Create a filled square and an unfilled triangle
        elist=Elements([square, triangle])

        # Create two filled boundaries from a list of points
        elist=Elements([square_pts, triangle_pts])
        
        # Create two unfilled paths from a list of points
        elist=Elements([square_pts, triangle_pts], obj_type='path', width=0.5)
    
        # Create a filled square and an unfilled triangle
        elist=Elements([square_pts, triangle_pts], obj_type=['boundary', 'path'])
    
    
    
    """
    show = _show

    def __init__(self, obj=None, layer=None, datatype=None, laydat=None, obj_type=None, **kwargs):

        self.obj = []

        ## Enable specifying (layer, datatype) with laydat tuple
        if laydat:
            (layer, datatype) = laydat

        # No parameters => Create an empty Elements list
        if (laydat is None) and (layer is None) and (obj is None):
            return #Empty list

        # A list of elements => Create an identical list
        if isinstance(obj[0], ElementBase):
            self._check_obj_list(obj)
            self.obj=list(obj)
            layer = obj[0].layer
            datatype = obj[0].datatype

        # Expecting list of point sequences
        else:
            # Use the pts to define Boundaries
            if obj_type is None:
                obj_type=['boundary']*len(obj)
            # Use the points to pts to create the obj_type defined
            elif isinstance(obj_type, str):
                obj_type=[obj_type]*len(obj)
            elif len(obj_type) != len(obj):
                raise ValueError('Length of obj_type list must match that of obj list')
    
            for p, t in zip(obj, obj_type):
                if t.lower() == 'boundary':
                    self.obj.append(Boundary(p, layer, datatype, **kwargs))
                elif t.lower() == 'path':
                    self.obj.append(Path(p, layer=layer, datatype=datatype, **kwargs))

        if layer is None:
            self.layer = default_layer
        else:
            self.layer = layer

        if datatype is None:
            self.datatype = default_datatype
        else:
            self.datatype = datatype

    def _check_obj_list(self, obj_list):
        for o in obj_list:
            if not isinstance(o, (ElementBase)):
                raise TypeError('Object list must contain only Boundaries or Paths')

    @property
    def layer(self):
        """
        Get the layer
        """
        return self._layer
    
    @layer.setter
    def layer(self, val):
        """
        Set the layer
        """
        self._layer=val
        for p in self:
            p.layer=val
      
    @property
    def datatype(self):
        """
        Get the datatype
        """
        return self._datatype
    
    @datatype.setter
    def datatype(self, val):
        """
        Set the datatype
        """
        self._datatype=val
        for p in self:
            p.datatype=val
  
    @property
    def laydat(self):
        """
        Get the laydat
        """
        return (self._layer, self._datatype)
    
    @laydat.setter
    def laydat(self, val):
        """
        Set the laydat
        """
        (self._layer, self._datatype)=val
        for p in self:
            (p.layer, p.datatype)=val
      
    def copy(self, suffix=None):
        """
        Make a copy of the object and all contained elements
        """
        return copy.deepcopy(self)

    def __repr__(self):
        if len(self.obj):
            ans =  "Elements(["
            for e in self:
                ans += '\n ' + repr(e)
            return ans+' ])'
        else:
            return "Elements()"
    
    def __str__(self):
        if len(self.obj):
            ans =  "Elements(["
            for e in self:
                ans += '\n ' + str(e)
            return ans+' ])'
        else:
            return "Elements()"
    
    def add(self, obj):
        """
        Add a new element or list of elements to this list.
                
        :param element: The element to be inserted in this list.
        
        """
        if isinstance(obj, Elements):
            self._check_obj_list(obj)
            self.obj.extend(obj)
            return
            
        if not isinstance(obj, ElementBase):
            raise ValueError('Can only add a drawing element to Elements')

        if len(self.obj) == 0:
            self.layer = obj.layer
            self.datatype = obj.datatype

        self.obj.append(obj)

    def remove(self, element):
        """
        Remove an element or list of elements.

        :param element: The element or list of elements to be removed.
        """
        if isinstance(element, (Elements)):
            element = list(element)
        elif not isinstance(element, (tuple, list)):
            element = [element]
        
        for e in element:
            self.obj.remove(e)

    def __len__(self):
        """
        Return the number of elements in the list
        """
        return len(self.obj)


    def __getitem__(self, index):
        """
        Get the element at index
        """
        return self.obj[index]

    def __setitem__(self, index, value):
        """
        Set a new element at index
        """
        self.obj[index]=value

    def __iter__(self):
        """
        Iterate over elements in list
        """
        return iter(self.obj)

    def translate(self, displacement):
        """
        Translate this object.

        :param displacement: The vector by which to displace all the elements.        
        :returns: self

        The transformation acts in place.
        """
        displacement=np.array(displacement)
        for p in self:
            p.translate(displacement)
        return self

    def rotate(self, angle, center=(0, 0)):
        """
        Rotate this object.
        
        :param angle: The angle of rotation (in deg).
        :param center: Center point for the rotation.        
        :returns: self

        The transformation acts in place.
        """
        for p in self:
            p.rotate(angle, center)
        return self

    def reflect(self, axis, origin=(0,0)):
        """
        Reflect this object in the x or y axis
    
        :param axis: 'x' or 'y' indcating which axis in which to make the refln
        :param origin: A point which will remain invariant on reflection
        :returns: self
        
        Optional origin can be a 2D vector or 'COM' indicating that scaling should
        be made about the pts centre of mass.

        The transformation acts in place.
        """
        
        for p in self:
            p.reflect(axis, origin)
        return self
    
    def scale(self, k, origin=(0,0)):
        """
        Scale this object by the factor k

        :param k: the value by which to scale the object
        :param origin: the point about which to make the scaling
        :returns: self
        
        The factor k can be a scalar or 2D vector allowing non-uniform scaling.
        Optional origin can be a 2D vector or 'COM' indicating that scaling should
        be made about the pts centre of mass.

        The transformation acts in place.        
        """
        for p in self:
            p.scale(k, origin)

        return self

    def area(self):
        """
        Calculate the area of the elements.
        """
        area = 0        
        for e in self:
            area += e.area()
        
        return area
        
    def centroid(self):
        """
        Calculates the centroid of all the elements in Elements.

        :returns: The tuple (x, y) of Element's centroid
        """
        centroid = self.shape.centroid
        return (centroid.x, centroid.y)

    def to_gds(self, multiplier):
        """
        Convert this object to a series of GDSII elements.
        
        :param multiplier:  A number that multiplies all dimensions written
            in the GDSII elements.        
        :returns: The GDSII binary string that represents this object.
        """
        data = b''

        for p in self:
            data += p.to_gds(multiplier)

        return data

    @property
    def bounding_box(self):
        """
        Return the bounding box containing all Elements
        """
        subboxes=[]
        for p in self:
            subboxes.append(p.bounding_box)

        subboxes=np.array(subboxes)
        bb = np.array([[min(subboxes[:, 0,0]),
                          min(subboxes[:, 0,1])],
                          [max(subboxes[:, 1,0]),
                          max(subboxes[:, 1,1])]])

        return bb

    def artist(self, color=None):
        """
        Return a list of matplotlib artists for drawing this object        
        """
        art=[]
        for p in self:
            art+=p.artist()
        return art

    @property
    def shape(self):
        """
        A shapely polygon representation of the boundary
        """
        return shapely.geometry.MultiPolygon([element.shape for element in self.obj])


class Layout(dict):
    """
    A layout object    

    :param name: Name of the GDSII library.
    :param unit: Unit size for the objects in the library (in *meters*).
    :param precision: Precision for the dimensions of the objects in the
        library (in *meters*).


    A layout is a dict based collection of Cells. Cells can be accessed
    by their name::
        l=gdsCAD.core.Layout('layout')
        l.add(top_cell)
        print l[top_cell.name]

    The dimensions actually written on the GDSII file will be the
    dimensions of the objects created times the ratio ``unit/precision``.
    For example, if a circle with radius 1.5 is created and we set
    ``unit=1.0e-6`` (1 um) and ``precision=1.0e-9`` (1 nm), the radius of
    the circle will be 1.5 um and the GDSII file will contain the dimension
    1500 nm.
    
    .. note::
        This is a direct equivalent to the Library element found in the GDSII
        specification.    

    """

    show=_show
    
    def __init__(self, name='library', unit=1e-6, precision=1.e-9, created=None, modified=None):

        dict.__init__(self)
        self.name=name
        self.unit=unit
        self.precision=precision

        now = datetime.datetime.today()
        if created:
            self.created=created
        else:
            self.created=now
        if modified:
            self.modified=modified
        else:
            self.modified=now

    def add(self, cell):
        """
        Add a new cell to this layout.
        
        :param element: The Cell to be inserted in this Layout.
        
        """
        
        names=[c.name for c in self.get_dependencies()]                
        
        if cell.name in names:
            warnings.warn("A cell named {0} is already in this library.".format(cell.name))

        self[cell.name]=cell
        

    def get_dependencies(self):
        """
        Returns a list of all cells included in this layout.
        
        Subcells are checked recursively
        
        :param out: List of the cells referenced by this cell.
        """

        dependencies = set(self.values())
        for cell in self.values():
            dependencies |= set(cell.get_dependencies())
                    
        return list(dependencies)

    def copy(self):
        """
        Creates a deep copy of this Layout.

        :returns: The new copy of this layout.

        This makes a deep copy, all elements are recursively duplicated
        """
        return copy.deepcopy(self)

        
    def save(self, outfile):
        """
        Output a list of cells as a GDSII stream library.

        Cell names are checked for uniqueness. If there are duplicate cell
        names then a unique ID is appended to the cell name to force uniqueness.

        :param outfile: The file (or path) where the GDSII stream will be
            written. It must be opened for writing operations in binary format.
        """
        close_source = False
        if not hasattr(outfile, "write"):
            outfile = os.path.expanduser(outfile)
            outfile = open(outfile, "wb")
            close_source = True

        cells=self.get_dependencies()

        cell_names = [x.name for x in cells]
        duplicates = set([x for x in cell_names if cell_names.count(x) > 1])
        if duplicates: 
            print('Duplicate cell names that will be made unique:', ', '.join(duplicates))

        print('Writing the following cells')
        for cell in cells:
            if cell.name not in duplicates:
                print(cell.name+':',cell)
            else:
                print(cell.unique_name+':',cell)

        longlist=[name for name in sorted(cell_names) if len(name)>32]
        if longlist:
            print('%d of the cells have names which are longer than the official GDSII limit of 32 character' % len(longlist))
            print('---------------')
            for n in longlist:
                print(n, ' : %d chars'%len(n))
            
        if len(self.name)%2 != 0:
            name = self.name + '\0'
        else:
            name = self.name
        
        c = list(self.created.timetuple()[:6])
        m = list(self.modified.timetuple()[:6])
        outfile.write(struct.pack('>19h', 6, 0x0002, 0x0258, 28, 0x0102,
                                  c[0], c[1], c[2], c[3], c[4], c[5],
                                  m[0], m[1], m[2], m[3], m[4], m[5],
                                  4+len(name), 0x0206) + name.encode('ascii') + struct.pack('>2h', 20, 0x0305) + _eight_byte_real(self.precision / self.unit) + _eight_byte_real(self.precision))

        for cell in cells:
            outfile.write(cell.to_gds(self.unit / self.precision, duplicates))

        outfile.write(struct.pack('>2h', 4, 0x0400))

        if close_source:
            outfile.close()

    def top_level(self):
        """
        Output the top level cells from the GDSII layout.  Top level cells 
        are those that are not referenced by any other cells.

        :returns: List of top level cells.
        """
        top = list(self.values())
        for cell in self.values():
            for dependency in cell.get_dependencies():
                if dependency in top:
                    top.remove(dependency)
        return top

    @property
    def bounding_box(self):
        """
        Returns the bounding box for this layout.
        
        :returns: Bounding box of this cell [[x_min, y_min], [x_max, y_max]], or
            ``None`` if the cell is empty.
        """

        top=self.top_level()

        boxes=[e.bounding_box for e in top]
        boxes=np.array([b for b in boxes if b is not None]) #discard empty cells
        
        return np.array([[min(boxes[:,0,0]), min(boxes[:,0,1])],
                     [max(boxes[:,1,0]), max(boxes[:,1,1])]])

    def artist(self):
        """
        Return a list of matplotlib artists for drawing this object

        Returns artists for every top level cell in this layout
        """        
        
        top=self.top_level()
        artists=[]
        
        for c in top:
            artists += c.artist()
        
        return artists


class Cell(object):
    """
    Collection of elements, both geometric objects and references to other
    cells.
    
    :param name: The name of the cell.
    """
    

    show=_show
     
    def __init__(self, name, created=None, modified=None):
        self.name = str(name)
        self._objects = []
        self._references = []

        now = datetime.datetime.today()
        if created:
            self.created=created
        else:
            self.created=now
        if modified:
            self.modified=modified
        else:
            self.modified=now

    @property
    def elements(self):
        return self.objects + self.references

    @property
    def objects(self):
        """
        Get all elements excluding any references.
        """
        return tuple(self._objects)

    @property
    def references(self):
        """
        Get all references in this cell.
        """
        return tuple(self._references)
 
    def objects_by_laydat(self, laydat):
        """
        Returns a list of objects of this cell that match a laydat tuple.

        :returns: list of objects of this cell that match a laydat tuple.
        """
        objects = []
        for element in self.objects:
            if (element.layer, element.datatype) == laydat:
                objects.append(element)
        return objects

    def __str__(self):
        return "Cell (\"{}\", {} elements, {} references)".format(self.name, len(self.objects),
                                                                             len(self.references))

    def __getitem__(self, index):
        """
        Get the element at index
        """
        return self.elements[index]

    def __setitem__(self, index, value):
        """
        Set a new element at index
        """
        self.elements[index]=value

    def __iter__(self):
        """
        Iterate over elements in list
        """
        return iter(self.elements)

    def __len__(self):
        return len(self.elements)

    @property
    def unique_name(self):
        return self.name + '_' + _compact_id(self)        

    def to_gds(self, multiplier, duplicates=[]):
        """
        Convert this cell to a GDSII structure.

        :param multiplier: A number that multiplies all dimensions written
            in the GDSII structure.
        :param uniquify: If True saves the cell reference according to its
            uniquified name.
        
        :returns: The GDSII binary string that represents this cell.
        """
        
        name = self.unique_name if self.name in duplicates else self.name

        if len(name)%2 != 0:
            name = name + '\0'
            
        c = list(self.created.timetuple()[:6])
        m = list(self.modified.timetuple()[:6])
        data = struct.pack('>16h', 28, 0x0502,
                            c[0], c[1], c[2], c[3], c[4], c[5],
                            m[0], m[1], m[2], m[3], m[4], m[5],
                           4 + len(name), 0x0606) + name.encode('ascii')
        for element in self:
            if isinstance(element, ReferenceBase):
                data += element.to_gds(multiplier, duplicates)
            else:
                data += element.to_gds(multiplier)
                
        return data + struct.pack('>2h', 4, 0x0700)
        
    def copy(self, name=None, suffix=None):
        """
        Creates a deepcopy of this cell.

        This makes a deep copy, all elements are recursively duplicated

        :param name: The name of the new cell.
        :param suffix: A suffix to add to the end of the name of every subcell       
        
        :returns: The new copy of this cell.
        """
        
        new_cell=copy.deepcopy(self)
        if name is None:            
            if suffix is not None:
                new_cell.name+=suffix
        else:
            new_cell.name = name
        
        if suffix is not None:
            deps=new_cell.get_dependencies(include_elements=True)
            for cell in [e for e in deps if isinstance(e, Cell)]:
                cell.name += suffix

        return new_cell


    def add(self, element, *args, **kwargs):
        """
        Add a new element or list of elements to this cell.

        :param element: The element or list of elements to be inserted in this cell.
        
        A :class:`Cell` are added by implicitly creating a :class:`CellReference`,
        they can be accompanied by all the arguments available when explicity
        using :class:`CellReference`. To add a Cell as an array it is necessary
        to first create the :class:`CellArray` and then add that.
        
        """
        if isinstance(element, Cell):
            self._references.append(CellReference(element, *args, **kwargs))
        elif isinstance(element, (ElementBase, Elements, ReferenceBase)):

            if len(args)!=0 or len(kwargs)!=0:
                raise TypeError('Cannot have extra arguments when adding elements')                        

            if isinstance(element, ReferenceBase):
                self._references.append(element)
            else:
                self._objects.append(element)

        elif isinstance(element, (tuple, list)):
            for e in element:
                self.add(e, **kwargs)
        
        else:
            raise TypeError('Cannot add type %s to cell.' % type(element))

        self.bb_is_valid = False
    
    def remove(self, element):
        """
        Remove an element or list of elements from this cell.

        :param element: The element or list of elements to be removed from this cell.

        """
        if isinstance(element, (Elements)):
            element = list(element)
        elif not isinstance(element, (tuple, list)):
            element = [element]

        for e in element:
            if isinstance(e, ReferenceBase):
                self._references.remove(e)
            else:
                self._objects.remove(e)
#        self._objects = [e for e in self._objects if e not in element]

        self.bb_is_valid = False

    def area(self, by_layer=False):
        """
        Calculate the total area of the elements on this cell, including
        cell references and arrays.
        
        :param by_layer: If ``True``, the return value is a dictionary with the areas of
            each individual layer.
        
        :returns: Area of this cell.
        """
        if by_layer:
            cell_area = {}
            for element in self.elements:
                element_area = element.area(True)
                for ll in element_area.iterkeys():
                    if ll in cell_area:
                        cell_area[ll] += element_area[ll]
                    else:
                        cell_area[ll] = element_area[ll]
        else:
            cell_area = 0
            for element in self.elements:
                cell_area += element.area()
        return cell_area

    def prune(self):
        """       
        Remove any subcells that contain no elements.

        :returns: True if the cell and all of its subcells contain no elements
        """        
        blacklist=[]
        for c in self.references:
             val=c.ref_cell.prune()
             if val:
                 blacklist += [c]
    
        self._references=[e for e in self.references if e not in blacklist]

        return False if len(self) else True
        
    def get_layers(self):
        """
        Returns a list of layers in this cell.

        :returns: List of the layers used in this cell.
        """
        layers = set()
        for element in self.elements:
            if isinstance(element, (ElementBase, Elements)):
                layers.add(element.layer)
            elif isinstance(element, ReferenceBase):
                layers |= set(element.ref_cell.get_layers())

        return list(layers)

    def get_laydats(self):
        """
        Returns a list of (layer, datatype) tuples only in this cell.

        :returns: list of (layer, datatype) tuples only in this cell.
        """
        layers_datatypes = set()
        for element in self.elements:
            if isinstance(element, (ElementBase, Elements)):
                layers_datatypes.add((element.layer, element.datatype))
        return sorted(list(layers_datatypes))

    @property
    def bounding_box(self):
        """
        Returns the bounding box for this cell.
        
        :returns: Bounding box of this cell [[x_min, y_min], [x_max, y_max]], or
            ``None`` if the cell is empty.
        """
        if len(self) == 0:
            return None

        boxes=[e.bounding_box for e in self]
        boxes=np.array([b for b in boxes if b is not None])
        
        return np.array([[min(boxes[:,0,0]), min(boxes[:,0,1])],
                     [max(boxes[:,1,0]), max(boxes[:,1,1])]])


    def get_dependencies(self, include_elements=False):
        """
        Returns a list of all cells included as references by this cell.
        
        Subcells are checked recursively.
        
        :param include_elements: If true returns a complete list of all
            elements in the heirarchy                
        
        :returns: List of the cells referenced by this cell.
        """


        dependencies = []
        
        for reference in self.references:
            dependencies += reference.get_dependencies(include_elements)
            
        if include_elements:
            dependencies += self.elements
                    
        return dependencies

    def artist(self):
        """
        Return a list of matplotlib artists for drawing this object
        """
        
        art=[]
        for e in self:
            art+=e.artist()
        
        return art
        
    def flatten(self):
        """
        Returns a list of copies of the elements of this cell with References
        converted to Paths and Boundaries.
 
        :returns: A flattened list of copies of this cell's contents.

        A flattened version of this cell can be reconstructed with::
            flat_cell = Cell('FLAT')
            flat_cell.add(deep_cell.flatten())
        """        

        obj_list = []

        # Add all drawing elements
        for obj in self.objects:
            if isinstance(obj, Elements):
                obj_list.extend(obj.copy().obj)
            else:
                obj_list.append(obj.copy())

        # Add references
        for ref in self.references:
            obj_list.extend(ref.flatten())

        return obj_list       


class ReferenceBase:
    """
    Base class for cell references    
    """

    def __init__(self):
        pass

    def __len__(self):
        return len(self.ref_cell)

    def copy(self, suffix=None):
        return copy.copy(self)        

    def translate(self, displacement):
        """
        Translate this object by displacement

        :param displacement: the vector by which to move the cell
        :returns: self

        """
        self.origin+=np.array(displacement)
        return self
    
    def rotate(self, angle):
        """
        Rotate this object by angle
        
        :param angle: the angle by which to rotate the cell
        :returns: self
        """
        if self.rotation is None:
            self.rotation = 0

        self.rotation += angle
        
        if self.rotation == 0:
            self.rotation=None

        return self        

    def scale(self, k):
        """
        Scale this object by factor k
        
        :param k: the factor by which to scale the cell
        :returns: self
        """
        if self.magnification is None:
            self.magnification = 0

        self.magnification *= k
        
        if self.magnification == 1.0:
            self.magnificiation=None

        return self        

    def get_dependencies(self, include_elements=False):
        return [self.ref_cell]+self.ref_cell.get_dependencies(include_elements)
    

class CellReference(ReferenceBase):
    """
    Simple reference to an existing cell.

    :param ref_cell: The referenced cell.
    :param origin:  Position where the reference is inserted.
    :param rotation:  Angle of rotation of the reference (in *degrees*).
    :param magnification: Magnification factor for the reference.
    :param x_reflection:  If ``True``, the reference is reflected parallel to
        the x direction before being rotated.

    .. note::
        This is a direct equivalent to the SREF element found in the GDSII
        specification.    

    """

    def __init__(self, ref_cell, origin=(0, 0), rotation=None, magnification=None, x_reflection=False):
        ReferenceBase.__init__(self)
        self.origin = np.array(origin)
        self.ref_cell = ref_cell
        self.rotation = rotation
        self.magnification = magnification
        self.x_reflection = x_reflection
    
        #return CellReference(v, origin=self.origin, rotation=self.rotation, magnification=self.magnification, x_reflection=self.x_reflection)

    def __str__(self):
        if isinstance(self.ref_cell, Cell):
            name = self.ref_cell.name
        else:
            name = self.ref_cell
        return "CellReference (\"{0}\", at ({1[0]}, {1[1]}), rotation {2}, magnification {3}, reflection {4})".format(name, self.origin, self.rotation, self.magnification, self.x_reflection)

    def __repr__(self):
        if isinstance(self.ref_cell, Cell):
            name = self.ref_cell.name
        else:
            name = self.ref_cell
        return "CellReference(\"{0}\", ({1[0]}, {1[1]}), {2}, {3}, {4})".format(name, self.origin, self.rotation, self.magnification, self.x_reflection)

    def to_gds(self, multiplier, duplicates=[]):
        """
        Convert this object to a GDSII element.
        
        :param multiplier: A number that multiplies all dimensions written in
            the GDSII element.
        :param uniquify: If True saves the cell reference according to its
            uniquified name.
        
        :returns: The GDSII binary string that represents this object.
        """
        ref_cell = self.ref_cell
        name = ref_cell.unique_name if ref_cell.name in duplicates else ref_cell.name
            
        if len(name)%2 != 0:
            name = name + '\0'
        data = struct.pack('>4h', 4, 0x0A00, 4 + len(name), 0x1206) + name.encode('ascii')
        if not (self.rotation is None) or not (self.magnification is None) or self.x_reflection:
            word = 0
            values = b''
            if self.x_reflection:
                word += 0x8000
            if not (self.magnification is None):
                word += 0x0004
                values += struct.pack('>2h', 12, 0x1B05) + _eight_byte_real(self.magnification)
            if not (self.rotation is None):
                word += 0x0002
                values += struct.pack('>2h', 12, 0x1C05) + _eight_byte_real(self.rotation)
            data += struct.pack('>2hH', 6, 0x1A01, word) + values
        return data + struct.pack('>2h2l2h', 12, 0x1003, int(round(self.origin[0] * multiplier)), int(round(self.origin[1] * multiplier)), 4, 0x1100)
    
    def area(self, by_layer=False):
        """
        Calculate the total area of the referenced cell with the
        magnification factor included.
        
        :param by_layer: If ``True``, the return value is a dictionary with the areas of
            each individual layer.
        
        :returns: Area of this cell.
        """
        if self.magnification is None:
            return self.ref_cell.area(by_layer)
        else:
            if by_layer:
                factor = self.magnification * self.magnification
                cell_area = self.ref_cell.area(True)
                for kk in cell_area.iterkeys():
                    cell_area[kk] *= factor
                return cell_area
            else:
                return self.ref_cell.area() * self.magnification * self.magnification

    @property
    def bounding_box(self):
        """
        Returns the bounding box for this reference.
        
        Currently does not handle rotated references
        
        :returns: Bounding box of this cell [[x_min, y_min], [x_max, y_max]], or
            ``None`` if the cell is empty.
        """
        from . import utils

        
        if len(self.ref_cell)==0:
            return None
        
        mag=self.magnification if (self.magnification is not None) else 1.0
        
        bbox=self.ref_cell.bounding_box
        bbox *= mag
        
        if self.rotation:
            x0,y0=bbox[0]
            x1,y1=bbox[1]
            
            box=np.array([[x0,y0],
                             [x0,y1],
                             [x1, y1],
                             [x1, y0]])            
            
            box = utils.rotate(box, self.rotation)
                        
            bbox[0]=[min(box[:,0]), min(box[:,1])]
            bbox[1]=[max(box[:,0]), max(box[:,1])]        
        
        bbox[0] += self.origin
        bbox[1] += self.origin        
        
        return bbox

    def artist(self):
        """
        Return a list of matplotlib artists for drawing this object

        .. warning::
            
            Does not yet handle x_reflections correctly

        """


        xform=matplotlib.transforms.Affine2D()
        if self.x_reflection:
            xform.scale(1, -1)
            
        if self.magnification is not None:
            xform.scale(self.magnification, self.magnification)
        
        if self.rotation is not None:
            xform.rotate_deg(self.rotation)

        xform.translate(self.origin[0], self.origin[1])

        artists=self.ref_cell.artist()        
        for a in artists:
            a.set_transform(a.get_transform() + xform)

        return artists

    def flatten(self):
        """
        Return reference as a flattened list of elements.
        """
        mag = 1 if self.magnification is None else self.magnification
        rot = 0 if self.rotation is None else self.rotation                        

        elements = self.ref_cell.flatten()
        for e in elements:
            e.scale(mag).rotate(rot).translate(self.origin)
        
        return elements


class CellArray(ReferenceBase):
    """
    Multiple references to an existing cell in a grid arrangement.

    :param ref_cell: The referenced cell.
    :param cols: Number of columns in the array.
    :param rows: Number of rows in the array.
    :param spacing: The distance between copies within the array. This can be 
        either a 2-tuple or a pair of 2-tuples. The former (n,m)
        is interpreted as ((n,0), (0,m))
    :param origin: Position where the cell is inserted.
    :param rotation:  Angle of rotation of the reference (in *degrees*).
    :param magnification: Magnification factor for the reference.
    :param x_reflection: If ``True``, the reference is reflected parallel to
        the x direction before being rotated.

    .. note::
        This is a direct equivalent to the AREF element found in the GDSII
        specification.    
    """

    def __init__(self, ref_cell, cols, rows, spacing, origin=(0, 0), rotation=None, magnification=None, x_reflection=False):
        ReferenceBase.__init__(self)

        self.rows = int(rows)
        self.cols = int(cols)
        self.spacing = np.array(spacing)
        try:
            self.spacing[0][0]
        except IndexError:
            self.spacing = np.array([[self.spacing[0], 0], [0, self.spacing[1]]])

        self.origin = np.array(origin)
        self.ref_cell = ref_cell
        self.rotation = rotation
        self.magnification = magnification
        self.x_reflection = x_reflection
    
    def __str__(self):
        if isinstance(self.ref_cell, Cell):
            name = self.ref_cell.name
        else:
            name = self.ref_cell
        return "CellArray (\"{0}\", {1} x {2}, at ({3[0]}, {3[1]}), spacing {4[0]} x {4[1]}, rotation {5}, magnification {6}, reflection {7})".format(name, self.cols, self.rows, self.origin, self.spacing, self.rotation, self.magnification, self.x_reflection)

    def __repr__(self):
        if isinstance(self.ref_cell, Cell):
            name = self.ref_cell.name
        else:
            name = self.ref_cell
        return "CellArray(\"{0}\", {1}, {2}, ({4[0]}, {4[1]}), ({3[0]}, {3[1]}), {5}, {6}, {7})".format(name, self.cols, self.rows, self.origin, self.spacing, self.rotation, self.magnification, self.x_reflection)


    def copy(self, suffix=None):
        return copy.copy(self)
        
    def to_gds(self, multiplier, duplicates=[]):
        """
        Convert this object to a GDSII element.
        
        :param multiplier: A number that multiplies all dimensions written in
            the GDSII element.
        :param uniquify: If True saves the cell reference according to its
            uniquified name.
        
        :returns: The GDSII binary string that represents this object.
        """
        ref_cell = self.ref_cell
        name = ref_cell.unique_name if ref_cell.name in duplicates else ref_cell.name
            
        if len(name)%2 != 0:
            name = name + '\0'
        data = struct.pack('>4h', 4, 0x0B00, 4 + len(name), 0x1206) + name.encode('ascii')
        x2 = self.origin[0] + self.cols * self.spacing[0][0]
        y2 = self.origin[1] + self.cols * self.spacing[0][1]
        x3 = self.origin[0] + self.rows * self.spacing[1][0]
        y3 = self.origin[1] + self.rows * self.spacing[1][1]
        if not (self.rotation is None) or not (self.magnification is None) or self.x_reflection:
            word = 0
            values = b''
            if self.x_reflection:
                word += 0x8000
                y3 = 2 * self.origin[1] - y3
            if not (self.magnification is None):
                word += 0x0004
                values += struct.pack('>2h', 12, 0x1B05) + _eight_byte_real(self.magnification)
            if not (self.rotation is None):
                word += 0x0002
                sa = np.sin(self.rotation * np.pi / 180.0)
                ca = np.cos(self.rotation * np.pi / 180.0)
                tmp = (x2 - self.origin[0]) * ca - (y2 - self.origin[1]) * sa + self.origin[0]
                y2 = (x2 - self.origin[0]) * sa + (y2 - self.origin[1]) * ca + self.origin[1]
                x2 = tmp
                tmp = (x3 - self.origin[0]) * ca - (y3 - self.origin[1]) * sa + self.origin[0]
                y3 = (x3 - self.origin[0]) * sa + (y3 - self.origin[1]) * ca + self.origin[1]
                x3 = tmp
                values += struct.pack('>2h', 12, 0x1C05) + _eight_byte_real(self.rotation)
            data += struct.pack('>2hH', 6, 0x1A01, word) + values
        return data + struct.pack('>6h6l2h', 8, 0x1302, self.cols, self.rows, 28, 0x1003, int(round(self.origin[0] * multiplier)), int(round(self.origin[1] * multiplier)), int(round(x2 * multiplier)), int(round(y2 * multiplier)), int(round(x3 * multiplier)), int(round(y3 * multiplier)), 4, 0x1100)

    def area(self, by_layer=False):
        """
        Calculate the total area of the referenced cell with the
        magnification factor included.
        
        :param by_layer: If ``True``, the return value is a dictionary with the areas of
            each individual layer.
        
        :returns: Area of this cell.
        """
        if self.magnification is None:
            factor = self.cols * self.rows
        else:
            factor = self.cols * self.rows * self.magnification * self.magnification
        if by_layer:
            cell_area = self.ref_cell.area(True)
            for kk in cell_area.iterkeys():
                cell_area[kk] *= factor
            return cell_area
        else:
            return self.ref_cell.area() * factor

    @property
    def bounding_box(self):
        """
        Returns the bounding box for this reference.
        
        Currently does not handle rotated references
        
        :returns: Bounding box of this cell [[x_min, y_min], [x_max, y_max]], or
            ``None`` if the cell is empty.
        """
        from . import utils

        if len(self.ref_cell)==0:
            return None

        mag=self.magnification if (self.magnification is not None) else 1.0
        
        size=np.array((self.cols-1, self.rows-1)).dot(self.spacing)

        bbox=self.ref_cell.bounding_box
        bbox *= mag

        bbox[1] += size
        
        if self.rotation:
            x0,y0=bbox[0]
            x1,y1=bbox[1]
            
            box=np.array([[x0,y0],
                             [x0,y1],
                             [x1, y1],
                             [x1, y0]])            
            
            box = utils.rotate(box, self.rotation)
            
            bbox[0]=[min(box[:,0]), min(box[:,1])]
            bbox[1]=[max(box[:,0]), max(box[:,1])]
            
        
        bbox[0] += self.origin
        bbox[1] += self.origin        
        
        return bbox
        
    def artist(self):
        """
        Return a list of matplotlib artists for drawing this object
            
        """        

        mag=1.0
        if self.magnification is not None:
            mag=self.magnification
        
        artists=[]
        #Magnify the cell and then pattern                
        for i in range(self.cols):
            for j in range(self.rows):

                p=np.array([i,j]).dot(self.spacing)

                art=self.ref_cell.artist()        

                trans=matplotlib.transforms.Affine2D()
                trans.scale(mag)
                trans.translate(p[0], p[1])

                for a in art:
                    a.set_transform(a.get_transform() + trans)
                artists += art

        #Rotate and translate the patterned array        
        trans=matplotlib.transforms.Affine2D()
        if self.x_reflection:
            trans.scale(1, -1)
        
        if self.rotation is not None:
            trans.rotate_deg(self.rotation)

        if any(self.origin):            
            trans.translate(self.origin[0], self.origin[1])

        for a in artists:
            a.set_transform(a.get_transform() + trans)

        return artists

    def flatten(self):
        """
        Return reference as a flattened list of elements.
        """
        mag = 1 if self.magnification is None else self.magnification
        rot = 0 if self.rotation is None else self.rotation                        

        elements = []        
        sub_el = self.ref_cell.flatten()

        for i in range(self.cols):
            for j in range(self.rows):
                p=np.array([i,j]).dot(self.spacing)

                for e in sub_el:
                    elements.append(e.copy().scale(mag).translate(p))
            
        for e in elements:
            e.rotate(rot).translate(self.origin)
        
        return elements

def GdsImport(infile, rename={}, layers={}, datatypes={}, verbose=True, unit=1e-6):
    """
    Import a new Layout from a GDSII stream file.

    :param infile: GDSII stream file (or path) to be imported. It must be opened for
        reading in binary format.
    :param rename: Dictionary used to rename the imported cells. Keys and values must
        be strings.
    :param layers: Dictionary used to convert the layers in the imported cells. Keys
        and values must be integers.
    :param datatypes: Dictionary used to convert the datatypes in the imported cells.
        Keys and values must be integers.
    :param verbose: If False, import is silent. If True or 1, displays warnings
        about unsupported records. If 2 lists all records read.
    :param unit: Unit of the imported GDS file. The library precicions will be set
        accordingly.
    :returns: A :class:``Layout`` containing the imported gds file.
    
    Notes::

        Not all features from the GDSII specification are currently supported.
        A warning will be produced if any unsuported features are found in the
        imported file.

    Examples::

        layout = core.GdsImport('sample.gds')
        
    The import function returns a Layout containing only top level cells.
    """

    record_name = ('HEADER', 'BGNLIB', 'LIBNAME', 'UNITS', 'ENDLIB', 'BGNSTR', 'STRNAME', 'ENDSTR', 'BOUNDARY', 'PATH', 'SREF', 'AREF', 'TEXT', 'LAYER', 'DATATYPE', 'WIDTH', 'XY', 'ENDEL', 'SNAME', 'COLROW', 'TEXTNODE', 'NODE', 'TEXTTYPE', 'PRESENTATION', 'SPACING', 'STRING', 'STRANS', 'MAG', 'ANGLE', 'UINTEGER', 'USTRING', 'REFLIBS', 'FONTS', 'PATHTYPE', 'GENERATIONS', 'ATTRTABLE', 'STYPTABLE', 'STRTYPE', 'ELFLAGS', 'ELKEY', 'LINKTYPE', 'LINKKEYS', 'NODETYPE', 'PROPATTR', 'PROPVALUE', 'BOX', 'BOXTYPE', 'PLEX', 'BGNEXTN', 'ENDTEXTN', 'TAPENUM', 'TAPECODE', 'STRCLASS', 'RESERVED', 'FORMAT', 'MASK', 'ENDMASKS', 'LIBDIRSIZE', 'SRFNAME', 'LIBSECUR')

    if infile.__class__ == ''.__class__:
        infile = open(infile, 'rb')
        close = True
    else:
        close = False

    cell_dict = {}
    emitted_warnings = []
    rec_typ, data =  _read_record(infile)
    kwargs = {}
    create_element = None
    i = -1
    while rec_typ is not None:
        i+=1
        rname = record_name[rec_typ]
        if verbose==2:       
            print(i, ':', rname, end=' ')

        # Library Head/Tail
        if 'HEADER' == rname:
            if verbose==2:
                print(data[0], end=' ')
        elif 'BGNLIB' == rname:
            kwargs['created'] = datetime.datetime(*data.tolist()[:6])
            kwargs['modified'] = datetime.datetime(*data.tolist()[6:])
            if verbose==2:
                print("created %d/%d/%d,%d:%d:%d modified %d/%d/%d,%d:%d:%d" % tuple(data.tolist()), end=' ')
        elif 'LIBNAME' == rname:
            kwargs['name'] = data.decode('ascii')
            if verbose==2:
                print(kwargs['name'], end=' ')
        elif 'UNITS' == rname:
            factor = data[0]
            kwargs['precision'] = unit * factor
            kwargs['unit'] = unit
            if verbose==2:
                print(kwargs['unit'], end=' ')
            layout = Layout(**kwargs)
            kwargs={}
        elif 'ENDLIB' == rname:
            if verbose==2:
                print()
            break

        # Cell Creation
        elif 'BGNSTR' == rname:
            kwargs['created'] = datetime.datetime(*data.tolist()[:6])
            kwargs['modified'] = datetime.datetime(*data.tolist()[6:])
            if verbose==2:
                print("created %d/%d/%d,%d:%d:%d modified %d/%d/%d,%d:%d:%d" % tuple(data.tolist()), end=' ')
        elif 'STRNAME' == rname:
            if not str is bytes:
                if data[-1] == 0:
                    data = data[:-1].decode('ascii')
                else:
                    data = data.decode('ascii')
            name = rename.get(data, data)
            cell = Cell(name, **kwargs)
            kwargs={}
            cell_dict[name] = cell
            if verbose==2:
                print(name, end=' ')
        elif 'ENDSTR' == rname:
            cell = None

        # Element Creation
        elif 'BOUNDARY' == rname:
            create_element =  _create_polygon
        elif 'PATH' == rname:
            create_element =  _create_path
        elif 'SREF' == rname:
            create_element =  _create_reference
        elif 'AREF' == rname:
            create_element =  _create_array
        elif 'TEXT' == rname:
            create_element =  _create_text
        elif 'ENDEL' == rname:
            if create_element is not None:
                cell.add(create_element(**kwargs))
            create_element = None
            kwargs = {}

        # Element Data and Modifiers
        elif 'LAYER' == rname:
            kwargs['layer'] = layers.get(data[0], data[0])
            if verbose==2:
                print(kwargs['layer'], end=' ')
        elif 'DATATYPE' == rname or 'TEXTTYPE' == rname:
            kwargs['datatype'] = datatypes.get(data[0], data[0])
            if verbose==2:
                print(kwargs['datatype'], end=' ')
        elif 'XY'  == rname:
            if 'xy' not in kwargs:
                kwargs['xy'] = factor * data
            else:
                kwargs['xy'] = np.hstack((kwargs['xy'], factor * data))
            if verbose==2:
                print(kwargs['xy'], end=' ')
        elif 'WIDTH' == rname:
            kwargs['width'] = factor * abs(data[0])
            if data[0] < 0 and rname not in emitted_warnings:
                warnings.warn("[GDSPY] Paths with absolute width value are not supported. Scaling these paths will also scale their width.", stacklevel=2)
                emitted_warnings.append(rname)
        elif 'PATHTYPE' == rname:
            kwargs['pathtype'] = data[0]
            if verbose==2:
                print(kwargs['pathtype'], end=' ')
        elif 'SNAME' == rname:
            if not str is bytes:
                if data[-1] == 0:
                    data = data[:-1].decode('ascii')
                else:
                    data = data.decode('ascii')
            kwargs['ref_cell'] = rename.get(data, data)
            if verbose==2:
                print(',', kwargs['ref_cell'], end=' ')
        elif 'COLROW' == rname:
            kwargs['cols'] = data[0]
            kwargs['rows'] = data[1]
        elif 'STRANS' == rname:
            kwargs['x_reflection'] = ((long(data[0]) & 0x8000) > 0)
            if verbose==2:
                print(kwargs['x_reflection'], end=' ')
        elif 'MAG' == rname:
            kwargs['magnification'] = data[0]
            if verbose==2:
                print(kwargs['magnification'], end=' ')
        elif 'ANGLE' == rname:
            kwargs['rotation'] = data[0]
            if verbose==2:
                print(kwargs['rotation'], end=' ')
        elif 'PRESENTATION' == rname:
            kwargs['anchor'] = ['tl', 'tc', 'tr', None, 'cl', 'cc', 'cr', None, 'bl', 'bc', 'br'][data[0]]
            if verbose==2:
                print(kwargs['anchor'], end=' ')
        elif 'STRING' == rname:
            if not str is bytes:
                if data[-1] == 0:
                    kwargs['text'] = data[:-1].decode('ascii')
                else:
                    kwargs['text'] = data.decode('ascii')
            else:
                kwargs['text'] = data
            if verbose==2:
                print(kwargs['text'], end=' ')

        # Not supported
        elif verbose and rname not in emitted_warnings:
            warnings.warn("Record type {0} not supported by GdsImport.".format(rname), stacklevel=2)
            emitted_warnings.append(rname)

        rec_typ, data =  _read_record(infile)
        if verbose==2: print('')

    if close:
        infile.close()
   
    # Make connections from cell references to all cells objects
    # We cannot add the cells to the library yet, since we cannot assert that all its
    # dependencies were resolved.
    for c in cell_dict.values():
        for r in c.references:
            r.ref_cell = cell_dict[r.ref_cell]

    # Add all the cells to the library.
    warnings.filterwarnings('ignore')  # suppress duplicate cell warning
    for c in cell_dict.values():
        if c not in layout:
            layout.add(c)
    warnings.filterwarnings('default')

    # Remove non-top level cells             
    for k in [j for j in layout.keys() if j not in [i.name for i in layout.top_level()]]:
        layout.pop(k)
    
    return layout


def DxfImport(fname, scale=1.0):
    """
    Import artwork from a DXF File.
    
    :param fname: the DXF file
    :param scale: the scale factor for the drawing dimensions    
    
    Currently only supports POLYLINE and LINE entities which are returned as
    a list. Closed POLYLINES are interpreted as Boundaries, LINES and open
    POLYLINES are interpreted as Paths. DxfImport will attempt to cast layer
    name strings to integers. If it fails the default layer will be used.
    """

    dxf = dxfgrabber.readfile(fname)

    art = []    
    for e in dxf.entities:
        if isinstance(e, dxfgrabber.entities.LWPolyline):
            art.append(_parse_POLYLINE(e, scale))
        elif isinstance(e, dxfgrabber.entities.Line):
            art.append(_parse_LINE(e, scale))
        else:        
            print('Ignoring unknown entity type %s in DxfImport.' % type(e))

    return art

def _parse_POLYLINE(pline, scale):
    """
    Convert a DXF Polyline to a GDS Path or Boundary    
    """
    try:
        layer = int(pline.layer)
    except ValueError:
        layer = None
    if layer == 0:
        layer = None;

    if pline.const_width != 0:
        width = pline.const_width * scale
    else:            
        width = np.array(pline.width).mean() * scale
    
    if width == 0:
        width = 1.0
        
    points = np.array(pline.points) * scale

    d = np.sqrt(((points[0]-points[-1])**2).sum())

    if d < 1e-10:
        return Boundary(points, layer=layer)
    else:
        return Path(points, width=width, layer=layer)

def _parse_LINE(line, scale):
    """
    Convert a DXF Line to a GDS Path
    """    
    try:
        layer = int(line.layer)
    except ValueError:
        layer = None
    if layer == 0:
        layer = None;

    width = line.thickness
    if width == 0:
        width = 1.0
        
    points = np.array((line.start, line.end)) * scale
    points = points[:,:2]
    return Path(points, width=width, layer=layer)
    
    
def _read_record(stream):
    """
    Read a complete record from a GDSII stream file.

    Parameters
    ----------
    stream : file
        GDSII stream file to be imported.

    Returns
    -------
    out : 2-tuple
        Record type and data (as a np.array)
    """
    header = stream.read(4)
    if len(header) < 4:
        return None, None
    size, rec_type = struct.unpack('>HH', header)
    data_type = (rec_type & 0x00ff)
    rec_type = rec_type // 256
    data = None
    if size > 4:
        if data_type == 0x01:
            data = np.array(struct.unpack('>{0}H'.format((size - 4) // 2), stream.read(size - 4)), dtype='uint')
        elif data_type == 0x02:
            data = np.array(struct.unpack('>{0}h'.format((size - 4) // 2), stream.read(size - 4)), dtype=int)
        elif data_type == 0x03:
            data = np.array(struct.unpack('>{0}l'.format((size - 4) // 4), stream.read(size - 4)), dtype=int)
        elif data_type == 0x05:
            data = np.array([_eight_byte_real_to_float(stream.read(8)) for _ in range((size - 4) // 8)])
        else:
            data = stream.read(size - 4)
            if data[-1] == '\0':
                data = data[:-1]
    return [rec_type, data]

def _clean_args(cls, kwargs):
    """
    Remove arguments with unknown names from kwargs 
    """
    
    arg_names = inspect.getargspec(cls.__init__).args
    return {k: kwargs[k] for k in kwargs if k in arg_names}

def _create_polygon(**kwargs):
    xy = kwargs.pop('xy')    
    kwargs['points'] = xy.reshape((xy.size // 2, 2))
    kwargs = _clean_args(Boundary, kwargs)
    return Boundary(**kwargs)

def _create_path(**kwargs):
    xy = kwargs.pop('xy')
    kwargs['points'] = xy.reshape((xy.size // 2, 2))
    kwargs = _clean_args(Path, kwargs)    
    return Path(**kwargs)

def _create_text(xy, **kwargs):
    kwargs['position'] = xy
    kwargs = _clean_args(Text, kwargs)
    return Text(**kwargs)

def _create_reference(**kwargs):
    kwargs['origin'] = kwargs.pop('xy')
    kwargs = _clean_args(CellReference, kwargs)
    return CellReference(**kwargs)

def _create_array(**kwargs):
    xy = kwargs.pop('xy')
    kwargs['origin'] = xy[0:2]
    if 'x_reflection' in kwargs:
        if 'rotation' in kwargs:
            sa = -np.sin(kwargs['rotation'] * np.pi / 180.0)
            ca = np.cos(kwargs['rotation'] * np.pi / 180.0)
            x2 = (xy[2] - xy[0]) * ca - (xy[3] - xy[1]) * sa + xy[0]
            y3 = (xy[4] - xy[0]) * sa + (xy[5] - xy[1]) * ca + xy[1]
        else:
            x2 = xy[2]
            y3 = xy[5]
        if kwargs['x_reflection']:
            y3 = 2 * xy[1] - y3
        kwargs['spacing'] = ((x2 - xy[0]) / kwargs['cols'], (y3 - xy[1]) / kwargs['rows'])
    else:
        kwargs['spacing'] = ((xy[2] - xy[0]) / kwargs['cols'], (xy[5] - xy[1]) / kwargs['rows'])

    kwargs = _clean_args(CellArray, kwargs)
    return CellArray(**kwargs)

def _compact_id(obj):
    """
    Return the id of the object as an ascii string.
    
    This is guaranteed to be unique, and uses only characters that are permitted
    in valid GDSII names.
    """

    i=bin(id(obj))[2:]
    chars=string.ascii_uppercase+string.ascii_lowercase+string.digits+'?$'

    out=''
    while len(i):
        s=int(i[-6:], base=2)
        out+=chars[s]
        i=i[:-6]
        
    return out[::-1]

def _eight_byte_real(value):
    """
    Convert a number into the GDSII 8 byte real format.
    
    Parameters
    ----------
    value : number
        The number to be converted.
    
    Returns
    -------
    out : string
        The GDSII binary string that represents ``value``.
    """
    byte1 = 0
    byte2 = 0
    short3 = 0
    long4 = 0
    if value != 0:
        if value < 0:
            byte1 = 0x80
            value = -value
        exponent = int(np.floor(np.log2(value) * 0.25))
        mantissa = long(value * 16**(14 - exponent))
        while mantissa >= 72057594037927936:
            exponent += 1
            mantissa = long(value * 16**(14 - exponent))
        byte1 += exponent + 64
        byte2 = (mantissa // 281474976710656)
        short3 = (mantissa % 281474976710656) // 4294967296
        long4 = mantissa % 4294967296
    return struct.pack(">HHL", byte1 * 256 + byte2, short3, long4)


def _eight_byte_real_to_float(value):
    """
    Convert a number from GDSII 8 byte real format to float.

    Parameters
    ----------
    value : string
        The GDSII binary string representation of the number.

    Returns
    -------
    out : float
        The number represented by ``value``.
    """
    short1, short2, long3 = struct.unpack('>HHL', value)
    exponent = (short1 & 0x7f00) // 256
    mantissa = (((short1 & 0x00ff) * 65536 + short2) * 4294967296 + long3) / 72057594037927936.0
    return (-1 if (short1 & 0x8000) else 1) * mantissa * 16 ** (exponent - 64)
