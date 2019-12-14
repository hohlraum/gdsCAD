import numpy as np
import gdspy
from gdsCAD import *
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath

# to avoid np.ndarray errors for gdspy polygons converted from gdsCAD, extract  the polygon points and reconstruct the polygon
def pyply(ply, ly):
    return gdspy.Polygon([list(i) for i in ply], layer=ly)
#end
# function to turn gdspy polygons into gdsCAD Boundary object
def pypol2bdy(plst, ly):
    return core.Boundary(plst.polygons, layer=ly)
#end

el_cad = core.Elements()
# notice the following definition only take in gdsCAD.core.Elements objects, flat or nested 
# def boolean(element01, element02, operation, ly):
#     aa = gdspy.PolygonSet([ii.points for ii in element02], layer=1)
#     mm = gdspy.PolygonSet([ii.points for ii in element01], layer=1)

#     aamm = gdspy.boolean([pyply(ii,1) for ii in mm.polygons], [pyply(ii,1) for ii in aa.polygons], operation)
#     for ii in aamm.polygons:
#         el_cad.add(core.Boundary(map(tuple, ii), layer=ly))
#     #end
#     return el_cad
# #end

# the following definition can take in any boundary object
def boolean(obj01, obj02, operation, ly):
    cl_aa = core.Cell('AA')
    cl_aa.add(obj02)
    cl_mm = core.Cell('MM')
    cl_mm.add(obj01)

    el_aa = core.Elements(cl_aa.flatten(), layer=ly)
    el_mm = core.Elements(cl_mm.flatten(), layer=ly)    #, obj_type='boundaries'

    aaa = gdspy.PolygonSet([ii.points for ii in el_aa], layer=ly)
    mmm = gdspy.PolygonSet([ii.points for ii in el_mm], layer=ly)

    aaa_mmm = gdspy.boolean([pyply(ii,1) for ii in mmm.polygons], [pyply(ii,1) for ii in aaa.polygons], operation)
    for ii in aaa_mmm.polygons:
        el_cad.add(core.Boundary(map(tuple, ii), layer=ly))
    #end
    return el_cad
#end

# test boolean
# a1 = core.Boundary([(0.0,0.0),(0.5,0.0),(0.5,0.5),(0.0,0.5)], layer=1)
# a2 = core.Boundary([(3.0,3.0),(4.0,3.0),(4.0,4.0),(3.0,4.0)], layer=1)
# a3 = core.Boundary([(4.0,1.5),(5.0,1.5),(5.0,2.5),(4.0,2.5)], layer=1)
# a4 = shapes.Disk((2.5,2.5),0.2,number_of_points=60)
# a5 = shapes.Disk((2.5,4.5), 0.3, inner_radius=0.1,number_of_points=60)
# a6 = shapes.Box((4.2,4.2),(4.5,4.5),width=0.1)
# a7 = shapes.Disk((4.5,3.0), 0.3, inner_radius=0.1,number_of_points=60,initial_angle=0,final_angle=180)
# a0 = core.Elements()
# a0.add(a1)
# a0.add(a2)
# a0.add(a3)
# a0.add(a4)     
# a0.add(a5)
# a0.add(a6)   # path object will be converted to boundary object
# # a0.add(a6)
# a0.add(a7)
# cl_a0 = core.Cell('A0')
# cl_a0.add(a0)
# m1 = core.Boundary([(0.0,0.0),(1.0,0.0),(1.0,1.0),(0.0,1.0)], layer=1)
# m2 = core.Boundary([(2.0,2.0),(5.0,2.0),(5.0,5.0),(2.0,5.0)], layer=1)
# m0 = core.Elements()
# m0.add(m1)
# m0.add(m2)

# result = boolean(m0,cl_a0,'not',1)

# cl_test = core.Cell('gdsCAD')
# ly_test = core.Layout('gdsCAD')

# cl_test.add(result)
# ly_test.add(cl_test)
# ly_test.save('test_boolean_function.gds')

