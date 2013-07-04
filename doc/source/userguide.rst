************
User's Guide
************

Introduction
============



Relationship to gdspy
=====================
gdsCAD is derived from gdspy by Lucas Heitzmann Gabrielli


A minimal script
================

Here is a minimal working script that creates a box and inserts it into a cell
which is then added to a layout. The layout is saved as a GDSII stream in
the file 'output.gds'. It is also sent to the viewer::

    from gdsCAD import *

    # Create a Cell and add the box
    cell=core.Cell('TOP')

    # Create three boxes on layer 2 of different sizes centered at
    # the origin and add them to the cell.
    for l in (3,6,10):
        box=shapes.Box(2, (-l,-l), (l,l), width=0.2)
        cell.add(box)

    # Create a layout and add the cell
    layout = core.Layout('LIBRARY')
    layout.add(cell)

    # Save the layout and then display it on screen
    layout.save('output.gds')
    layout.show()
    

.. plot::

    from gdsCAD import *

    # Create a Cell and add the box
    cell=core.Cell('TOP')

    # Create three boxes on layer 2 of different sizes centered at
    # the origin and add them to the cell.
    for l in (3,6,10):
        box=shapes.Box(2, (-l,-l), (l,l), width=0.2)
        cell.add(box)

    # Create a layout and add the cell
    layout = core.Layout('LIBRARY')
    layout.add(cell)

    # Save the layout and then display it on screen
    layout.save('output.gds')
    layout.show()
    

.. currentmodule:: gdsCAD.core

Primitive Objects for Drawing Art
=================================

There are only two basic objects for drawing art in a GDSII file:
:class:`Boundary` and :class:`Path`. The object :class:`Text` creates annotations
that can be reviewed in design viewers, but will not print. All the other 
primitive classes (:class:`Cell`, :class:`Elements`, :class:`Layout`, etc...)
are for managing and organizing objects based on ``Boundary`` and ``Path``.

:class:`Boundary`
-----------------
:class:`Boundary` objects are filled, closed polygons. They correspond to the
Boundary object defined in the GDSII specification. ``Boundaries`` are created by
specifying a sequence of points that define the boundary outline, they are
closed automatically.

The following code will create an L-shaped polygon::

    from gdsCAD import *
    
    points=[(0,0), (20,0), (20,10), (5,10), (5,20), (0,20)]
    bdy = core.Boundary(1, points)
    bdy.show()

.. plot::

    from gdsCAD import *
    
    points=[(0,0), (20,0), (20,10), (5,10), (5,20), (0,20)]
    bdy = core.Boundary(1, points)
    bdy.show()

``Boundaries`` can be copied, and subjected to the geometric transformations
``rotate``, ``reflect``, ``scale``, and ``translate``::

    bdy2 = bdy.copy()
    bdy2.scale(2)
    bdy2.rotate(45)
    bdy2.translate((20,20))
    
    # Change the layer so that we can see it more easily
    bdy2.layer=2
    bdy2.show()

.. plot::

    from gdsCAD import *
    
    points=[(0,0), (20,0), (20,10), (5,10), (5,20), (0,20)]
    bdy = core.Boundary(1, points)
    bdy.show()

    bdy2 = bdy.copy()
    bdy2.scale(2)
    bdy2.rotate(45)
    bdy2.translate((20,20))
    
    # Change the layer so that we can see it more easily
    bdy2.layer=2
    bdy2.show()

``Boundaries`` cannot be self intersecting, or have internal voids. Such voids
can be created by using "keyhole" type geometries, or through the use of XOR 
postprocessing.


:class:`Path`
-------------
In contrast to a :class:`Boundary` which is closed and filled, a :class:`Path`
is unfilled and may be open. ``Paths`` have a finite width given by third
parameter::

    points=[(-10,0), (0,20), (10,0)]
    pth = core.Path(1, points, 0.5)
    pth.show()

.. plot::

    from gdsCAD import *
    
    points=[(-10,0), (0,20), (10,0)]
    pth = core.Path(1, points, 0.5)
    pth.show()

``Paths`` can have different endpoint styles specified by the *pathtype* argument,
however because of how they are implement ``Paths`` always are drawn with rounded
endcaps. Thus designs that depend critically on the endpoint geometry should be
checked in an external GDSII viewer.
 
``Paths`` cannot be self intersecting.


.. currentmodule:: gdsCAD.shapes

Derived Objects for Drawing Art
===============================
gdsCAD provides several higher order classes for creating common objects. These
are contained in the module ``gdsCAD.shape`` and are derived from the base
classes :class:`core.Boundary` and :class:`core.Path`.

:class:`Rectangle` and :class:`Box`
-----------------------------------
These two classes create filled and unfilled rectangles respectively. The are
defined by the positions of two opposite corners, and in the case of ``Box``,
the width of the path::

    rect=shapes.Rectangle(1, (-10,-10), (0,0))
    box=shapes.Box(2, (0,0), (10,10), 1.0)

.. plot::

    from gdsCAD import *
    
    rect=shapes.Rectangle(1, (-10,-10), (0,0))
    rect.show()

    box=shapes.Box(2, (0,0), (10,10), 1.0)
    box.show()

Again, they can transformed through simple geometrical transformations::

    rect.rotate(45, center=(-5,-5))
    box.scale(3).translate((-14,-14))


.. plot::

    from gdsCAD import *
    
    rect=shapes.Rectangle(1, (-10,-10), (0,0))
    box=shapes.Box(2, (0,0), (10,10), 1.0)

    rect.rotate(45, center=(-5,-5))
    box.scale(3).translate((-14,-14))

    rect.show()
    box.show()


:class:`Disk` and :class:`Circle`
--------------------------------
These two classes create filled and unfilled circles. They are defined by their
center position and radius::

    disk=shapes.Disk(1, (-5,-5), 5)
    circ=shapes.Circle(2, (10,10), 10, 0.5)


.. plot::

    from gdsCAD import *
    
    disk=shapes.Disk(1, (-5,-5), 5)
    disk.show()

    circ=shapes.Circle(2, (10,10), 10, 0.5)
    circ.show()

It's possible to draw a disks with a hollow inner radius, this is constructed
using a keyhole geometry so it does not defy the restriction that ``Boundaries``
cannot have internal voids::

    disk=shapes.Disk(1, (0,0), 5, inner_radius=2.5)

.. plot::

    from gdsCAD import *
    
    disk=shapes.Disk(1, (0,0), 5, inner_radius=2.5)
    disk.show()

It is possible to draw only segments of both ``Circles`` and ``Disks`` by
specifying an initial and final angle::

    disk=shapes.Disk(1, (-5,-5), 5, initial_angle=90, final_angle=360)
    circ=shapes.Circle(2, (10,10), 10, 0.5, initial_angle=270, final_angle=180)

.. plot::

    from gdsCAD import *
    
    disk=shapes.Disk(1, (-5,-5), 5, initial_angle=90, final_angle=360)
    disk.show()

    circ=shapes.Circle(2, (10,10), 10, 0.5, initial_angle=180, final_angle=270)
    circ.show()



Making Annotations
==================
.. currentmodule:: gdsCAD

There are two ways of adding text to a design: :class:`core.Text` and :class:`shapes.Label`

.. currentmodule:: gdsCAD.core
Non-printing :class:`Text` 
--------------------------
The class :class:`Text` permits notes and annotations to be added to a design.
These will not be printed on the mask are intended only for clarification during
the design process. Since they are not true drawing geometry they do not scale
in a physical manner with other drawing geometry.

.. plot::

    from gdsCAD import *
    
    box=shapes.Rectangle(1, (-5,-5), (5,5))
    box.show()

    top=core.Text(2, 'TOP', (0, 4))
    bottom=core.Text(2, 'BOTTOM', (0,-4))
    top.show()
    bottom.show()




Organizing Art
==============
:class:`Cell`
-------------
:class:`Cell`\ s are collections of multiple geometry elements, and references
to other ``Cells``. The contents of a ``Cell`` can have different datatypes and
layers, so they are a good way of grouping together the many elements that make up
a device.




:class:`Layout`
---------------

The most basic gdsCAD object is the :class:`Layout`, which is essentially the 
GDS stream that you will send to the mask shop. A ``Layout`` contains many
:class:`Cell`\ s which can in turn contain drawing elements or reference to other
``Cells``. Those ``Cells`` in a ``Layout`` which are not referred to by any other ``Cell`` are
known as **top level** ``Cells``.

Spatial dimensions of objects in gdsCAD have no units, and the size of objects
is determined by the units specified in the ``Layout``. Two parameters govern
how dimensions are interpreted: units and precision, these can both be adjusted 
when the library is created. The default is for units to be in um and precision 
to be in nm. With this unit scheme a 10x10 box would have dimensions when printed 
of 10um x 10um, and the smallest possible box would be 1nm x 1nm (although that's
very unlikely to print). In practice it's best to use the defaults and measure 
everything in um.

``Layout`` is subclassed from the Python dict, so the ``Cells`` within a
 ``Layout`` can be accessed by their name like a Python dict, and it is
possible to iterate over the names of the cells::

    from gdsCAD import *

    A=core.Cell('CELL A')
    B=core.Cell('CELL B')  

    l=core.Layout('layout')
    l.add(A)
    l.add(B)

    # Prints information on cell A
    print l['CELL A']

    # Prints the names of all cells
    for name in l:
        print name

A ``Layout`` can be saved to a binary GDSII stream by using the method
``save(fname)``. It can be displayed using the method ``show()``.








Common Features
---------------
The following methods can be found in all classes

* ``rotate()``, ``translate()``, ``reflect()``, ``scale()``: transformation
  operations on the object which act in place (not present for ``Cell``)


* ``show()``: display the object in a matplotlib figure

* ``bounding_box``: return the rectangular extents of the object 
``[[min_x, min_y], [max_x, max_y]]``

*``copy()``: create a shallow copy of the object

*``deepcopy()``: create a deep copy of the object which also makes new
copies of the objects to which it refers

*``artist()``: return the matplotlib artist that will draw the object 

Drawing elements contain:
* layer

* datatype


More on Transformations
=======================



Introduction to Shapes
######################




Cells
#####



Cell References
###############




Templates
#########




