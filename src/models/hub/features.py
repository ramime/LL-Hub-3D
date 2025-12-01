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

def create_usb_features(body, dims, angle=0.0):
    """Adds USB mounting pillars and wall cutout.
    angle: Rotation angle in degrees (0=South, -60=SW, +60=SE)
    """
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
    
    pillars_fuse = None
    
    for pos in positions:
        p = solid.copy()
        p.translate(pos)
        if pillars_fuse is None:
            pillars_fuse = p
        else:
            pillars_fuse = pillars_fuse.fuse(p)
        
    # Holes (Deep into floor)
    # Start Z=1.0, Length enough to clear top
    cutter = Part.makeCylinder(spcb_inner_r, spcb_height + 10)
    cutter.translate(FreeCAD.Vector(0, 0, 1.0))
    
    pillars_cut = None
    
    for pos in positions:
        h = cutter.copy()
        h.translate(pos)
        if pillars_cut is None:
            pillars_cut = h
        else:
            pillars_cut = pillars_cut.fuse(h)
            
    # Combine pillars solid and cut
    if pillars_fuse and pillars_cut:
        pillars_final = pillars_fuse.cut(pillars_cut)
    elif pillars_fuse:
        pillars_final = pillars_fuse
    else:
        pillars_final = None

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
        
    # Apply Rotation if needed
    if abs(angle) > 0.001:
        rot = FreeCAD.Matrix()
        rot.rotateZ(math.radians(angle))
        
        if pillars_final:
            pillars_final = pillars_final.transformGeometry(rot)
        
        box = box.transformGeometry(rot)

    # Fuse Pillars and Cut Box
    if pillars_final:
        body = body.fuse(pillars_final)
        
    body = body.cut(box)
    
    return body

def create_magnet_features(body, dims, magnet_config):
    """
    Adds magnet mounting features (housing and cutout) to the specified walls.
    
    magnet_config: dict { side_idx: [positions] }
      - side_idx: 1-6
      - positions: list of 'left', 'right' (or both)
      
    Geometry:
    - Housing: Box attached to inner wall.
      - Depth (from wall inwards): 2.6mm
      - Width: 9mm
      - Height: 6mm (from floor)
    - Cutout: Box cutting into wall and housing.
      - Depth: 3.2mm (2.1mm into wall, 1.1mm into housing)
      - Width: 6.2mm
      - Height: 10.5mm (from floor)
      
    Built at +X (East) wall (Angle 0) and rotated.
    """
    if not magnet_config:
        return body

    # Dimensions
    housing_depth = 2.6
    housing_width = 9.0
    housing_height = 6.0
    
    cutout_depth_total = 3.2
    cutout_into_wall = 2.1
    cutout_width = 6.2
    cutout_height = 10.5
    
    floor_height = dims['floor_height']
    apothem = dims['inner_flat_to_flat'] / 2.0
    
    # 1. Create Housing (Solid)
    # Built at +X wall.
    # X range: [apothem - housing_depth, apothem]
    # Y range: [-housing_width/2, housing_width/2]
    # Z range: [floor_height, floor_height + housing_height]
    
    h_x = apothem - housing_depth
    h_y = -housing_width / 2.0
    h_z = floor_height
    
    housing_box = Part.makeBox(housing_depth, housing_width, housing_height)
    housing_box.translate(FreeCAD.Vector(h_x, h_y, h_z))
    
    # 2. Create Cutout (Cutter)
    # X range: [apothem - (cutout_depth_total - cutout_into_wall), apothem + cutout_into_wall]
    # cutout_into_room = 3.2 - 2.1 = 1.1
    # X start = apothem - 1.1
    # X end = apothem + 2.1
    # Length = 3.2
    
    cutout_into_room = cutout_depth_total - cutout_into_wall
    c_x = apothem - cutout_into_room
    c_y = -cutout_width / 2.0
    c_z = floor_height
    
    cutout_box = Part.makeBox(cutout_depth_total, cutout_width, cutout_height)
    
    # Chamfer the top-outer edge (in the wall)
    # Edge at X=max (cutout_depth_total), Z=max (cutout_height), parallel to Y
    chamfer_edge = None
    for e in cutout_box.Edges:
        bbox = e.BoundBox
        # Check if edge is at the top-outer corner
        # X should be near cutout_depth_total (3.2)
        # Z should be near cutout_height (10.5)
        # Length should be near cutout_width (6.2) (Parallel to Y)
        if (abs(bbox.XMax - cutout_depth_total) < 0.01 and 
            abs(bbox.ZMax - cutout_height) < 0.01 and
            abs(bbox.YMax - bbox.YMin) > 1.0): 
            chamfer_edge = e
            break
            
    if chamfer_edge:
        cutout_box = cutout_box.makeChamfer(2.1, [chamfer_edge])
        
    cutout_box.translate(FreeCAD.Vector(c_x, c_y, c_z))
    
    # 3. Create Inner Cutout (Cutter for Housing)
    # Cut from the face facing the room (X = apothem - housing_depth) inwards.
    # Width: 4.2mm (centered)
    # Height: 7.0mm (to clear top)
    # Depth: 2.1mm
    
    in_cut_w = 4.2
    in_cut_h = 7.0
    in_cut_d = 2.1
    
    in_cut_x = apothem - housing_depth
    in_cut_y = -in_cut_w / 2.0
    in_cut_z = floor_height
    
    inner_cutout = Part.makeBox(in_cut_d, in_cut_w, in_cut_h)
    inner_cutout.translate(FreeCAD.Vector(in_cut_x, in_cut_y, in_cut_z))

    # Positions on the wall (Y-offsets)
    # "10mm from inner corner"
    # Side length s = inner_flat_to_flat / sqrt(3)
    # Corner is at y = +/- s/2
    # Position = +/- (s/2 - 10)
    
    side_length = dims['inner_flat_to_flat'] / math.sqrt(3)
    y_offset_abs = (side_length / 2.0) - 10.0
    
    # Mapping 'left'/'right' to Y offsets
    # Looking at the wall from center:
    # Left is +Y (for East wall)
    # Right is -Y (for East wall)
    pos_map = {
        'left': y_offset_abs,
        'right': -y_offset_abs
    }

    # Side Angles (from geometry.py logic)
    # 1=N(90), 2=NE(30), 3=SE(330), 4=S(270), 5=SW(210), 6=NW(150)
    side_angles = {
        1: 90,
        2: 30,
        3: 330,
        4: 270,
        5: 210,
        6: 150
    }
    
    # Apply to each side
    for side_idx, positions in magnet_config.items():
        angle = side_angles.get(side_idx, 0)
        
        # Normalize positions to list if it's not (though we expect list)
        if not isinstance(positions, (list, tuple)):
            positions = [positions]
            
        for pos_key in positions:
            y_off = pos_map.get(pos_key)
            if y_off is None:
                continue
                
            # Create a compound of the feature parts for this position
            # Translate to Y offset BEFORE rotation
            
            # Housing
            h = housing_box.copy()
            h.translate(FreeCAD.Vector(0, y_off, 0))
            h.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), angle)
            body = body.fuse(h)
            
            # Cutout
            c = cutout_box.copy()
            c.translate(FreeCAD.Vector(0, y_off, 0))
            c.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), angle)
            body = body.cut(c)
            
            # Inner Cutout
            ic = inner_cutout.copy()
            ic.translate(FreeCAD.Vector(0, y_off, 0))
            ic.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), angle)
            body = body.cut(ic)
        
    return body
