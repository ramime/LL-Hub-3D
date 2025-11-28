import FreeCAD
import Part
from lib import cad_tools

def create_horizontal_lid(global_dims):
    """
    Creates the horizontal lid for the Hub.
    """
    # Dimensions
    # It fits into the recess.
    # Recess starts at inner_flat_to_flat and goes outwards by recess_width (1mm).
    # So Lid Flat-to-Flat = inner_flat_to_flat + 2*recess_width.
    # BUT we need some clearance! Let's assume tight fit for now or -0.2mm?
    # User didn't specify clearance, but usually 3D printing needs 0.1-0.2mm.
    # Let's use exact dimensions for CAD, slicer can handle XY-compensation if needed, 
    # or we subtract a small tolerance.
    
    outer_flat_to_flat = global_dims['hub']['outer_flat_to_flat_mm']
    wall_thickness = global_dims['hub']['wall_thickness_mm']
    inner_flat_to_flat = outer_flat_to_flat - (2 * wall_thickness)
    
    recess_width = 1.0
    lid_flat_to_flat = inner_flat_to_flat + (2 * recess_width) - 0.2 # 0.2mm clearance total (0.1 per side)
    
    lid_thickness = 1.8
    
    # 1. Base Plate (Full Hexagon initially)
    lid_shape = cad_tools.create_hexagon(lid_flat_to_flat, lid_thickness)
    
    # 2. Cut away the South (Sloped) part
    # The split line is at y_north_start.
    # We want to KEEP North (Y > y_north_start).
    # So we cut away South (Y < y_north_start).
    
    # Slope parameters (needed for split line)
    slope_length_y = 29.0
    y_south = -outer_flat_to_flat / 2
    y_north_start = y_south + slope_length_y
    
    # Create a cutter box for the south part
    # Box from Y = -BigNumber to y_north_start
    x_width = outer_flat_to_flat * 2
    cutter_south = Part.makeBox(x_width, x_width, 50) # Big enough
    # Position: X centered, Y ends at y_north_start
    cutter_south.translate(FreeCAD.Vector(-x_width/2, y_north_start - x_width, 0))
    
    lid_shape = lid_shape.cut(cutter_south)
    
    # Move to correct Z height
    floor_height = 2.0
    wall_height = 14.0
    z_lid_bottom = floor_height + wall_height - lid_thickness # 16 - 1.8 = 14.2
    lid_shape.translate(FreeCAD.Vector(0, 0, z_lid_bottom))
    
    # 3. Mounting Pillars (4x)
    # "beim Horizontalen Deckel werden 4 Pfeiler benötigt"
    # Positions: Need to be in the North part (Y > y_north_start).
    # y_north_start is around -42 + 29 = -13.
    # Top edge is at +42.
    # So we have space from Y=-13 to Y=42.
    # Let's place them in a rectangle?
    # X: +/- 20
    # Y: 0 and 25?
    
    pillar_positions = [
        FreeCAD.Vector(-20, 0, 0),
        FreeCAD.Vector(20, 0, 0),
        FreeCAD.Vector(-20, 25, 0),
        FreeCAD.Vector(20, 25, 0)
    ]
    
    pillar_outer_r = 6.0 / 2
    pillar_inner_r = 2.0 / 2
    
    # Height of pillar:
    # From Floor (Z=2.0) to Lid Bottom (Z=14.2)
    pillar_len = z_lid_bottom - floor_height # 12.2
    
    pillar_solid = Part.makeCylinder(pillar_outer_r, pillar_len)
    pillar_solid.translate(FreeCAD.Vector(0, 0, floor_height)) # Starts at floor
    
    # Fuse pillars to lid
    for pos in pillar_positions:
        p = pillar_solid.copy()
        p.translate(pos)
        lid_shape = lid_shape.fuse(p)
        
    # Cut Holes (through pillar but NOT through lid surface)
    # Pillar goes from Z=2.0 to Z=14.2.
    # Lid is above Z=14.2.
    # We want the hole to be inside the pillar.
    # Let's cut from Z=2.0 up to Z=14.2 (or slightly less to be safe? User said "Sackloch").
    # If we cut up to 14.2, it touches the lid bottom.
    # If we want it "auf den Flächen aufsitzen, als seien sie dort aufgeklebt", 
    # then the hole should go through the pillar but not the lid.
    # So cutting from Z=2.0 to Z=14.2 is correct.
    
    hole_cutter = Part.makeCylinder(pillar_inner_r, pillar_len) # Length 12.2
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
    # This is trickier.
    # It needs to fit into the sloped recess.
    # The sloped recess was created by intersecting the "Slope Cutter Lower" with the "Recess Ring".
    
    # Strategy:
    # 1. Recreate the "Slope Cutter Lower" (the volume removed for the recess).
    # 2. Use this as the base shape for the lid?
    #    No, that volume is just the rim. The lid covers the whole center too.
    
    # Better Strategy:
    # 1. Create a big Hexagon Prism (full width).
    # 2. Cut it with the "Slope Plane" (Top Surface).
    # 3. Cut it with the "Lower Slope Plane" (Bottom Surface, 1.8mm lower).
    #    This gives a plate of 1.8mm thickness that follows the slope.
    # 4. Intersect with the Hexagon boundary (Inner + Recess).
    
    outer_flat_to_flat = global_dims['hub']['outer_flat_to_flat_mm']
    wall_thickness = global_dims['hub']['wall_thickness_mm']
    inner_flat_to_flat = outer_flat_to_flat - (2 * wall_thickness)
    recess_width = 1.0
    lid_flat_to_flat = inner_flat_to_flat + (2 * recess_width) - 0.2
    
    # 1. Big Hexagon Prism (Vertical boundaries)
    # Height doesn't matter much, just needs to cover Z range.
    hex_prism = cad_tools.create_hexagon(lid_flat_to_flat, 30)
    
    # 2. Define Slope Planes
    slope_length_y = 29.0
    slope_angle_deg = 80.0
    floor_height = 2.0
    wall_height = 14.0
    z_top_wall = floor_height + wall_height # 16.0
    
    y_south = -outer_flat_to_flat / 2
    y_north_start = y_south + slope_length_y
    
    import math
    angle_from_horizontal_rad = math.radians(90 - slope_angle_deg)
    delta_z = slope_length_y * math.tan(angle_from_horizontal_rad)
    z_south = z_top_wall - delta_z
    
    # We need to Keep everything BELOW the Slope Plane.
    # And Keep everything ABOVE the (Slope Plane - 1.8mm).
    
    # Let's create a "Slope Cutter" that removes everything ABOVE the slope.
    # (Same as in hub.py)
    x_width = outer_flat_to_flat * 2
    
    # Points for Top Cutter (removes above lid)
    # Pivot at (y_north_start, z_top_wall)
    p1 = (y_north_start, z_top_wall)
    p2 = (y_south, z_south)
    # We want to cut everything ABOVE the line P1-P2.
    # So polygon goes UP.
    cut_points_top = [
        (y_north_start, z_top_wall),
        (y_south, z_south),
        (y_south, z_top_wall + 20),
        (y_north_start, z_top_wall + 20)
    ]
    
    # Points for Bottom Cutter (removes below lid)
    # We want to cut everything BELOW the line (P1-1.8) - (P2-1.8).
    lid_thickness = 1.8
    p1_low = (y_north_start, z_top_wall - lid_thickness)
    p2_low = (y_south, z_south - lid_thickness)
    
    cut_points_bottom = [
        (y_north_start, z_top_wall - lid_thickness),
        (y_south, z_south - lid_thickness),
        (y_south, 0), # Go down to 0
        (y_north_start, 0)
    ]
    
    # Extrude Cutters
    def make_cutter(pts):
        vec_pts = [FreeCAD.Vector(-x_width/2, p[0], p[1]) for p in pts] # Note: pts are (Y, Z)
        return cad_tools.create_prism_from_points(vec_pts, FreeCAD.Vector(x_width, 0, 0))
        
    cutter_top = make_cutter(cut_points_top)
    cutter_bottom = make_cutter(cut_points_bottom)
    
    # Apply cuts to Hex Prism
    lid_shape = hex_prism.cut(cutter_top)
    lid_shape = lid_shape.cut(cutter_bottom)
    
    # Now we have the sloped plate.
    # But wait! The lid is NOT fully sloped.
    # The Hub has a horizontal part (North of y_north_start) and a sloped part (South of y_north_start).
    # The user said: "Zuerst muss die Aussparung für den Horizontalen Deckel gemacht werden... Danach dann des Selbe für den schrägen Deckel."
    # This implies TWO separate lids? Or one complex lid?
    # "Es soll aber nur je ein Deckel erzeugt werden" -> "Only one lid of EACH type generated"?
    # Or "One lid total"?
    # Context: "Die Slots haben noch 2 Deckel, einen Horizontalen und einen für die abgeschrägte Fläche."
    # So we have 2 separate parts: Horizontal Lid and Sloped Lid.
    
    # My logic above for Horizontal Lid covered the WHOLE hexagon.
    # But the horizontal lid should only cover the horizontal part?
    # And the sloped lid the sloped part?
    # Or does the horizontal lid sit UNDER the sloped one?
    # Usually, if there is a slope cut, the "Horizontal Lid" covers the part that wasn't cut (the North part).
    # And the "Sloped Lid" covers the South part.
    
    # Let's assume they are split at y_north_start.
    
    # Refine Horizontal Lid:
    # Cut away everything South of y_north_start.
    # Refine Sloped Lid:
    # Cut away everything North of y_north_start.
    
    # Let's split them.
    
    # Splitter Box
    splitter = Part.makeBox(x_width, x_width, 50)
    splitter.translate(FreeCAD.Vector(-x_width/2, y_north_start, 0))
    # Splitter covers everything North of y_north_start.
    
    # Sloped Lid is South of y_north_start.
    # So we cut away the Splitter from the Sloped Lid.
    # Wait, Splitter is North. So Sloped Lid = Sloped_Shape.cut(Splitter).
    # But Splitter starts at y_north_start and goes +Y (North).
    # So cutting it removes the North part. Correct.
    lid_shape = lid_shape.cut(splitter)
    
    # Pillars for Sloped Lid
    # Vertical to floor.
    # Positions? Let's assume same X offsets (+/- 20) but Y centered on the slope?
    # Y center of slope is (y_south + y_north_start) / 2.
    y_center_slope = (y_south + y_north_start) / 2
    
    pillar_positions = [
        FreeCAD.Vector(-20, y_center_slope, 0),
        FreeCAD.Vector(20, y_center_slope, 0)
    ]
    
    pillar_outer_r = 6.0 / 2
    pillar_inner_r = 2.0 / 2
    
    # Calculate height for each pillar
    # Top of pillar touches bottom of lid.
    # Lid bottom Z at y_center_slope is:
    # z_at_y = z_top_wall - lid_thickness - (distance_from_start * tan(angle))
    # distance = y_north_start - y_center_slope
    dist = y_north_start - y_center_slope
    z_lid_bottom_at_pillar = (z_top_wall - lid_thickness) - (dist * math.tan(angle_from_horizontal_rad))
    
    pillar_len = z_lid_bottom_at_pillar - floor_height
    
    pillar_solid = Part.makeCylinder(pillar_outer_r, pillar_len)
    pillar_solid.translate(FreeCAD.Vector(0, 0, floor_height))
    
    for pos in pillar_positions:
        p = pillar_solid.copy()
        # Adjust height? No, we calculated for y_center_slope.
        # But wait, if X changes, Z doesn't change (slope is only in Y).
        # So both pillars have same height.
        p.translate(pos)
        lid_shape = lid_shape.fuse(p)
        
    # Cut Holes
    # Sackloch: Cut from floor_height upwards, length = pillar_len
    # Note: pillar_len was calculated for the center Y. 
    # Since slope is only in Y, and pillars are at same Y, they have same length.
    
    hole_cutter = Part.makeCylinder(pillar_inner_r, pillar_len)
    hole_cutter.translate(FreeCAD.Vector(0, 0, floor_height))
    
    for pos in pillar_positions:
        h = hole_cutter.copy()
        h.translate(pos)
        lid_shape = lid_shape.cut(h)

    return {
        "Lid_Sloped": {
            "shape": lid_shape,
            "color": (0.3, 0.3, 0.3)
        }
    }
