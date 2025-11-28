import FreeCAD
import Part
from lib import cad_tools

def create_model(params, global_dims):
    """
    Creates the Hub model.
    Returns a dictionary of parts: {'part_name': shape}
    """
    # 1. Get Dimensions
    # We interpret 'outer_flat_to_flat_mm' as the Outer Flat-to-Flat dimension of the floor/wall structure
    outer_flat_to_flat = global_dims['hub']['outer_flat_to_flat_mm']
    
    # Wall thickness from JSON (2.4mm)
    wall_thickness = global_dims['hub']['wall_thickness_mm']
    
    # Heights
    floor_height = 2.0 # Fixed value as per user request
    wall_height = 14.0 # Height of the wall sitting ON TOP of the floor
    
    # 2. Create Floor
    # Hexagon with outer dimensions
    floor_shape = cad_tools.create_hexagon(outer_flat_to_flat, floor_height)
    
    # 3. Create Wall
    # The wall sits on the floor. It has the same outer dimension, but is hollow.
    # Outer Hexagon Prism
    wall_outer = cad_tools.create_hexagon(outer_flat_to_flat, wall_height)
    
    # Inner Hexagon Prism (Hole)
    # Inner flat-to-flat = Outer flat-to-flat - 2 * wall_thickness
    inner_flat_to_flat = outer_flat_to_flat - (2 * wall_thickness)
    wall_inner = cad_tools.create_hexagon(inner_flat_to_flat, wall_height)
    
    # Cut hole from outer wall
    wall_shape = wall_outer.cut(wall_inner)
    
    # Move wall up to sit on floor
    wall_shape.translate(FreeCAD.Vector(0, 0, floor_height))
    
    # 4. Fuse Floor and Wall
    hub_body = floor_shape.fuse(wall_shape)

    # 5. Apply Slope Cut (Chamfer) on South Side
    # Parameters
    slope_length_y = 29.0
    slope_angle_deg = 80.0 # Angle from Vertical
    
    # Geometry Calculation
    # Y-Coordinates
    # South edge is at Y = -outer_flat_to_flat / 2
    y_south = -outer_flat_to_flat / 2
    y_north_start = y_south + slope_length_y
    
    # Z-Coordinates
    # We assume the slope starts at the full wall height at y_north_start and goes down towards south.
    # Full height at top of wall
    z_top = floor_height + wall_height
    
    # Calculate height drop
    # Angle is 80 deg from vertical -> 10 deg from horizontal
    # tan(10) = delta_z / delta_y
    # delta_z = delta_y * tan(10)
    # But wait, user said "80 Grad gemessen an der Senkrechten".
    # If the wall is vertical (90 deg), and we measure 80 deg from it, the remaining angle to horizontal is 10 deg.
    # Let's use math.tan(radians(90 - 80))
    import math
    angle_from_horizontal_rad = math.radians(90 - slope_angle_deg)
    delta_z = slope_length_y * math.tan(angle_from_horizontal_rad)
    
    z_south = z_top - delta_z
    
    # Define the Cutting Prism (in YZ plane, extruded in X)
    # We want to cut away everything ABOVE the slope line.
    # So the prism should be a triangle/polygon defined by:
    # P1: (y_north_start, z_top) - The pivot point
    # P2: (y_south, z_south) - The point on the slope at the south edge
    # P3: (y_south, z_top + 10) - A point high above to clear everything
    # P4: (y_north_start, z_top + 10) - High above pivot
    
    # X-Extrusion needs to be wide enough to cover the whole hexagon width
    # Hexagon width (point-to-point) is 2 * circumradius = 2 * (d / sqrt(3))
    # d = 84.2 -> R = 48.6 -> Width = 97.2. Let's use 120 to be safe.
    x_width = outer_flat_to_flat * 2 
    
    cut_points = [
        (0, y_north_start, z_top),
        (0, y_south, z_south),
        (0, y_south, z_top + 20), # Go high enough
        (0, y_north_start, z_top + 20)
    ]
    
    # Create the prism
    # We define it at X=0 and extrude in both directions? 
    # create_prism_from_points extrudes in one direction.
    # So let's define points at X = -x_width/2 and extrude by +x_width
    
    cut_points_shifted = []
    for p in cut_points:
        cut_points_shifted.append(FreeCAD.Vector(-x_width/2, p[1], p[2]))
        
    cutter = cad_tools.create_prism_from_points(cut_points_shifted, FreeCAD.Vector(x_width, 0, 0))
    
    # Apply Cut
    hub_body = hub_body.cut(cutter)
    
    return {
        "Hub_Body": {
            "shape": hub_body,
            "color": (0.9, 0.9, 0.9) # Light Grey
        }
    }
