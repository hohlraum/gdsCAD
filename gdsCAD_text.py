import numpy as np
import gdspy
from gdsCAD import *
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath

# the following 'render_text' function is copied from source below
######################################################################
#                                                                    #
#  Copyright 2009-2019 Lucas Heitzmann Gabrielli.                    #
#  This file is part of gdspy, distributed under the terms of the    #
#  Boost Software License - Version 1.0.  See the accompanying       #
#  LICENSE file or <http://www.boost.org/LICENSE_1_0.txt>            #
#                                                                    #
######################################################################

from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
import gdspy

def render_text(text, size=None, position=(0, 0), font_prop=None, tolerance=0.1):
    path = TextPath(position, text, size=size, prop=font_prop)
    polys = []
    xmax = position[0]
    for points, code in path.iter_segments():
        if code == path.MOVETO:
            c = gdspy.Curve(*points, tolerance=tolerance)
        elif code == path.LINETO:
            c.L(*points)
        elif code == path.CURVE3:
            c.Q(*points)
        elif code == path.CURVE4:
            c.C(*points)
        elif code == path.CLOSEPOLY:
            poly = c.get_points()
            if poly.size > 0:
                if poly[:, 0].min() < xmax:
                    i = len(polys) - 1
                    while i >= 0:
                        if gdspy.inside(poly[:1], [polys[i]], precision=0.1 * tolerance)[0]:
                            p = polys.pop(i)
                            poly = gdspy.boolean([p], [poly], 'xor', precision=0.1 * tolerance,
                                                 max_points=0).polygons[0]
                            break
                        elif gdspy.inside(polys[i][:1], [poly], precision=0.1 * tolerance)[0]:
                            p = polys.pop(i)
                            poly = gdspy.boolean([p], [poly], 'xor', precision=0.1 * tolerance,
                                                 max_points=0).polygons[0]
                        i -= 1
                xmax = max(xmax, poly[:, 0].max())
                polys.append(poly)
    return polys
#end


# define  texts , for horizontal texts, there is no need to respacing between characters, since it renders them difficult to read
def text_hrzt(letters,ftppt,size,ly):
    txt_polys = render_text(letters, size=size, font_prop=ftppt)
    txt_label = core.Elements()
    chars = [ core.Boundary(mm, layer=ly) for mm in txt_polys]
    for cc in chars:
        txt_label.add( cc  )
    # end
    txt_x_center = (txt_label.bounding_box[0,0] + txt_label.bounding_box[1,0])/2
    txt_y_center = (txt_label.bounding_box[0,1] + txt_label.bounding_box[1,1])/2
    txt_tsl = utils.translate(  txt_label, (-txt_x_center, -txt_y_center)  )
    return txt_tsl
#end

# for vertical texts, there is freedom to put gaps between characters.
# vtcl_sp is the vertical spacing between letters (characters if not in latin letters), ranging from 0 to 1
def text_vtcl(letters,ftppt,size,vtcl_sp, ly):
    letters_new = letters.replace(' ', '-')
    txt_label = core.Elements()
    chars = [text_hrzt(ii,ftppt, size, ly) for ii in letters_new]
    ht_chars = [nn.bounding_box[1,1]-nn.bounding_box[0,1] for nn in chars ]
    wdt_chars = [nn.bounding_box[1,0]-nn.bounding_box[0,0] for nn in chars  ]
    x_gap = max(wdt_chars)*vtcl_sp if len(chars)>1 else 0.0                    
    y_gap = max(ht_chars)*vtcl_sp if len(chars)>1 else 0.0                      # vtcl_sp is the vertical spacing between letters (characters if not in latin letters)
    for ii in np.arange(0,len(letters_new),1):
        cc = chars[ii]
        x_char_ct = (cc.bounding_box[0,0] + cc.bounding_box[1,0])/2
        y_char_ct = (cc.bounding_box[0,1] + cc.bounding_box[1,1])/2
        y_char_ct_new = (max(ht_chars)*len(chars) + y_gap*(len(chars)-1) )/2 - max(ht_chars)*(ii+1) - y_gap*ii + max(ht_chars)/2
        if letters[ii]==' ':
            continue
        txt_label.add(utils.translate(cc, (-x_char_ct, y_char_ct_new - y_char_ct)))
    # end
    txt_x_center = (txt_label.bounding_box[0,0] + txt_label.bounding_box[1,0])/2
    txt_y_center = (txt_label.bounding_box[0,1] + txt_label.bounding_box[1,1])/2
    txt_tsl = utils.translate(  txt_label, (-txt_x_center, -txt_y_center)  )
    return txt_tsl
#end
