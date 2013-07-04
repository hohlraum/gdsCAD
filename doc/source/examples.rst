************
Examples
************

Lots of examples


.. plot::

    import matplotlib.pyplot as plt
    from gdsCAD import *
    
    top=core.Cell('TOP')
    
    top.add(shapes.Rectangle(1, (0,0), (10,10)))    
    top.add(core.Path(2, [(0,0), (1,2), (2,4), (4,5), (6,20), (-10,20)]))
    
    l=core.Layout('composite')
    l.add(top)
        
    top.show()
    plt.show()

.. plot::

   import matplotlib.pyplot as plt
   import numpy as np
   x = np.random.randn(1000)
   plt.hist( x, 20)
   plt.grid()
   plt.title(r'Normal: $\mu=%.2f, \sigma=%.2f$'%(x.mean(), x.std()))
   plt.show()


Contents:
