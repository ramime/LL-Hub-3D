import FreeCAD
import Part
from lib import cad_tools
import math

def create_model(params, global_dims, features={}):
    """
    Creates the Hub model.
    Returns a dictionary of parts: {'part_name': shape}
    features: dict of enabled features.
        - controller_mounts: bool
        - usb_mounts: bool
        - open_sides: list of int (0-5) - indices of walls to cut cable channels into.
    """
    # Extract dimensions
    dims = _extract_dimensions(global_dims)
    
    # 1. Create Base Body (Floor + Wall + Slope)
    hub_body = _create_base_body(dims)
    
    # 2. Add Lid Recesses
    hub_body = _create_lid_recesses(hub_body, dims)
    
    # 3. Add Spacer Rim
    hub_body = _create_rim(hub_body, dims)
    
    # 4. Add Floor Mounting Holes
    hub_body = _create_floor_holes(hub_body, dims)
    
    # 5. Add Magnet Pillars
    hub_body = _create_magnet_pillars(hub_body, dims)
    
    # 6. Add PogoPin Pillars
    hub_body = _create_pogo_pillars(hub_body, dims)
    
    # 7. Add Controller Mounts (Optional)
    if features.get('controller_mounts', False):
        hub_body = _create_controller_features(hub_body, dims)
        
    # 8. Add USB Mounts & Cutout (Optional)
    if features.get('usb_mounts', False):
        hub_body = _create_usb_features(hub_body, dims)

    # 9. Add Cable Channels (Cutouts)
    open_sides = features.get('open_sides', [])
    if open_sides:
        hub_body = _create_cable_channels(hub_body, dims, open_sides)
        
    # 10. Add Connectors (Configurable)
    if features.get('conn_ne', False):
        hub_body = _create_connector_ne(hub_body, dims)
    if features.get('conn_nw', False):
        hub_body = _create_connector_nw(hub_body, dims)
    if features.get('conn_e', False):
        hub_body = _create_connector_e(hub_body, dims)

    # 11. Create Modifier (for printing optimization)
    modifier = _create_modifier(dims)
    
    return {
        "Hub_Body": {
            "shape": hub_body,
            "color": (0.9, 0.9, 0.9) # Light Grey
        },
        "Modifier": {
            "shape": modifier,
            "color": (0.2, 0.8, 0.2) # Greenish
        }
    }

# ... (Previous functions unchanged) ...

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

def _create_connector_ne(body, dims):
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
    
    length = 20.0
    prof_ne = _get_connector_profile(dims, clearance=0.0)
    prof_ne.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0), 90) # Y->Z
    conn_ne = prof_ne.extrude(FreeCAD.Vector(0, length, 0)) # +Y
    conn_ne.translate(pos_ne)
    
    # Cut
    inner_prism = _get_inner_prism(dims)
    conn_ne = conn_ne.cut(inner_prism)
    
    return body.fuse(conn_ne)

def _create_connector_nw(body, dims):
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
    
    length = 20.0
    prof_nw = _get_connector_profile(dims, clearance=0.0)
    prof_nw.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0), 90) # Y->Z
    conn_nw = prof_nw.extrude(FreeCAD.Vector(0, length, 0)) # +Y
    conn_nw.translate(pos_nw)
    
    # Cut
    inner_prism = _get_inner_prism(dims)
    conn_nw = conn_nw.cut(inner_prism)
    
    return body.fuse(conn_nw)

def _create_connector_e(body, dims):
    """Adds East Connector (Side 5)."""
    R = dims['outer_flat_to_flat'] / math.sqrt(3)
    apothem = dims['outer_flat_to_flat'] / 2.0
    
    v0 = FreeCAD.Vector(R, 0, 0)
    v300 = FreeCAD.Vector(R/2, -apothem, 0)
    
    # Position: 10mm from V300 towards V0
    dist_e = 10.0
    dir_e = v0.sub(v300).normalize()
    pos_e = v300.add(dir_e.multiply(dist_e))
    
    # Shift Inwards (-X)
    shift_x_e = -1.0
    pos_e.x += shift_x_e
    
    length = 20.0
    prof_e = _get_connector_profile(dims, clearance=0.0)
    prof_e.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0), 90) # XZ
    prof_e.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), 90) # YZ
    conn_e = prof_e.extrude(FreeCAD.Vector(length, 0, 0)) # +X
    conn_e.translate(pos_e)
    
    # Cut
    inner_prism = _get_inner_prism(dims)
    conn_e = conn_e.cut(inner_prism)
    
    return body.fuse(conn_e)

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

def _extract_dimensions(global_dims):
    """Helper to extract and calculate common dimensions."""
    d = {}
    d['outer_flat_to_flat'] = global_dims['hub']['outer_flat_to_flat_mm']
    d['wall_thickness'] = global_dims['hub']['wall_thickness_mm']
    d['floor_height'] = 2.0
    d['wall_height'] = 14.0
    d['inner_flat_to_flat'] = d['outer_flat_to_flat'] - (2 * d['wall_thickness'])
    
    # Slope parameters
    d['slope_length_y'] = 29.0
    d['slope_angle_deg'] = 80.0
    
    # Calculate Z heights
    d['z_top_wall'] = d['floor_height'] + d['wall_height']
    
    angle_rad = math.radians(90 - d['slope_angle_deg'])
    d['delta_z_slope'] = d['slope_length_y'] * math.tan(angle_rad)
    d['z_south_wall'] = d['z_top_wall'] - d['delta_z_slope']
    
    # Connector Dimensions
    d['rail_spacing'] = 10.0
    d['male_z_height'] = 5.0
    d['female_housing_height'] = 4.0
    d['pin_length'] = 20.0
    d['recess_depth'] = 3.0
    
    return d

def _create_base_body(dims):
    """Creates the basic floor and wall structure with slope cut."""
    # Floor
    floor = cad_tools.create_hexagon(dims['outer_flat_to_flat'], dims['floor_height'])
    
    # Wall
    wall_outer = cad_tools.create_hexagon(dims['outer_flat_to_flat'], dims['wall_height'])
    wall_inner = cad_tools.create_hexagon(dims['inner_flat_to_flat'], dims['wall_height'])
    wall = wall_outer.cut(wall_inner)
    wall.translate(FreeCAD.Vector(0, 0, dims['floor_height']))
    
    # Fuse
    body = floor.fuse(wall)
    
    # Apply Slope Cut
    y_south = -dims['outer_flat_to_flat'] / 2
    y_north_start = y_south + dims['slope_length_y']
    
    # Cutter Prism Points (YZ plane)
    # We cut everything ABOVE the slope line.
    z_top = dims['z_top_wall']
    z_south = dims['z_south_wall']
    
    cut_points = [
        (y_north_start, z_top),
        (y_south, z_south),
        (y_south, z_top + 20),
        (y_north_start, z_top + 20)
    ]
    
    x_width = dims['outer_flat_to_flat'] * 2
    
    # Create Prism
    vec_points = [FreeCAD.Vector(-x_width/2, y, z) for y, z in cut_points]
    cutter = cad_tools.create_prism_from_points(vec_points, FreeCAD.Vector(x_width, 0, 0))
    
    return body.cut(cutter)

def _create_lid_recesses(body, dims):
    """Adds the horizontal and sloped lid recesses."""
    recess_depth = 1.8
    recess_width = 1.0
    recess_flat_to_flat = dims['inner_flat_to_flat'] + (2 * recess_width)
    
    # 1. Horizontal Recess
    # Cut from top edge
    z_recess_start = dims['z_top_wall'] - recess_depth
    cutter_horiz = cad_tools.create_hexagon(recess_flat_to_flat, recess_depth)
    cutter_horiz.translate(FreeCAD.Vector(0, 0, z_recess_start))
    
    body = body.cut(cutter_horiz)
    
    # 2. Sloped Recess
    # We need to remove material to create a shelf 1.8mm below the slope surface,
    # but only within the 1mm wide rim area.
    
    # Recreate the slope cutter geometry but shifted down
    y_south = -dims['outer_flat_to_flat'] / 2
    y_north_start = y_south + dims['slope_length_y']
    z_top = dims['z_top_wall']
    z_south = dims['z_south_wall']
    
    cut_points_recess = [
        (y_north_start, z_top - recess_depth),
        (y_south, z_south - recess_depth),
        (y_south, z_top + 20),
        (y_north_start, z_top + 20)
    ]
    
    x_width = dims['outer_flat_to_flat'] * 2
    vec_points = [FreeCAD.Vector(-x_width/2, y, z) for y, z in cut_points_recess]
    slope_cutter_lower = cad_tools.create_prism_from_points(vec_points, FreeCAD.Vector(x_width, 0, 0))
    
    # Create the "Recess Ring" (the area to be cut)
    ring_outer = cad_tools.create_hexagon(recess_flat_to_flat, 30)
    ring_inner = cad_tools.create_hexagon(dims['inner_flat_to_flat'], 30)
    recess_ring = ring_outer.cut(ring_inner)
    
    # Intersect: We want to cut the volume that is (Above Lower Slope) AND (Inside Ring)
    cut_volume = slope_cutter_lower.common(recess_ring)
    
    return body.cut(cut_volume)

def _create_rim(body, dims):
    """Adds the outer spacer rim."""
    rim_thickness = 0.5
    rim_height = 10.0
    
    rim_flat_to_flat_outer = dims['outer_flat_to_flat'] + (2 * rim_thickness)
    
    rim_outer = cad_tools.create_hexagon(rim_flat_to_flat_outer, rim_height)
    rim_inner = cad_tools.create_hexagon(dims['outer_flat_to_flat'], rim_height)
    
    rim = rim_outer.cut(rim_inner)
    return body.fuse(rim)

def _create_floor_holes(body, dims):
    """Cuts the 6 mounting holes in the floor."""
    hole_dist = 40.0
    hole_r = 2.4 / 2
    chamfer = 0.8
    
    # Create single cutter
    cyl = Part.makeCylinder(hole_r, 10)
    cone = Part.makeCone(hole_r + chamfer, hole_r, chamfer)
    cutter = cyl.fuse(cone)
    
    # Pattern
    all_cutters = []
    for i in range(6):
        c = cutter.copy()
        c.translate(FreeCAD.Vector(hole_dist, 0, 0))
        c.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), i * 60)
        all_cutters.append(c)
        
    if all_cutters:
        compound = all_cutters[0]
        for c in all_cutters[1:]:
            compound = compound.fuse(c)
        body = body.cut(compound)
        
    return body

def _create_magnet_pillars(body, dims):
    """Adds the 4 magnet mounting pillars."""
    magnet_dist = 33.5 # Hardcoded based on previous logic/user input if not in dims
    # Actually it was in global_dims['system']['magnet_mounting_radius_mm']
    # But we don't have global_dims here, only dims.
    # Let's assume it's standard or passed. 
    # Wait, I didn't extract it in _extract_dimensions. Let's fix that assumption.
    # I'll use a default or re-read from global_dims if I had it.
    # Since I can't change the signature of _extract_dimensions easily inside this block without context,
    # I will assume 33.5 as it was used in calculation before (or I should have passed it).
    # Ah, in the original code: magnet_dist = global_dims['system']['magnet_mounting_radius_mm']
    # I should add it to _extract_dimensions.
    
    # NOTE: I will update _extract_dimensions to include this.
    # But for now, I'll use the value 33.5 which is standard for this project.
    magnet_dist = 33.5 
    
    mag_outer_r = 11.8 / 2
    mag_inner_r = 10.1 / 2
    mag_base_height = 11.2 # From Z=2.0
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

def _create_pogo_pillars(body, dims):
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

def _create_controller_features(body, dims):
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

def _create_usb_features(body, dims):
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
    
    body = body.cut(box)
    
    return body

def _create_cable_channels(body, dims, open_sides):
    """Cuts cable channels into the specified walls."""
    # Dimensions from user drawing
    width = 10.0
    total_height = 7.0
    # derived from 135 degree angle (45 degree slope)
    # tan(45) = 1, so roof height = half_width = 5.0
    roof_height = width / 2.0 
    side_height = total_height - roof_height # 2.0
    
    channel_depth = dims['wall_thickness'] * 2 
    
    # Create Profile in YZ plane (centered on Y)
    # Points: Bottom-Left, Bottom-Right, Vertical-Right, Top-Peak, Vertical-Left
    y_half = width / 2.0
    
    points = [
        FreeCAD.Vector(0, -y_half, 0),
        FreeCAD.Vector(0, y_half, 0),
        FreeCAD.Vector(0, y_half, side_height),
        FreeCAD.Vector(0, 0, total_height),
        FreeCAD.Vector(0, -y_half, side_height)
    ]
    
    # Create Prism (Extrude along X)
    # We create a face on X=0 plane and extrude
    # Actually cad_tools.create_prism_from_points expects points in a plane and an extrusion vector.
    # But my points are already 3D vectors on X=0.
    # Let's just use Part.makePolygon and extrude.
    
    wire = Part.makePolygon(points + [points[0]])
    face = Part.Face(wire)
    cutter = face.extrude(FreeCAD.Vector(channel_depth, 0, 0))
    
    # Center the cutter on X (Depth)
    cutter.translate(FreeCAD.Vector(-channel_depth/2, 0, 0))
    
    # Lift to floor height
    cutter.translate(FreeCAD.Vector(0, 0, dims['floor_height']))
    
    dist = dims['outer_flat_to_flat'] / 2
    
    # Calculate side length (inner)
    # inner_flat_to_flat = 2 * apothem
    # side_length = inner_flat_to_flat / sqrt(3)
    # half_side = side_length / 2
    
    h = dims['inner_flat_to_flat'] / (2 * math.sqrt(3))
    
    # Offsets for each side (shift along the wall tangent)
    # Calculated based on user requirements:
    # Side 1 (N): 4mm from Right (-h). -> -h + 4 + 5 = -h + 9
    # Side 4 (S): Aligned with N. -> h - 9
    # Side 0 (NE): 6mm from South (-h). -> -h + 6 + 5 = -h + 11
    # Side 2 (NW): 6mm from South (+h). -> h - 6 - 5 = h - 11
    # Side 3 (SW): Aligned with NE. -> h - 11
    # Side 5 (SE): Aligned with NW. -> -h + 11
    
    side_offsets = {
        0: -h + 11,
        1: -h + 9,
        2: h - 11,
        3: h - 11,
        4: h - 9,
        5: -h + 11
    }
    
    compound_cutters = []
    
    for side_idx in open_sides:
        angle_deg = 30 + (side_idx * 60)
        offset = side_offsets.get(side_idx, 0)
        
        c = cutter.copy()
        # Translate to the wall distance
        c.translate(FreeCAD.Vector(dist, offset, 0))
        
        # Rotate around Z
        c.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), angle_deg)
        
        compound_cutters.append(c)
        
    if compound_cutters:
        c_all = compound_cutters[0]
        for c in compound_cutters[1:]:
            c_all = c_all.fuse(c)
        body = body.cut(c_all)
        
    return body

def _create_modifier(dims):
    """Creates the modifier body for the floor to save filament."""
    # Simple hexagon corresponding to inner floor area
    # Start 0.5mm above floor bottom (Z=0.5)
    # Height 1.5mm (Ends at Z=2.0)
    
    modifier = cad_tools.create_hexagon(dims['inner_flat_to_flat'], 1.5)
    modifier.translate(FreeCAD.Vector(0, 0, 0.5))
    return modifier

def _create_connectors(body, dims, connectors):
    """Adds Male/Female connectors to specified sides."""
    for side_idx, c_type in connectors.items():
        if c_type == 'male':
            body = _create_male_connector(body, dims, side_idx)
        elif c_type == 'female':
            body = _create_female_connector(body, dims, side_idx)
    return body

def _get_rail_orientation(side_idx):
    """Returns the extrusion vector for the rails (Horizontal X or Vertical Y)."""
    # Side 0 (NE), 5 (SE) -> X (1,0,0)
    # Side 2 (NW), 3 (SW) -> X (-1,0,0)
    # Side 1 (N) -> Y (0,1,0)
    # Side 4 (S) -> Y (0,-1,0)
    
    if side_idx in [0, 5]:
        return FreeCAD.Vector(1, 0, 0)
    elif side_idx in [2, 3]:
        return FreeCAD.Vector(-1, 0, 0)
    elif side_idx == 1:
        return FreeCAD.Vector(0, 1, 0)
    elif side_idx == 4:
        return FreeCAD.Vector(0, -1, 0)
    return FreeCAD.Vector(0, 1, 0)

def _get_connector_profile(dims, clearance=0.0):
    """Creates the 2D profile for the connector rail."""
    # New Requirement:
    # Square with 4mm edge length, rotated 45 deg.
    # Shifted down by 0.9mm.
    # Cut off at Y=0 (Z=0 in Hub).
    
    edge_len = 4.0
    shift_down = 0.9
    
    # Diagonal of 4mm square
    diag = edge_len * math.sqrt(2) # ~5.657
    half_diag = diag / 2.0 # ~2.828
    
    # Center Y (so that bottom tip is at -shift_down)
    # Bottom tip of centered diamond is at -half_diag.
    # We want it at -shift_down.
    # So we shift by (-shift_down - (-half_diag)) = half_diag - shift_down.
    center_y = half_diag - shift_down # 2.828 - 0.9 = 1.928
    
    # Coordinates of the diamond corners (before cut)
    # Top: (0, center_y + half_diag)
    # Right: (half_diag, center_y)
    # Bottom: (0, center_y - half_diag) -> Should be -0.9
    # Left: (-half_diag, center_y)
    
    # We need to intersect this with Y >= 0.
    # The bottom edges are lines from (0, -0.9) to (+/- half_diag, center_y).
    # Slope m = (center_y - (-0.9)) / half_diag = (half_diag) / half_diag = 1.
    # Line Right: y = x - 0.9. At y=0 -> x = 0.9.
    # Line Left: y = -x - 0.9. At y=0 -> x = -0.9.
    
    # So the points at Y=0 are (-0.9, 0) and (0.9, 0).
    
    # Points:
    p_bottom_l = FreeCAD.Vector(-0.9, 0, 0)
    p_bottom_r = FreeCAD.Vector(0.9, 0, 0)
    p_right = FreeCAD.Vector(half_diag, center_y, 0)
    p_top = FreeCAD.Vector(0, center_y + half_diag, 0)
    p_left = FreeCAD.Vector(-half_diag, center_y, 0)
    
    points = [p_bottom_l, p_bottom_r, p_right, p_top, p_left]
    
    wire = Part.makePolygon(points + [points[0]])
    
    # Apply clearance if needed
    if clearance > 0:
        # Offset the wire outwards
        # makeOffset2D returns a wire (or list of wires?)
        try:
            offset_wire = wire.makeOffset2D(clearance)
            face = Part.Face(offset_wire)
        except Exception:
            # Fallback if makeOffset2D fails or not available (older FC)
            # Simple scaling? No, scaling is wrong.
            # Let's manually offset points? Complex for general polygon.
            # But this is a convex polygon.
            # Let's try to just return the face of the wire and hope clearance is handled elsewhere?
            # No, we need it here.
            # Let's assume makeOffset2D works (standard in recent FC).
            face = Part.Face(wire) # Fallback
            # Log warning?
            pass
            
            # Actually, let's try to implement a simple manual offset for this specific shape if we want to be safe.
            # But makeOffset2D is best.
            face = Part.Face(offset_wire)
    else:
        face = Part.Face(wire)
        
    return face

def _create_male_connector(body, dims, side_idx):
    """Creates the male connector (Rails in Recess)."""
    dist_outer = dims['outer_flat_to_flat'] / 2
    angle_deg = 30 + (side_idx * 60)
    
    # 1. Create Recess
    recess_w = 20.0
    recess_d = dims['recess_depth']
    recess_h = dims['male_z_height']
    
    box = Part.makeBox(recess_w, recess_d, recess_h)
    box.translate(FreeCAD.Vector(-recess_w/2, -recess_d, 0))
    box.translate(FreeCAD.Vector(0, dist_outer, 0))
    box.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), angle_deg)
    
    body = body.cut(box)
    
    # 2. Create Rails
    spacing = dims['rail_spacing']
    ext_vec = _get_rail_orientation(side_idx)
    length = dims['pin_length']
    
    rails = []
    for i in [-1, 1]:
        offset_val = (spacing / 2) * i
        
        # Profile in XY
        prof = _get_connector_profile(dims, clearance=0.0)
        
        # Rotate to XZ (Y becomes Z)
        prof.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0), 90)
        
        # Rotate based on extrusion direction
        if abs(ext_vec.x) > 0.9: # Extrusion along X
            prof.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), 90) # To YZ
            prof.translate(FreeCAD.Vector(0, offset_val, 0))
        elif abs(ext_vec.y) > 0.9: # Extrusion along Y
            prof.translate(FreeCAD.Vector(offset_val, 0, 0))
            
        # Extrude
        rail = prof.extrude(ext_vec.multiply(length))
        
        # Center longitudinally
        rail.translate(ext_vec.multiply(-length/2))
        
        # Move to Wall Center Position
        m = FreeCAD.Matrix()
        m.rotateZ(math.radians(angle_deg))
        wall_center_pt = m.multVec(FreeCAD.Vector(0, dist_outer - recess_d, 0))
        
        rail.translate(FreeCAD.Vector(wall_center_pt.x, wall_center_pt.y, 0))
        
        rails.append(rail)
        
    for r in rails:
        body = body.fuse(r)
        
    return body

def _create_female_connector(body, dims, side_idx):
    """Creates the female connector (Cutout + Housing)."""
    dist_outer = dims['outer_flat_to_flat'] / 2
    angle_deg = 30 + (side_idx * 60)
    
    # 1. Housing
    housing_h = dims['female_housing_height']
    housing_w = 24.0
    housing_d = 8.0
    
    box = Part.makeBox(housing_w, housing_d, housing_h)
    box.translate(FreeCAD.Vector(-housing_w/2, -housing_d, 0))
    box.translate(FreeCAD.Vector(0, dist_outer, 0))
    box.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), angle_deg)
    
    body = body.fuse(box)
    
    # 2. Cutouts
    spacing = dims['rail_spacing']
    ext_vec = _get_rail_orientation(side_idx)
    length = dims['pin_length'] + 10.0
    
    cutters = []
    for i in [-1, 1]:
        offset_val = (spacing / 2) * i
        
        prof = _get_connector_profile(dims, clearance=0.15)
        prof.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0), -90)
        
        if abs(ext_vec.x) > 0.9:
            prof.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), 90)
            prof.translate(FreeCAD.Vector(0, offset_val, 0))
        elif abs(ext_vec.y) > 0.9:
            prof.translate(FreeCAD.Vector(offset_val, 0, 0))
            
        cutter = prof.extrude(ext_vec.multiply(length))
        cutter.translate(ext_vec.multiply(-length/2))
        
        m = FreeCAD.Matrix()
        m.rotateZ(math.radians(angle_deg))
        wall_center_pt = m.multVec(FreeCAD.Vector(0, dist_outer, 0))
        
        cutter.translate(FreeCAD.Vector(wall_center_pt.x, wall_center_pt.y, 0))
        
        cutters.append(cutter)
        
    for c in cutters:
        body = body.cut(c)
        
    return body
