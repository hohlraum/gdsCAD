
***************************************
gdsCAD -- Simple GDSII design in Python
***************************************

gdsCAD is a simple, but powerful, Python package for creating, reading, and
manipulating GDSII layout files. It's suitable for scripting and interactive
use. It excels particularly in generating designs with multiple incrementally
adjusted objects. gdsCAD uses matplotlib to visualize everything from individual
geometry primitives to the entire layout.

Documentation
=============

Complete documentation can be found at:
    http://pythonhosted.org/gdsCAD/#


Download
========

The package can be downloaded for installation via easy_install at
    https://pypi.python.org/pypi/gdsCAD


Gallery
=======
.. image:: http://pythonhosted.org/gdsCAD/_images/Gallery.png


A Simple Example
================

Here is a simple example that shows the creation of some text with alignment
features. It involves the creation of drawing geometry, ``Cell`` and 
a ``Layout`` . The result is saved as a GDSII file, and also displayed
to the screen:: 

    import os.path 
    from gdsCAD import *

    # Create some things to draw:
    amarks = templates.AlignmentMarks(('A', 'C'), (1,2))
    text = shapes.Label('Hello\nworld!', 200, (0, 0))
    box = shapes.Box((-500, -400), (1500, 400), 10, layer=2)

    # Create a Cell to hold the objects
    cell = core.Cell('EXAMPLE')
    cell.add([text, box])
    cell.add(amarks, origin=(-200, 0))
    cell.add(amarks, origin=(1200, 0))

    # Create two copies of the Cell
    top = core.Cell('TOP')
    cell_array = core.CellArray(cell, 1, 2, (0, 850))
    top.add(cell_array)

    # Add the copied cell to a Layout and save
    layout = core.Layout('LIBRARY')
    layout.add(top)
    layout.save('output.gds')

    layout.show()

Recent Changes
==============
v0.3.7 (14.02.14)
    * More colors for layer numbers greater than six (Matthias Blaicher)
v0.3.6 (12.12.13) **bugfix**
    * Fixed installation to include missing resource files
v0.3.5 (11.12.13 PM) **bugfix**
    * Introduced automatic version numbering
    * git_version module is now included in distribution (Thanks Matthias)
v0.3.2 (11.12.13)
    * CellArray spacing can now be non-orthogonal
    * Block will now take cell spacing information from the attribute cell.spacing
v0.3.1 (06.12.13)
    * Added support for `Hershey Fonts <http://en.wikipedia.org/wiki/Hershey_font>`_.
    * Thanks to Matthias Blaicher.

    
