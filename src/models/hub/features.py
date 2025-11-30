import FreeCAD
import Part
import math

def create_magnet_pillars(body, dims):
    """Adds the 4 magnet mounting pillars."""
    magnet_dist = 33.5 
    
    mag_outer_r = 11.8 / 2
    mag_inner_r = 10.1 / 2
    mag_base_height = 11.2 
    mag_rim_height = 2.0
    
    # Base
    base = Part.makeCylinder(mag_outer_r, mag_base_height)
    base.translate(FreeCAD.Vector(0, 0, dims['floor_height']))
    
    # Rim
    r_out = Part.makeCylinder(mag_outer_r, mag_rim_height)
    r_in = Part.makeCylinder(mag_inner_r, mag_rim_height)
    rim = r_out.cut(r_in)
    rim.translate(FreeCAD.Vector(0, 0, dims['floor_height'] + mag_base_height))
    
    pillar = base.fuse(rim)
    
    # Positions
    positions = [
        FreeCAD.Vector(0, 0, 0), # Center
        FreeCAD.Vector(0, magnet_dist, 0) # North
    ]
    
    # Rotated
    v_north = FreeCAD.Vector(0, magnet_dist, 0)
    m = FreeCAD.Matrix()
    m.rotateZ(math.radians(60))
    positions.append(m.multVec(v_north))
    
    m = FreeCAD.Matrix()
    m.rotateZ(math.radians(-60))
    positions.append(m.multVec(v_north))
    
    for pos in positions:
        p = pillar.copy()
        p.translate(pos)
        body = body.fuse(p)
        
    return body

def create_pogo_pillars(body, dims):
    """Adds the 4 PogoPin pillars."""
    pogo_outer_r = 2.5
    pogo_hole_r = 1.0
    pogo_height = 9.7
    
    y_ref = 16.65
    y_offset = 7.5
    x_left = -6.0
    x_right = 5.0
    
    positions = [
        FreeCAD.Vector(x_left, y_ref + y_offset, 0),
        FreeCAD.Vector(x_left, y_ref - y_offset, 0),
        FreeCAD.Vector(x_right, y_ref + y_offset, 0),
        FreeCAD.Vector(x_right, y_ref - y_offset, 0)
    ]
    
    # Solid
    solid = Part.makeCylinder(pogo_outer_r, pogo_height)
    solid.translate(FreeCAD.Vector(0, 0, dims['floor_height']))
    
    for pos in positions:
        p = solid.copy()
        p.translate(pos)
        body = body.fuse(p)
        
    # Holes
    cutter = Part.makeCylinder(pogo_hole_r, pogo_height + 5)
    cutter.translate(FreeCAD.Vector(0, 0, dims['floor_height']))
    
    compound_holes = []
    for pos in positions:
        h = cutter.copy()
        h.translate(pos)
        compound_holes.append(h)
        
    if compound_holes:
        c = compound_holes[0]
        for h in compound_holes[1:]:
            c = c.fuse(h)
        body = body.cut(c)
        
    return body

def create_controller_features(body, dims):
    """Adds controller mounting pillars."""
    ctrl_outer_r = 2.5
    ctrl_hole_r = 1.0
    ctrl_height = 5.0
    
    positions = [
        FreeCAD.Vector(-16, 28, 0),
        FreeCAD.Vector(16, 28, 0),
        FreeCAD.Vector(-32, 0, 0),
        FreeCAD.Vector(32, 0, 0),
        FreeCAD.Vector(-17, -26, 0),
        FreeCAD.Vector(17, -26, 0)
    ]
    
    # Solid
    solid = Part.makeCylinder(ctrl_outer_r, ctrl_height)
    solid.translate(FreeCAD.Vector(0, 0, dims['floor_height']))
    
    for pos in positions:
        p = solid.copy()
        p.translate(pos)
        body = body.fuse(p)
        
    # Holes
    cutter = Part.makeCylinder(ctrl_hole_r, ctrl_height + 5)
    cutter.translate(FreeCAD.Vector(0, 0, dims['floor_height']))
    
    compound_holes = []
    for pos in positions:
        h = cutter.copy()
        h.translate(pos)
        compound_holes.append(h)
        
    if compound_holes:
        c = compound_holes[0]
        for h in compound_holes[1:]:
            c = c.fuse(h)
        body = body.cut(c)
        
    return body

def create_usb_features(body, dims):
    """Adds USB mounting pillars and wall cutout."""
    # 1. Pillars
    y_south_wall = -dims['inner_flat_to_flat'] / 2
    y_south_pillars = y_south_wall + 3.0
    y_north_pillars = y_south_pillars + 14.0
    x_offset = 7.0
    
    positions = [
        FreeCAD.Vector(-x_offset, y_north_pillars, 0),
        FreeCAD.Vector(x_offset, y_north_pillars, 0),
        FreeCAD.Vector(-x_offset, y_south_pillars, 0),
        FreeCAD.Vector(x_offset, y_south_pillars, 0)
    ]
    
    spcb_outer_r = 2.0
    spcb_inner_r = 1.0
    spcb_height = 1.0
    
    # Solid
    solid = Part.makeCylinder(spcb_outer_r, spcb_height)
    solid.translate(FreeCAD.Vector(0, 0, dims['floor_height']))
    
    for pos in positions:
        p = solid.copy()
        p.translate(pos)
        body = body.fuse(p)
        
    # Holes (Deep into floor)
    # Start Z=1.0, Length enough to clear top
    cutter = Part.makeCylinder(spcb_inner_r, spcb_height + 10)
    cutter.translate(FreeCAD.Vector(0, 0, 1.0))
    
    compound_holes = []
    for pos in positions:
        h = cutter.copy()
        h.translate(pos)
        compound_holes.append(h)
        
    if compound_holes:
        c = compound_holes[0]
        for h in compound_holes[1:]:
            c = c.fuse(h)
        body = body.cut(c)
        
    # 2. Wall Cutout
    cutout_w = 13.0
    cutout_h = 7.0
    cutout_r = 2.0
    material_above = 2.0
    
    cutout_top_z = dims['z_south_wall'] - material_above
    cutout_bottom_z = cutout_top_z - cutout_h
    
    y_south_outer = -dims['outer_flat_to_flat'] / 2
    y_south_inner = y_south_outer + dims['wall_thickness']
    
    y_cut_start = y_south_outer - 1.0
    y_cut_end = y_south_inner + 0.5
    cutout_depth = y_cut_end - y_cut_start
    
    box = Part.makeBox(cutout_w, cutout_depth, cutout_h)
    box.translate(FreeCAD.Vector(-cutout_w/2, y_cut_start, cutout_bottom_z))
    
    # Fillet
    edges = []
    for e in box.Edges:
        if abs(e.tangentAt(e.FirstParameter).y) > 0.99:
            edges.append(e)
            
    if edges:
        box = box.makeFillet(cutout_r, edges)
        
    body = body.cut(box)
    
    return body
