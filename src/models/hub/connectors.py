import FreeCAD
import Part
import math

def _get_inner_prism(dims):
    """Creates the inner hexagon prism for cutting connectors."""
    wall_thickness = dims['wall_thickness']
    inner_flat_to_flat = dims['outer_flat_to_flat'] - (2 * wall_thickness)
    r_inner = inner_flat_to_flat / math.sqrt(3)
    
    inner_shape = Part.makePolygon([
        FreeCAD.Vector(r_inner, 0, 0),
        FreeCAD.Vector(r_inner/2, inner_flat_to_flat/2, 0),
        FreeCAD.Vector(-r_inner/2, inner_flat_to_flat/2, 0),
        FreeCAD.Vector(-r_inner, 0, 0),
        FreeCAD.Vector(-r_inner/2, -inner_flat_to_flat/2, 0),
        FreeCAD.Vector(r_inner/2, -inner_flat_to_flat/2, 0),
        FreeCAD.Vector(r_inner, 0, 0)
    ])
    inner_face = Part.Face(inner_shape)
    inner_prism = inner_face.extrude(FreeCAD.Vector(0, 0, 20))
    inner_prism.translate(FreeCAD.Vector(0, 0, -5))
    return inner_prism

def _get_outer_prism(dims):
    """Creates the outer hexagon prism for trimming housings."""
    outer_flat_to_flat = dims['outer_flat_to_flat']
    r_outer = outer_flat_to_flat / math.sqrt(3)
    
    outer_shape = Part.makePolygon([
        FreeCAD.Vector(r_outer, 0, 0),
        FreeCAD.Vector(r_outer/2, outer_flat_to_flat/2, 0),
        FreeCAD.Vector(-r_outer/2, outer_flat_to_flat/2, 0),
        FreeCAD.Vector(-r_outer, 0, 0),
        FreeCAD.Vector(-r_outer/2, -outer_flat_to_flat/2, 0),
        FreeCAD.Vector(r_outer/2, -outer_flat_to_flat/2, 0),
        FreeCAD.Vector(r_outer, 0, 0)
    ])
    outer_face = Part.Face(outer_shape)
    # Extrude high enough to cover the housing (Z=0 to Z=4+)
    outer_prism = outer_face.extrude(FreeCAD.Vector(0, 0, 20))
    outer_prism.translate(FreeCAD.Vector(0, 0, -5))
    return outer_prism

def _get_connector_profile(dims, clearance=0.0):
    """Creates the 2D profile for the connector rail."""
    # Square with 4mm edge length, rotated 45 deg.
    # Shifted down by 0.9mm.
    # Cut off at Y=0 (Z=0 in Hub).
    
    edge_len = 4.0
    shift_down = 0.9
    
    # Diagonal of 4mm square
    diag = edge_len * math.sqrt(2) # ~5.657
    half_diag = diag / 2.0 # ~2.828
    
    center_y = half_diag - shift_down 
    
    # Points:
    p_bottom_l = FreeCAD.Vector(-0.9, 0, 0)
    p_bottom_r = FreeCAD.Vector(0.9, 0, 0)
    p_right = FreeCAD.Vector(half_diag, center_y, 0)
    p_top = FreeCAD.Vector(0, center_y + half_diag, 0)
    p_left = FreeCAD.Vector(-half_diag, center_y, 0)
    
    points = [p_bottom_l, p_bottom_r, p_right, p_top, p_left]
    
    wire = Part.makePolygon(points + [points[0]])
    
    if clearance > 0:
        try:
            offset_wire = wire.makeOffset2D(clearance)
            face = Part.Face(offset_wire)
        except Exception:
            face = Part.Face(wire)
    else:
        face = Part.Face(wire)
        
    return face

def create_connector_ne(body, dims):
    """Adds NE Connector (Side 0)."""
    R = dims['outer_flat_to_flat'] / math.sqrt(3)
    apothem = dims['outer_flat_to_flat'] / 2.0
    
    v0 = FreeCAD.Vector(R, 0, 0)
    v60 = FreeCAD.Vector(R/2, apothem, 0)
    
    # Position: 15mm from V0 towards V60
    dist_ne = 15.0
    dir_ne = v60.sub(v0).normalize()
    pos_ne = v0.add(dir_ne.multiply(dist_ne))
    
    # Shift Inwards (-Y)
    pos_ne.y -= 4.0
    
    length = dims['pin_length']
    prof_ne = _get_connector_profile(dims, clearance=0.0)
    prof_ne.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0), 90) # Y->Z
    conn_ne = prof_ne.extrude(FreeCAD.Vector(0, length, 0)) # +Y
    conn_ne.translate(pos_ne)
    
    # Cut
    inner_prism = _get_inner_prism(dims)
    conn_ne = conn_ne.cut(inner_prism)
    
    return body.fuse(conn_ne)

def create_connector_nw(body, dims):
    """Adds NW Connector (Side 2) - Mirrored from NE."""
    # We calculate NE position and mirror X
    R = dims['outer_flat_to_flat'] / math.sqrt(3)
    apothem = dims['outer_flat_to_flat'] / 2.0
    
    v0 = FreeCAD.Vector(R, 0, 0)
    v60 = FreeCAD.Vector(R/2, apothem, 0)
    
    # NE Position Calculation
    dist_ne = 15.0
    dir_ne = v60.sub(v0).normalize()
    pos_ne = v0.add(dir_ne.multiply(dist_ne))
    pos_ne.y -= 4.0 # Shift
    
    # Mirror to NW (X -> -X)
    pos_nw = FreeCAD.Vector(-pos_ne.x, pos_ne.y, 0)
    
    length = dims['pin_length']
    prof_nw = _get_connector_profile(dims, clearance=0.0)
    prof_nw.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0), 90) # Y->Z
    conn_nw = prof_nw.extrude(FreeCAD.Vector(0, length, 0)) # +Y
    conn_nw.translate(pos_nw)
    
    # Cut
    inner_prism = _get_inner_prism(dims)
    conn_nw = conn_nw.cut(inner_prism)
    
    return body.fuse(conn_nw)

def create_connector_sw(body, dims):
    """Adds SW Female Connector (Side 3) - Counterpart to NE."""
    R = dims['outer_flat_to_flat'] / math.sqrt(3)
    apothem = dims['outer_flat_to_flat'] / 2.0
    
    v180 = FreeCAD.Vector(-R, 0, 0)
    v240 = FreeCAD.Vector(-R/2, -apothem, 0)
    
    dist_sw = 15.0
    dir_sw = v180.sub(v240).normalize()
    pos_sw = v240.add(dir_sw.multiply(dist_sw))
    
    # Shift (+Y)
    pos_sw.y += 4.0
    
    # Create Housing (Block)
    housing_h = 4.0
    width = 8.0
    depth = dims['pin_length']
    housing_shape = Part.makeBox(width, depth, housing_h)
    # Center it at pos_sw
    housing_shape.translate(FreeCAD.Vector(-width/2, -depth/2, 0))
    housing_shape.translate(pos_sw)
    
    # Trim Housing to Outer Hexagon (so it doesn't protrude outwards)
    outer_prism = _get_outer_prism(dims)
    housing_shape = housing_shape.common(outer_prism)
    
    body = body.fuse(housing_shape)
    
    # Create Cutout (Female Profile)
    # Clearance 0.15mm
    prof_sw = _get_connector_profile(dims, clearance=0.15)
    prof_sw.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0), 90) # Y->Z
    
    # Extrusion Direction:
    # NE Pin points +Y. So the cutout is also +Y.
    # We need to cut "through" the wall and housing.
    
    # Let's translate -10 Y and extrude 40 Y?
    cutout_sw = prof_sw.extrude(FreeCAD.Vector(0, 40, 0)) # Re-extrude longer
    cutout_sw.translate(pos_sw)
    cutout_sw.translate(FreeCAD.Vector(0, -20, 0)) # Center roughly
    
    body = body.cut(cutout_sw)
    
    return body

def create_connector_se(body, dims):
    """Adds SE Female Connector (Side 5) - Counterpart to NW."""
    # Side 5 connects V300 and V0.
    # Counterpart to NW (Side 2).
    # NW Position: Mirrored NE.
    # SE Position: Mirrored SW (X -> -X).
    
    # Calculate SW Position again
    R = dims['outer_flat_to_flat'] / math.sqrt(3)
    apothem = dims['outer_flat_to_flat'] / 2.0
    v180 = FreeCAD.Vector(-R, 0, 0)
    v240 = FreeCAD.Vector(-R/2, -apothem, 0)
    dist_sw = 15.0
    dir_sw = v180.sub(v240).normalize()
    pos_sw = v240.add(dir_sw.multiply(dist_sw))
    pos_sw.y += 4.0
    
    # Mirror to SE (X -> -X)
    pos_se = FreeCAD.Vector(-pos_sw.x, pos_sw.y, 0)
    
    # Housing
    housing_h = 4.0
    width = 8.0
    depth = dims['pin_length']
    housing_shape = Part.makeBox(width, depth, housing_h)
    housing_shape.translate(FreeCAD.Vector(-width/2, -depth/2, 0))
    housing_shape.translate(pos_se)
    
    # Trim Housing
    outer_prism = _get_outer_prism(dims)
    housing_shape = housing_shape.common(outer_prism)
    
    body = body.fuse(housing_shape)
    
    # Cutout
    prof_se = _get_connector_profile(dims, clearance=0.15)
    prof_se.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0), 90) # Y->Z
    
    cutout_se = prof_se.extrude(FreeCAD.Vector(0, 40, 0))
    cutout_se.translate(pos_se)
    cutout_se.translate(FreeCAD.Vector(0, -20, 0))
    
    body = body.cut(cutout_se)
    
    return body

def create_connectors(body, dims, connectors_config):
    """
    Generic connector creation for Side 1 (N) and Side 4 (S).
    connectors_config: list of dicts { 'side': int, 'type': 'male'|'female' }
    """
    # Center-Based Logic for N/S
    # Side 1 (N): Center is (0, apothem). Normal (0, 1).
    # Side 4 (S): Center is (0, -apothem). Normal (0, -1).
    
    apothem = dims['outer_flat_to_flat'] / 2.0
    
    for side, ctype in connectors_config.items():
        if side == 1: # North
            pos = FreeCAD.Vector(0, apothem, 0)
            rotation = 0 # Pointing +Y
            
            if ctype == 'male':
                pos.y -= 4.0
                _create_generic_male(body, dims, pos, rotation)
            elif ctype == 'female':
                pos.y -= 4.0
                _create_generic_female(body, dims, pos, rotation)
                
        elif side == 4: # South
            pos = FreeCAD.Vector(0, -apothem, 0)
            rotation = 180 # Pointing -Y
            
            if ctype == 'male':
                pos.y += 4.0 # Shift Inwards (+Y)
                _create_generic_male(body, dims, pos, rotation)
            elif ctype == 'female':
                pos.y += 4.0
                _create_generic_female(body, dims, pos, rotation)
                
        # New 1-based Numbering Mapping
        # 2: NE (Old 0)
        # 3: SE (Old 5)
        # 5: SW (Old 3)
        # 6: NW (Old 2)
        
        elif side == 2: # NE
             if ctype == 'male':
                 body = create_connector_ne(body, dims)
             # Add female support if needed later
             
        elif side == 6: # NW
             if ctype == 'male':
                 body = create_connector_nw(body, dims)
                 
        elif side == 5: # SW
             if ctype == 'female':
                 body = create_connector_sw(body, dims)
                 
        elif side == 3: # SE
             if ctype == 'female':
                 body = create_connector_se(body, dims)

    return body

def _create_generic_male(body, dims, pos, rotation_deg):
    """Creates a male connector at pos with rotation."""
    length = dims['pin_length']
    prof = _get_connector_profile(dims, clearance=0.0)
    prof.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0), 90) # Y->Z
    
    # Extrude +Y
    pin = prof.extrude(FreeCAD.Vector(0, length, 0))
    
    # Rotate around Z
    pin.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), rotation_deg)
    
    # Translate
    pin.translate(pos)
    
    # Cut Inner
    inner_prism = _get_inner_prism(dims)
    pin = pin.cut(inner_prism)
    
    body.fuse(pin)

def _create_generic_female(body, dims, pos, rotation_deg):
    """Creates a female connector at pos with rotation."""
    # Housing
    housing_h = 4.0
    width = 8.0
    depth = dims['pin_length']
    housing = Part.makeBox(width, depth, housing_h)
    housing.translate(FreeCAD.Vector(-width/2, -depth/2, 0))
    
    # Rotate Housing
    housing.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), rotation_deg)
    housing.translate(pos)
    
    # Trim Housing
    outer_prism = _get_outer_prism(dims)
    housing = housing.common(outer_prism)
    
    body.fuse(housing)
    
    # Cutout
    prof = _get_connector_profile(dims, clearance=0.15)
    prof.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0), 90) # Y->Z
    
    # Extrude
    cutout = prof.extrude(FreeCAD.Vector(0, 40, 0))
    
    # Rotate Cutout
    cutout.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), rotation_deg)
    
    # Translate
    cutout.translate(pos)
    
    # Center correction (since we extruded 40, we need to shift back 20 along the rotation axis)
    # Vector(0, -20, 0) rotated
    shift = FreeCAD.Vector(0, -20, 0)
    m = FreeCAD.Matrix()
    m.rotateZ(math.radians(rotation_deg))
    shift = m.multVec(shift)
    cutout.translate(shift)
    
    body.cut(cutout)
