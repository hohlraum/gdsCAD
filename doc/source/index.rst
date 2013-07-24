**********************************
Welcome to gdsCAD's documentation!
**********************************

Introduction
============

gdsCAD is a simple, but powerful, Python package for creating, reading, and
manipulating GDSII layout files. It's suitable for scripting and interactive
use. It excels particularly in generating designs with multiple incrementally
adjusted objects. gdsCAD uses matplotlib to visualize everything from individual
geometry primitives to the entire layout.

Gallery
=======

.. image:: /Gallery.png
    :target: examples.html


A Simple Example
================
.. currentmodule:: gdsCAD.core

Here is a simple example that shows the creation of some text with alignment
features. It involves the creation of drawing geometry, :class:`Cell`\ s and 
a :class:`Layout`\ . The result is saved as a GDSII file, and also displayed
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


.. plot::
    
    import os.path 
    from gdsCAD import *

    # Create some things to draw:
    amarks = templates.AlignmentMarks(['A', 'C'], [1,2])
    text = shapes.Label('Hello\nworld!', 200, (0, 0))
    box = shapes.Box((-500, -400), (1500, 400), 8, layer=2)

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


Contents
========

.. toctree::
    :maxdepth: 2

    userguide.rst
    examples.rst
    api/api.rst
    versions.rst

Installation
============

1. Start by getting a working version of `Python <http://www.python.org/getit/>`_.
    For Windows users this is most easily done by installing
    `Python (x,y) <https://code.google.com/p/pythonxy/>`_\ . 

#. gdsCAD has the following mandatory dependency (it's installed as standard by
    Python(x,y)):

    * `numpy <http://www.numpy.org/.>`_

    For visualizing objects these packages are also required: 

    * `matplotlib <http://matplotlib.org/index.html>`_
    * `shapely <https://pypi.python.org/pypi/Shapely>`_
    * `descartes <https://pypi.python.org/pypi/descartes>`_

#. Download gdsCAD from `PyPi <https://pypi.python.org/pypi/gdsCAD>`_

#. Unzip the package and run ``python setup.py install`` from the command line.

#. Start Python and type ``import gdsCAD``. If you don't recieve any import
   warnings then you're ready to go.

Getting Started
===============
Once you have ``gdsCAD`` installed, start by reading the :doc:`userguide`
and reviewing the :doc:`examples`. More advanced use will benefit from referring
to the :doc:`api/api`. 



License
=======
gdsCAD is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

