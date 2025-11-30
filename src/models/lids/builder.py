import FreeCAD
import math
from lib import cad_tools, constants
from . import geometry, features

def create_horizontal_lid(global_dims):
    """
    Creates the horizontal lid for the Hub.
    """
    # 1. Base Geometry
    lid_shape = geometry.create_base_hex(global_dims)
    
    # 2. Cut away South part
    cutter_south = geometry.create_horizontal_cutters(global_dims)
    lid_shape = lid_shape.cut(cutter_south)
    
    # Move to correct Z height
    lid_shape.translate(FreeCAD.Vector(0, 0, constants.Z_LID_BOTTOM))
    
    # 3. Mounting Pillars
    r = constants.PILLAR_MOUNTING_RADIUS
    y_60 = r * math.sin(math.radians(60))
    
    pillar_positions = [
        FreeCAD.Vector(r, 0, 0),      # 0 deg
        FreeCAD.Vector(r/2, y_60, 0), # 60 deg
        FreeCAD.Vector(-r/2, y_60, 0),# 120 deg
        FreeCAD.Vector(-r, 0, 0)      # 180 deg
    ]
    
    pillars, holes = features.create_mounting_pillars(pillar_positions)
    
    lid_shape = cad_tools.fuse_all(lid_shape, pillars)
    lid_shape = cad_tools.cut_all(lid_shape, holes)
    
    # 4. Magnet Recesses
    mag_cutters = features.create_magnet_recesses(global_dims, constants.Z_LID_BOTTOM)
    lid_shape = cad_tools.cut_all(lid_shape, mag_cutters)
    
    # 5. Pogo Cutout
    pogo_cutter = features.create_pogo_cutout()
    lid_shape = lid_shape.cut(pogo_cutter)
    
    return {
        "Lid_Horizontal": {
            "shape": lid_shape,
            "color": (0.3, 0.3, 0.3)
        }
    }

def create_sloped_lid(global_dims):
    """
    Creates the sloped lid.
    """
    # 1. Tall Base Geometry
    lid_shape = geometry.create_tall_base_hex(global_dims)
    
    # 2. Slope Cuts
    cutter_top, cutter_bottom, splitter = geometry.create_slope_cutters(global_dims)
    
    lid_shape = lid_shape.cut(cutter_top)
    lid_shape = lid_shape.cut(cutter_bottom)
    lid_shape = lid_shape.cut(splitter)
    
    # 3. Mounting Pillars
    r = constants.PILLAR_MOUNTING_RADIUS
    y_60 = r * math.sin(math.radians(60))
    
    pillar_positions = [
        FreeCAD.Vector(-r/2, -y_60, 0), # 240 deg
        FreeCAD.Vector(r/2, -y_60, 0)   # 300 deg
    ]
    
    # Height calculation function
    outer_flat_to_flat = global_dims['hub']['outer_flat_to_flat_mm']
    y_south = -outer_flat_to_flat / 2
    y_north_start = y_south + constants.SLOPE_LENGTH_Y
    z_top_wall = constants.FLOOR_HEIGHT + constants.WALL_HEIGHT
    angle_from_horizontal_rad = math.radians(90 - constants.SLOPE_ANGLE_DEG)
    
    def calc_pillar_height(pos):
        dist = y_north_start - pos.y
        z_lid_bottom_at_pillar = (z_top_wall - constants.LID_THICKNESS) - (dist * math.tan(angle_from_horizontal_rad))
        return z_lid_bottom_at_pillar - constants.FLOOR_HEIGHT
        
    pillars, holes = features.create_mounting_pillars(pillar_positions, height_func=calc_pillar_height)
    
    lid_shape = cad_tools.fuse_all(lid_shape, pillars)
    lid_shape = cad_tools.cut_all(lid_shape, holes)
    
    return {
        "Lid_Sloped": {
            "shape": lid_shape,
            "color": (0.3, 0.3, 0.3)
        }
    }
