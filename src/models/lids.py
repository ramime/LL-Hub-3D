import FreeCAD
import Part
from lib import cad_tools
import math

def create_horizontal_lid(global_dims):
    """
    Creates the horizontal lid for the Hub.
    """
    outer_flat_to_flat = global_dims['hub']['outer_flat_to_flat_mm']
    wall_thickness = global_dims['hub']['wall_thickness_mm']
    inner_flat_to_flat = outer_flat_to_flat - (2 * wall_thickness)
    
    recess_width = 1.0
    lid_flat_to_flat = inner_flat_to_flat + (2 * recess_width) - 0.2 # 0.2mm clearance
    
    lid_thickness = 1.8
    
    # 1. Base Plate (Full Hexagon initially)
    lid_shape = cad_tools.create_hexagon(lid_flat_to_flat, lid_thickness)
    
    # 2. Cut away the South (Sloped) part
    slope_length_y = 29.0
    y_south = -outer_flat_to_flat / 2
    y_north_start = y_south + slope_length_y
    
    x_width = outer_flat_to_flat * 2
    cutter_south = Part.makeBox(x_width, x_width, 50)
    cutter_south.translate(FreeCAD.Vector(-x_width/2, y_north_start - x_width, 0))
    
    lid_shape = lid_shape.cut(cutter_south)
    
    # Move to correct Z height
    floor_height = 2.0
    wall_height = 14.0
    z_lid_bottom = floor_height + wall_height - lid_thickness # 14.2
    lid_shape.translate(FreeCAD.Vector(0, 0, z_lid_bottom))
    
    # 3. Mounting Pillars (4x)
    # Positions: Match the 6 floor holes at Radius 40mm.
    # Horizontal Lid covers North part (Y > y_north_start).
    # Angles: 0, 60, 120, 180.
    r = 40.0
    y_60 = r * math.sin(math.radians(60))
    
    pillar_positions = [
        FreeCAD.Vector(r, 0, 0),      # 0 deg
        FreeCAD.Vector(r/2, y_60, 0), # 60 deg
        FreeCAD.Vector(-r/2, y_60, 0),# 120 deg
        FreeCAD.Vector(-r, 0, 0)      # 180 deg
    ]
    
    pillar_outer_r = 6.0 / 2
    pillar_inner_r = 2.0 / 2
    
    # Height of pillar: From Floor (Z=2.0) to Lid Bottom (Z=14.2)
    pillar_len = z_lid_bottom - floor_height # 12.2
    
    pillar_solid = Part.makeCylinder(pillar_outer_r, pillar_len)
    pillar_solid.translate(FreeCAD.Vector(0, 0, floor_height))
    
    # Fuse pillars to lid
    for pos in pillar_positions:
        p = pillar_solid.copy()
        p.translate(pos)
        lid_shape = lid_shape.fuse(p)
        
    # Cut Holes (Sackloch: through pillar but NOT through lid surface)
    hole_cutter = Part.makeCylinder(pillar_inner_r, pillar_len)
    hole_cutter.translate(FreeCAD.Vector(0, 0, floor_height))
    
    for pos in pillar_positions:
        h = hole_cutter.copy()
        h.translate(pos)
        lid_shape = lid_shape.cut(h)
        
    return {
        "Lid_Horizontal": {
            "shape": lid_shape,
            "color": (0.3, 0.3, 0.3) # Dark Grey
        }
    }

def create_sloped_lid(global_dims):
    """
    Creates the sloped lid.
    """
    outer_flat_to_flat = global_dims['hub']['outer_flat_to_flat_mm']
    wall_thickness = global_dims['hub']['wall_thickness_mm']
    inner_flat_to_flat = outer_flat_to_flat - (2 * wall_thickness)
    recess_width = 1.0
    lid_flat_to_flat = inner_flat_to_flat + (2 * recess_width) - 0.2
    
    # 1. Big Hexagon Prism
    hex_prism = cad_tools.create_hexagon(lid_flat_to_flat, 30)
    
    # 2. Define Slope Planes
    slope_length_y = 29.0
    slope_angle_deg = 80.0
    floor_height = 2.0
    wall_height = 14.0
    z_top_wall = floor_height + wall_height
    
    y_south = -outer_flat_to_flat / 2
    y_north_start = y_south + slope_length_y
    
    angle_from_horizontal_rad = math.radians(90 - slope_angle_deg)
    delta_z = slope_length_y * math.tan(angle_from_horizontal_rad)
    z_south = z_top_wall - delta_z
    
    x_width = outer_flat_to_flat * 2
    
    # Points for Top Cutter (removes above lid)
    cut_points_top = [
        (y_north_start, z_top_wall),
        (y_south, z_south),
        (y_south, z_top_wall + 20),
        (y_north_start, z_top_wall + 20)
    ]
    
    # Points for Bottom Cutter (removes below lid)
    lid_thickness = 1.8
    cut_points_bottom = [
        (y_north_start, z_top_wall - lid_thickness),
        (y_south, z_south - lid_thickness),
        (y_south, 0),
        (y_north_start, 0)
    ]
    
    # Extrude Cutters
    def make_cutter(pts):
        vec_pts = [FreeCAD.Vector(-x_width/2, p[0], p[1]) for p in pts]
        return cad_tools.create_prism_from_points(vec_pts, FreeCAD.Vector(x_width, 0, 0))
        
    cutter_top = make_cutter(cut_points_top)
    cutter_bottom = make_cutter(cut_points_bottom)
    
    # Apply cuts to Hex Prism
    lid_shape = hex_prism.cut(cutter_top)
    lid_shape = lid_shape.cut(cutter_bottom)
    
    # Splitter Box (Keep South)
    splitter = Part.makeBox(x_width, x_width, 50)
    splitter.translate(FreeCAD.Vector(-x_width/2, y_north_start, 0))
    lid_shape = lid_shape.cut(splitter)
    
    # Pillars for Sloped Lid
    # Positions: Match the 6 floor holes at Radius 40mm.
    # Sloped Lid covers South part (Y < y_north_start).
    # Angles: 240, 300.
    r = 40.0
    y_60 = r * math.sin(math.radians(60))
    
    pillar_positions = [
        FreeCAD.Vector(-r/2, -y_60, 0), # 240 deg
        FreeCAD.Vector(r/2, -y_60, 0)   # 300 deg
    ]
    
    pillar_outer_r = 6.0 / 2
    pillar_inner_r = 2.0 / 2
    
    for pos in pillar_positions:
        # Calculate height at this Y
        dist = y_north_start - pos.y
        z_lid_bottom_at_pillar = (z_top_wall - lid_thickness) - (dist * math.tan(angle_from_horizontal_rad))
        
        this_pillar_len = z_lid_bottom_at_pillar - floor_height
        
        p = Part.makeCylinder(pillar_outer_r, this_pillar_len)
        p.translate(FreeCAD.Vector(0, 0, floor_height))
        p.translate(pos)
        
        lid_shape = lid_shape.fuse(p)
        
        # Cut Hole (Sackloch)
        h = Part.makeCylinder(pillar_inner_r, this_pillar_len)
        h.translate(FreeCAD.Vector(0, 0, floor_height))
        h.translate(pos)
        lid_shape = lid_shape.cut(h)

    return {
        "Lid_Sloped": {
            "shape": lid_shape,
            "color": (0.3, 0.3, 0.3)
        }
    }
