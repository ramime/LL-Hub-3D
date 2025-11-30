import FreeCAD
import Part
import math
from lib import cad_tools, constants

def create_base_hex(global_dims):
    """
    Creates the base hexagon for the lid.
    """
    outer_flat_to_flat = global_dims['hub']['outer_flat_to_flat_mm']
    wall_thickness = global_dims['hub']['wall_thickness_mm']
    inner_flat_to_flat = outer_flat_to_flat - (2 * wall_thickness)
    
    lid_flat_to_flat = inner_flat_to_flat + (2 * constants.LID_RECESS_WIDTH) - constants.LID_CLEARANCE
    
    # Create Hexagon Prism
    # For horizontal lid, height is LID_THICKNESS.
    # For sloped lid, we create a taller prism and cut it.
    # We'll return the shape with LID_THICKNESS by default, 
    # but for sloped lid we might need a different approach or just extrude more there.
    # Actually, let's just return the 2D shape or a prism of requested height?
    # Let's return the prism of LID_THICKNESS for standard usage.
    
    return cad_tools.create_hexagon(lid_flat_to_flat, constants.LID_THICKNESS)

def create_tall_base_hex(global_dims, height=30.0):
    """
    Creates a taller hexagon prism for the sloped lid to be cut.
    """
    outer_flat_to_flat = global_dims['hub']['outer_flat_to_flat_mm']
    wall_thickness = global_dims['hub']['wall_thickness_mm']
    inner_flat_to_flat = outer_flat_to_flat - (2 * wall_thickness)
    lid_flat_to_flat = inner_flat_to_flat + (2 * constants.LID_RECESS_WIDTH) - constants.LID_CLEARANCE
    
    return cad_tools.create_hexagon(lid_flat_to_flat, height)

def create_slope_cutters(global_dims):
    """
    Creates the cutters for the sloped lid.
    Returns (cutter_top, cutter_bottom, splitter_box)
    """
    outer_flat_to_flat = global_dims['hub']['outer_flat_to_flat_mm']
    
    y_south = -outer_flat_to_flat / 2
    y_north_start = y_south + constants.SLOPE_LENGTH_Y
    
    z_top_wall = constants.FLOOR_HEIGHT + constants.WALL_HEIGHT
    
    angle_from_horizontal_rad = math.radians(90 - constants.SLOPE_ANGLE_DEG)
    delta_z = constants.SLOPE_LENGTH_Y * math.tan(angle_from_horizontal_rad)
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
    cut_points_bottom = [
        (y_north_start, z_top_wall - constants.LID_THICKNESS),
        (y_south, z_south - constants.LID_THICKNESS),
        (y_south, 0),
        (y_north_start, 0)
    ]
    
    def make_cutter(pts):
        vec_pts = [FreeCAD.Vector(-x_width/2, p[0], p[1]) for p in pts]
        return cad_tools.create_prism_from_points(vec_pts, FreeCAD.Vector(x_width, 0, 0))
        
    cutter_top = make_cutter(cut_points_top)
    cutter_bottom = make_cutter(cut_points_bottom)
    
    # Splitter Box (Keep South)
    splitter = Part.makeBox(x_width, x_width, 50)
    splitter.translate(FreeCAD.Vector(-x_width/2, y_north_start, 0))
    
    return cutter_top, cutter_bottom, splitter

def create_horizontal_cutters(global_dims):
    """
    Creates the cutter for the horizontal lid (cutting away the south part).
    """
    outer_flat_to_flat = global_dims['hub']['outer_flat_to_flat_mm']
    y_south = -outer_flat_to_flat / 2
    y_north_start = y_south + constants.SLOPE_LENGTH_Y
    
    x_width = outer_flat_to_flat * 2
    cutter_south = Part.makeBox(x_width, x_width, 50)
    cutter_south.translate(FreeCAD.Vector(-x_width/2, y_north_start - x_width, 0))
    
    return cutter_south
