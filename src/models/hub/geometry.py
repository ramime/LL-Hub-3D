import FreeCAD
import Part
from lib import cad_tools
import math

def create_base_body(dims):
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

def create_lid_recesses(body, dims):
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

def create_rim(body, dims):
    """Adds the outer spacer rim."""
    rim_thickness = 0.5
    rim_height = 10.0
    
    rim_flat_to_flat_outer = dims['outer_flat_to_flat'] + (2 * rim_thickness)
    
    rim_outer = cad_tools.create_hexagon(rim_flat_to_flat_outer, rim_height)
    rim_inner = cad_tools.create_hexagon(dims['outer_flat_to_flat'], rim_height)
    
    rim = rim_outer.cut(rim_inner)
    return body.fuse(rim)

def create_floor_holes(body, dims):
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

def create_cable_channels(body, dims, open_sides):
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
    wire = Part.makePolygon(points + [points[0]])
    face = Part.Face(wire)
    cutter = face.extrude(FreeCAD.Vector(channel_depth, 0, 0))
    
    # Center the cutter on X (Depth)
    cutter.translate(FreeCAD.Vector(-channel_depth/2, 0, 0))
    
    # Lift to floor height
    cutter.translate(FreeCAD.Vector(0, 0, dims['floor_height']))
    
    dist = dims['outer_flat_to_flat'] / 2
    
    h = dims['inner_flat_to_flat'] / (2 * math.sqrt(3))
    
    # Offsets for each side (shift along the wall tangent)
    side_offsets = {
        0: -h + 11,
        1: -h + 9,
        2: h - 11,
        3: h - 11,
        4: -h + 9,
        5: -h + 11
    }
    
    for side_idx in open_sides:
        c = cutter.copy()
        
        # 1. Rotate to side angle
        angle = side_idx * 60 + 30
        c.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), angle)
        
        # 2. Move to wall distance
        # The cutter is centered at X=0. We need to move it to X=dist (apothem)
        # But we rotated it.
        # Let's do it differently:
        # Create at X=dist, Y=offset
        
        # Reset cutter
        c = cutter.copy()
        
        # Shift Y by offset
        offset = side_offsets.get(side_idx, 0)
        c.translate(FreeCAD.Vector(0, offset, 0))
        
        # Shift X to wall
        # The wall is at X = apothem (approx)
        # outer_flat_to_flat / 2
        apothem = dims['outer_flat_to_flat'] / 2.0
        c.translate(FreeCAD.Vector(apothem, 0, 0))
        
        # Rotate
        c.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), angle)
        
        body = body.cut(c)
        
    return body

def create_modifier(dims):
    """Creates the modifier body for the slot floor."""
    # Hexagon matching inner floor
    # Height 1.5mm
    # Z start: 0.5mm above floor (floor is at Z=0 relative to body start? No, floor starts at Z=0 and has height floor_height)
    # The floor solid starts at Z=0 and goes to Z=floor_height (2.0).
    # Modifier should start at Z = floor_height + 0.5?
    # "Its starting Z-position should be 0.5mm above the actual floor of the slot."
    # Actual floor surface is at Z=2.0.
    # So start at Z=2.5.
    # "It should extend 1mm below the actual floor of the slot."
    # So it goes down to Z=1.0.
    # Total height 1.5mm. (2.5 - 1.0 = 1.5). Correct.
    
    z_start = dims['floor_height'] - 1.0 # 1.0
    height = 1.5
    
    modifier = cad_tools.create_hexagon(dims['inner_flat_to_flat'], height)
    modifier.translate(FreeCAD.Vector(0, 0, z_start))
    
    return modifier
