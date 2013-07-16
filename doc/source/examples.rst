********
Examples
********

This is a gallery of example structures built in gdsCAD. Click on the 
*Source code* link to see the code that generated the figure.

A Microfluidic Channel
----------------------

.. plot::

    import numpy as np
    from gdsCAD import *

    R = 50      # reservoir radius
    w = 10      # channel widths
    ang = 45    # Y angle
    l = 200     # channel length

    # Position of the upper pool
    p1 = 0.5 * l * np.array([-np.cos(ang), np.sin(ang)])

    # Create the three pools
    pool1 = shapes.Disk(p1, R)
    pool2 = utils.reflect(pool1, 'x')
    pool3 = shapes.Disk((l, 0), R)

    # Create the two channels
    chan1 = core.Path([p1, (0,0), (l, 0)])
    chan2 = core.Path([utils.reflect(p1, 'x'), (0,0)])

    # Create the cell and add the different objects
    u_fluid = core.Cell('MIXER')
    u_fluid.add([pool1, pool2, pool3, chan1, chan2])
    u_fluid.show()

A Cloverleaf Arrangement
------------------------

.. plot::

    import numpy as np
    from gdsCAD import *

    R = 50                 # outer diameter
    l = np.array((20,20))  # inner square

    angles = np.linspace(0, np.pi/2, 50)
    pts = np.vstack((np.cos(angles), np.sin(angles))).T * R
    pts = np.vstack(((0,0), pts))

    quad = core.Boundary(pts).translate(0.50 * l)
    
    top = core.Cell('TOP')

    for ang in [0, 90, 180, 270]:
        top.add(utils.rotate(quad, ang))
    top.add(shapes.Rectangle(-l, l))

    top.show()


A Hallbar
---------

.. plot::
    
    from gdsCAD import *
    from gdsCAD.shapes import Rectangle
    from gdsCAD.core import Path, Cell

    hbar = Cell('HALL_BAR')

    # Build the channel
    hbar.add(Rectangle((-50, -10), (50,10)))
    hbar.add(Rectangle((-50, -10), (-48, 10), layer=2))
    hbar.add(Rectangle((50, -10), (48, 10), layer=2))

    # Build a pad
    pad = Cell('PAD')
    pad.add(Rectangle((-5,-5), (5,5)))
    pad.add(Rectangle((-2,-2), (2,2), layer=2))

    # Copy the pads
    for i in range(-2,3):
        x = -10 * i
        ys = 20 + 12 * (i%2)

        for y in (ys, -ys):
            # Add a connecting trace
            hbar.add(Path(((x,y), (x,0)), width=2))
            # Add a pad
            hbar.add(pad, (x,y))

    hbar.show()    

A Serpentine Heater
-------------------

.. plot::

    import numpy as np
    from gdsCAD import *

    width = 2    # wire width
    height = 40  # device width
    spacing = 20 # spacing between windings
    N = 5        # number of windings

    heater = core.Cell('HEATER')

    unit = np.array([[0,0], [0, height], [spacing/2., height], [spacing/2., 0]])    

    pts=unit
    for i in range(1,N):
        next_unit = unit + i * np.array([spacing, 0])
        pts = np.vstack((pts, next_unit))

    pts=np.vstack(([0,-10], pts, [spacing * N, 0], [spacing * N, height+10]))

    trace=core.Path(pts, width=2)
    heater.add(trace)

    pad = core.Cell('PAD')
    pad.add(shapes.Rectangle((-5,-5), (5,5)))
    pad.add(shapes.Rectangle((-2,-2), (2,2), layer=2))

    heater.add(pad, origin= (0, -10))
    heater.add(pad, origin=(spacing * N, height+10))

    heater.show()    


An Array of Crossbars
---------------------

.. plot::

    import numpy as np
    from gdsCAD import *

    length = 50
    spacing = np.array([75, 75])

    def xbar(w1, w2):
        cell = core.Cell('XBAR')
        xstrip = shapes.Rectangle((0,0), (length, w1))        
        ystrip = shapes.Rectangle((0,0), (w2, length), layer=2)

        N = int(length/(2*w1))
        for i in range(N):
            d = (0, i*w1*2)
            cell.add(utils.translate(xstrip, d))

        N = int(length/(2*w2))
        for i in range(N):
            d = (i*w2*2, 0)
            cell.add(utils.translate(ystrip, d))               

        return cell

    grid = core.Cell('GRID')
    w_vals = [1, 2, 3, 5]

    for (i, bottom) in enumerate(w_vals):
        for (j, top) in enumerate(w_vals):
            grid.add(xbar(bottom, top), origin = np.array([i,j])*spacing)

    grid.show()



Several Serpentine Designs
--------------------------

.. plot::

    import numpy as np
    from gdsCAD import *

    width = 2    # wire width
    height = 40  # device width
    width = 150  # device length (approx.)

    def Heater(spacing):
        heater = core.Cell('HEATER')
    
        unit = np.array([[0,0], [0, height], [spacing/2., height], [spacing/2., 0]])    

        N = int(np.floor(width/spacing))
        pts=unit
        for i in range(1,N):
            next_unit = unit + i * np.array([spacing, 0])
            pts = np.vstack((pts, next_unit))
    
        pts=np.vstack(([0,-10], pts, [spacing * N, 0], [spacing * N, height+10]))
    
        trace=core.Path(pts, width=2)
        heater.add(trace)
    
        pad = core.Cell('PAD')
        pad.add(shapes.Rectangle((-5,-5), (5,5)))
        pad.add(shapes.Rectangle((-2,-2), (2,2), layer=2))
    
        heater.add(pad, origin= (0, -10))
        heater.add(pad, origin=(spacing * N, height+10))

        return heater

    top = core.Cell('TOP')
    yPos = 0
    for sp in [5, 10, 20, 30, 50]:
        htr = Heater(sp)
        bb = htr.bounding_box
        h = bb[1,1] - bb[0,1]
        top.add(htr, (0, yPos + h ))
        yPos += h

    top.show()

MEMS Gears
-----------

.. plot::

    import numpy as np
    from gdsCAD import *


    def Gear(r, N, layer=None):
        """
        A crude gear.

        TODO: Make this involute
        """
        gear = core.Elements()

        d_theta = 360. / N 
        w = float(2*np.pi*r) / (2*N)

        disk = shapes.Disk((0,0), r-w/2, layer=layer)
        tooth = shapes.Rectangle((0, w/2), (r+w/2, -w/2), layer=layer)

        gear.add(disk)
        for i in range(N):
            gear.add(utils.rotate(tooth, i * d_theta))

        return gear

    top = core.Cell('TOP')

    gear1 = Gear(15, 20).rotate(360./20/2)
    gear2 = Gear(30, 40, 2).translate((45,0))

    top.add(gear1)
    top.add(gear2)

    top.show()

An Array of Many Devices
------------------------

.. plot::

    from gdsCAD import *

    device = core.Cell('DEVICE')

    rect = shapes.Rectangle((-200,-200), (200,200))
    tri = core.Boundary([[-80,-230], [0,0], [80,-230]], layer=2)    
    tri2 = utils.rotate(tri, 135).translate((20,20))
    tri.rotate(-45).translate((-20,-20))

    device.add(rect)
    device.add(tri)
    device.add(tri2)

    block = templates.Block('ARRAY', device, (7000, 5000))
    block.show()


Fanout
------

.. plot::
    
    from gdsCAD import *

    rndpad = core.Cell('RND_PAD')
    rndpad.add(shapes.Disk((0,0), 20))
    rndpad.add(shapes.Disk((0,0), 10, layer=2))

    sqpad = core.Cell('SQ_PAD')
    sqpad.add(shapes.Rectangle((-80,-80), (80,80)))
    sqpad.add(shapes.Rectangle((-50,-50), (50,50), layer=2))

    fanout = core.Cell('FANOUT')

    innerpts = np.arange(-5,6) * 50
    outerpts = np.arange(-5,6) * 200

    outline = -400
    bendline1 = -100
    bendline2 = -300
    for (i, (ins, out)) in enumerate(zip(innerpts, outerpts)):
        trace = core.Cell('TRACE_%d' % i)

        pts = [[ins, 0], [ins, bendline1], [out, bendline2], [out, outline]]
        trace.add(core.Path(pts, width=3))

        trace.add(rndpad, (ins, 0))   
        trace.add(sqpad,  (out, outline))
        
        fanout.add(trace)

    top = core.Cell('TOP')
    top.add(fanout, (0, -30))
    top.add(fanout, (0, 30), rotation=180)

    top.add(shapes.Label('1', 100, (200 * 6, -outline)))
    top.add(shapes.Label('22', 100, (200 * 6, outline)))

    top.show()
Contents:
