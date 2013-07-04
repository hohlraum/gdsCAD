************
User's Guide
************

Introduction
############



Relationship to gdspy
#####################
gdsCAD is derived from gdspy by Lucas Heitzmann Gabrielli


A minimal script
################

Here is a minimal working script, that creates a box and inserts it into a cell
which is then added to a layout. The layout is saved as a GDSII stream in
the file 'output.gds'. It is also sent to the viewer::

    from gdsCAD import *
    
    # Create a box on layer 2 centered at the origin
    box=shapes.Box(2, (-10,10), (10,10))

    # Create a top level cell and add the box
    cell=core.Cell('TOP')
    cell.add(box)

    # Create a layout and add the cell
    layout = core.Layout('LIBRARY')
    layout.add(cell)

    layout.save('output.gds')
    layout.show()
    

Primitive Drawing Elements
##########################




Introduction to Shapes
######################




Cells
#####



Cell References
###############




Templates
#########




