# -*- coding: utf-8 -*-
"""
Created on Sat Apr 27 20:08:59 2013

@author: andrewmark
"""
from core import Cell, CellReference, CellArray, GdsImport

import os.path
import numpy as np

class wafer_Style1(Cell):
    """
    A Style1 Wafer
    
    TODO: Mark dicing lanes
          Add large scale alignment
          Add text labels
          Add wafer perimeter
          Magnify main alignment
    """
    
    #bottom left corners of blocks (in mm)
    block_pts=np.array([[1.41, 21.66],
                              [13.23, 5.29],
                            [13.23, 13.48],
                            [13.23, 21.66],
                            [13.23, 29.82],
                            [13.23, 38.02],
                            [25.05, 5.29],
                            [25.05, 13.48],
                            [25.05, 21.66],
                            [25.05, 29.82],
                            [25.05, 38.02],
                            [36.90, 21.66]])

    align_pts=np.array([[1.41, 13.48],
                            [1.41, 29.82],
                            [36.90, 13.48],
                            [36.90, 29.82]])+np.array([11./2, 7./2])


    def __init__(self, name, cells, origin=(0,0)):
        """Create a wafer with blocks in the scheme of style1
            
            cells: a list of cells that will be tiled to fill the blocks
                   style1 contains 12 blocks, the cells will be cycled until
                   all blocks are filled.
        """
        
        Cell.__init__(self, name)
        
        origin=np.array(origin)
        self._subcells=[]

        for (i, pt) in enumerate(self.block_pts):
            cell=cells[i % len(cells)]
            cell_name=('BLOCK%02d_'%(i))+cell.name
            print cell_name
            print pt*1000+origin
            block=block_section(cell_name, cell, (11e3, 7e3), pt*1000+origin)
            self.add(block)

        alignment = Cell('BLOCK_ALIGNMENT_'+str(id(self))[:4])
        mag = 10.
        for pt in self.align_pts:
            mark1=CellReference(Bott_Mark, origin=(pt*1000+origin), magnification=mag)
            mark2=CellReference(Top_Mark, origin=(pt*1000+origin), magnification=mag)
        
            alignment.add(mark1)
            alignment.add(mark2)

        self.add(alignment)        
        
    
class block_section(Cell):
    """
    Creates a block section
    """
    def __init__(self, name, cell, size, origin=(0,0),
                 spacing=None, edge_gap=0,
                 **kwargs):
        """
        Creates a rectangular block with alignment marks, label, and many copies of the cell        
        
        
        cell: the cell to tile
        origin: the location of the lower left corner of the block
        size: the width and height in physical units of the block
        edge_gap: how much space to leave around the perimeter of the block
        """

        Cell.__init__(self, name)
        size=np.asarray(size)
        origin=np.asarray(origin)

        #Create alignment marks
        bam=Bott_Mark
        tam=Top_Mark
        am_bbox=np.array([600,400])
        sp=size - am_bbox - 2*edge_gap
        self.add(CellArray(bam, 2, 2, sp, origin+am_bbox/2+edge_gap))
        self.add(CellArray(tam, 2, 2, sp, origin+am_bbox/2+edge_gap))
        
        #Pattern reference cell                
        if spacing is None:
            bbox = cell.get_bounding_box()
            bbox = np.array([bbox[1][0]-bbox[0][0], bbox[1][1]-bbox[0][1]])
            spacing=bbox*(2.)        

        # the tiled area consists of three regions:
        # the central section below and above the alignment marks
        # the top section between the two alignement marks
        # the bottom section between the two alignemnt marks
        
        self.N=0
        
        rows=int((size[0]-2*edge_gap)/spacing[0])
        cols=int((size[1]-2*am_bbox[1]-2*edge_gap)/spacing[1])       
        shift=np.array([0, am_bbox[1]])
        ar=CellArray(cell, rows, cols, spacing, origin+shift+edge_gap, **kwargs)
        self.add(ar)
        self.N+=rows*cols
        
        rows=int((size[0]-2*am_bbox[0]-2*edge_gap)/spacing[0])
        cols=int(am_bbox[1]/spacing[1])       
        shift=np.array([am_bbox[0], 0])
        ar=CellArray(cell, rows, cols, spacing, origin+shift+edge_gap, **kwargs)
        self.add(ar)
        
        shift = np.array([am_bbox[0], size[1]-2*edge_gap-am_bbox[1]])
        ar=CellArray(cell, rows, cols, spacing, origin+shift+edge_gap, **kwargs)
        self.add(ar)
        self.N+=2*rows*cols


        
#        tx=gdspy.Text('1', name, 100, origin)
#        self.add(tx)

def _AlignmentMark(layer):
    """


    Bottom (layer1):    300 x 300 um
    Top (layer3): 600x400um
    """
    cell=Cell('BOTT_ALIGN')
    path,_=os.path.split(__file__)
    fname=os.path.join(path, 'CONTACTALIGN.GDS')
    imp=GdsImport(fname)
    for el in imp['CONTACTALIGN'].elements:
        if el.layer==layer:
            cell.add(el)
    return cell

Bott_Mark=_AlignmentMark(1)
Top_Mark=_AlignmentMark(3)                