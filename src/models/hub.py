import FreeCAD
import Part
from lib import cad_tools

def create_model(params, global_dims, features={}):
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
    
    # 6. Mounting Holes
    # Parameters
    hole_count = 6
    hole_dist = 40.0
    hole_diameter = 2.4
    hole_radius = hole_diameter / 2
    chamfer_size = 0.8
    
    # Geometry for one hole cutter
    # 1. Straight hole (Cylinder)
    # Make it long enough to cut through the floor (2mm)
    cut_cyl = Part.makeCylinder(hole_radius, 10)
    
    # 2. Chamfer (Cone) at bottom (Z=0)
    # Chamfer 0.8mm means it goes from Radius + 0.8 to Radius over a height of 0.8
    chamfer_bottom_r = hole_radius + chamfer_size
    cut_cone = Part.makeCone(chamfer_bottom_r, hole_radius, chamfer_size)
    
    # Fuse to make a single cutter shape
    single_cutter = cut_cyl.fuse(cut_cone)
    
    # Position and Pattern
    # We need 6 holes arranged in a circle
    hole_cutters = []
    import math
    
    for i in range(hole_count):
        angle_deg = i * 60
        
        # Create a copy of the cutter
        cutter_copy = single_cutter.copy()
        
        # Move to radius (on X axis initially)
        cutter_copy.translate(FreeCAD.Vector(hole_dist, 0, 0))
        
        # Rotate around Z axis to final position
        # rotate(center, axis, angle)
        cutter_copy.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), angle_deg)
        
        hole_cutters.append(cutter_copy)
        
    # Fuse all cutters into one compound for efficient cutting
    if hole_cutters:
        all_holes = hole_cutters[0]
        for h in hole_cutters[1:]:
            all_holes = all_holes.fuse(h)
            
        # Cut from Hub
        hub_body = hub_body.cut(all_holes)
    
    # 7. Lid Recesses (Falz für Deckel)
    # Recess parameters
    recess_depth = 1.8 # From top edge downwards
    recess_width = 1.0 # From inner wall edge outwards
    
    # 7a. Horizontal Lid Recess
    # We need to cut away material from the inner top edge of the wall.
    # Strategy: Create a hexagonal prism that is slightly larger than the inner hole, 
    # and cut it away from the top.
    
    # Inner hole flat-to-flat was: inner_flat_to_flat
    # Recess starts at inner edge and goes 1mm into the wall.
    # So the cutter diameter (flat-to-flat) is: inner_flat_to_flat + 2 * recess_width
    recess_flat_to_flat = inner_flat_to_flat + (2 * recess_width)
    
    # Create the cutter prism
    # It needs to be positioned at the top of the wall.
    # Total height at top is z_top = floor_height + wall_height
    # Cutter height is recess_depth.
    # Z position is z_top - recess_depth
    
    # However, we have already cut the slope! 
    # If we cut the recess now, it will follow the horizontal plane.
    # The user says: "Zuerst muss die Aussparung für den Horizontalen Deckel gemacht werden... Danach dann des Selbe für den schrägen Deckel."
    # This implies we cut the recess into the *current* geometry.
    
    # Horizontal Recess Cutter
    recess_cutter_horiz = cad_tools.create_hexagon(recess_flat_to_flat, recess_depth)
    
    # The inner part of this cutter is empty space (we only want to cut the rim).
    # Actually, if we just use a solid hexagon of size (inner + 2*width), and cut it, 
    # it will cut the air inside the hub (no problem) and the 1mm rim of the wall.
    # That works.
    
    # Position it
    z_recess_start = (floor_height + wall_height) - recess_depth
    recess_cutter_horiz.translate(FreeCAD.Vector(0, 0, z_recess_start))
    
    # Apply Horizontal Recess Cut
    hub_body = hub_body.cut(recess_cutter_horiz)
    
    # 7b. Sloped Lid Recess
    # Now we need a recess that follows the slope we created in step 5.
    # The slope cut was defined by 'cutter' (the big prism).
    # We need to cut 1.8mm "deeper" (perpendicular to slope? or vertical?)
    # User says "von der Wandoberkannte ist diese 1.8 mm tief". Usually for lids this means vertical depth Z.
    # And "1mm von der Wandinnenkante".
    
    # Strategy:
    # We can reuse the slope cutter logic but shift it downwards by 1.8mm?
    # No, that would cut the whole top off.
    # We need to cut a "step" into the sloped surface.
    
    # Let's construct a cutter that represents the volume of the lid.
    # The lid sits on the recess.
    # So we need a shape that is:
    # - Bounded by the inner wall (plus 1mm outwards)
    # - Bounded by the slope plane (but 1.8mm lower?)
    
    # Actually, the simplest way to think about it:
    # The slope cut (Step 5) defined the top surface.
    # Now we want to lower that surface by 1.8mm, BUT ONLY in the region [InnerWall, InnerWall+1mm].
    
    # Let's create a "Recess Zone" prism:
    # A hexagonal ring of thickness 1mm (from inner_flat_to_flat to recess_flat_to_flat).
    # Height: Full height.
    recess_zone_outer = cad_tools.create_hexagon(recess_flat_to_flat, 30) # High enough
    recess_zone_inner = cad_tools.create_hexagon(inner_flat_to_flat, 30)
    recess_ring = recess_zone_outer.cut(recess_zone_inner)
    
    # Now we need to trim this ring to the correct height.
    # The top of the ring should be the current top surface MINUS 1.8mm.
    # Wait, if we cut the recess, the "shelf" for the lid is 1.8mm below the top surface.
    # So we want to remove material from the current top surface down to (Top - 1.8mm).
    
    # Let's try this:
    # 1. Take the Slope Cutter from Step 5.
    # 2. Move it DOWN by 1.8mm (Z-1.8).
    # 3. Intersect it with the "Recess Ring" (the 1mm wide zone).
    # This gives us a shape that represents the volume to be removed for the sloped recess?
    # No, the slope cutter removes everything ABOVE.
    # If we move it down, it covers the volume we want to remove (plus more).
    # So:
    # Cutter_Down = Slope_Cutter.translated(0, 0, -1.8)
    # Recess_Volume = Cutter_Down.common(Recess_Ring)
    # Hub = Hub.cut(Recess_Volume)
    
    # But wait, we also have the horizontal part.
    # The horizontal recess was already cut.
    # The slope recess needs to handle the sloped part.
    
    # Let's recreate the slope cutter (we didn't keep it in a variable accessible here, so let's rebuild or move logic).
    # Ideally, we should have defined the recess BEFORE the slope cut?
    # No, the recess follows the slope.
    
    # Let's rebuild the slope cutter geometry for the recess.
    # We used 'cutter' in Step 5.
    # We need a cutter that is 1.8mm lower.
    
    # Re-calculate points for slope cutter (shifted down by recess_depth)
    cut_points_recess = []
    for p in cut_points: # cut_points from Step 5
        # Shift Z down by recess_depth
        cut_points_recess.append((p[0], p[1], p[2] - recess_depth))
        
    cut_points_shifted_recess = []
    for p in cut_points_recess:
        cut_points_shifted_recess.append(FreeCAD.Vector(-x_width/2, p[1], p[2]))
        
    slope_cutter_lower = cad_tools.create_prism_from_points(cut_points_shifted_recess, FreeCAD.Vector(x_width, 0, 0))
    
    # Now intersect this "Lower Slope Cutter" with the "Recess Ring"
    # Recess Ring needs to be placed correctly (it was created at Z=0).
    # It needs to go up to at least the top of the wall.
    # recess_ring is 30mm high, created at Z=0.
    # Our wall is 2+14=16mm high. So it covers it.
    
    # The volume to cut is: The intersection of (Everything above the Lower Slope Plane) AND (The 1mm Ring).
    # slope_cutter_lower is "Everything above the Lower Slope Plane".
    recess_cut_volume = slope_cutter_lower.common(recess_ring)
    
    # Apply the cut
    hub_body = hub_body.cut(recess_cut_volume)
    
    # 8. Spacer Rim (Abstandsrand)
    # 0.5mm thick, 10mm high, around the outer wall.
    rim_thickness = 0.5
    rim_height = 10.0
    
    # Outer dimension of the rim
    rim_flat_to_flat_outer = outer_flat_to_flat + (2 * rim_thickness)
    
    # Create Rim Geometry
    rim_outer_shape = cad_tools.create_hexagon(rim_flat_to_flat_outer, rim_height)
    rim_inner_shape = cad_tools.create_hexagon(outer_flat_to_flat, rim_height)
    
    rim_shape = rim_outer_shape.cut(rim_inner_shape)
    
    # Fuse to Hub
    hub_body = hub_body.fuse(rim_shape)
    
    # 9. Magnet Pillars (Magnetpfeiler)
    # Parameters
    # Radius from center to outer pillars
    magnet_dist = global_dims['system']['magnet_mounting_radius_mm']
    
    # Pillar dimensions
    # Inner diameter 10.1mm -> Radius 5.05mm
    mag_inner_r = 10.1 / 2
    # Wall thickness 0.85mm
    mag_wall_thick = 0.85
    # Outer diameter = 10.1 + 2*0.85 = 11.8mm -> Radius 5.9mm
    mag_outer_r = mag_inner_r + mag_wall_thick
    
    # Heights
    # "11,2mm hoch. Das ist die Fläche wo der Magnet aufliegt."
    # So the solid cylinder goes up to Z=11.2
    mag_base_height = 11.2
    
    # "Rand um den Magneten ... 2mm Höhe"
    # This rim sits ON TOP of the base height? Or is the total height 11.2 + 2?
    # Usually "Rand ... 2mm Höhe" implies it protrudes 2mm above the seating surface.
    mag_rim_height = 2.0
    
    # Geometry Construction for ONE Pillar
    # 1. Base Cylinder (Solid)
    # Radius = Outer Radius (11.8mm)
    # Height = Base Height (11.2mm)
    # Note: It sits on the floor (Z=2mm) or starts at Z=0?
    # "Pfeiler" usually implies starting from the bottom.
    # If the floor is 2mm thick, and the pillar is 11.2mm high, does it mean 11.2mm from Z=0 or from Z=2?
    # Usually absolute height from Z=0 is meant in mechanical design unless specified "above floor".
    # Let's assume 11.2mm is the Z-coordinate of the seating surface.
    # Since the floor is at Z=0..2, the pillar goes from Z=0 to Z=11.2.
    # CORRECTION: User says "Das Mass darf nicht ab dem Boden unten außen gemessen werden sondern im Inneren des Slot".
    # This means the height 11.2mm is FROM THE INNER FLOOR (Z=2.0).
    # So the pillar sits on Z=2.0 and has a length of 11.2mm.
    
    pillar_base = Part.makeCylinder(mag_outer_r, mag_base_height)
    pillar_base.translate(FreeCAD.Vector(0, 0, floor_height)) # Move up to sit on floor
    
    # 2. Rim (Hollow Cylinder)
    # Sits on top of base (Z = floor_height + mag_base_height)
    # Height = 2.0
    rim_outer = Part.makeCylinder(mag_outer_r, mag_rim_height)
    rim_inner = Part.makeCylinder(mag_inner_r, mag_rim_height)
    pillar_rim = rim_outer.cut(rim_inner)
    pillar_rim.translate(FreeCAD.Vector(0, 0, floor_height + mag_base_height))
    
    # Fuse Base and Rim
    single_pillar = pillar_base.fuse(pillar_rim)
    
    # Positions
    # 1. Center Pillar (0,0)
    # 2. North Pillar (0, magnet_dist) -> Angle 90 deg?
    # User says: "einer nach Norden" -> Y-Axis positive?
    # "die beiden Anderen jeweils 60Grad rechts und Links davon"
    # North is 90 deg (if X is East).
    # Left of North (+60) = 150 deg.
    # Right of North (-60) = 30 deg.
    
    # Let's verify coordinates.
    # North: (0, 33.5)
    # +60 deg from North: Rotate (0, 33.5) by 60 deg around Z.
    # -60 deg from North: Rotate (0, 33.5) by -60 deg around Z.
    
    pillar_positions = [
        FreeCAD.Vector(0, 0, 0), # Center
        FreeCAD.Vector(0, magnet_dist, 0) # North
    ]
    
    # Calculate the other two
    import math
    # North vector
    v_north = FreeCAD.Vector(0, magnet_dist, 0)
    
    # Rotate +60 (Left)
    m = FreeCAD.Matrix()
    m.rotateZ(math.radians(60))
    v_left = m.multVec(v_north) # multVec is the correct method in FreeCAD Python API
    pillar_positions.append(v_left)
    
    # Rotate -60 (Right)
    m = FreeCAD.Matrix()
    m.rotateZ(math.radians(-60))
    v_right = m.multVec(v_north)
    pillar_positions.append(v_right)
    
    # Place and Fuse Pillars
    all_pillars = []
    for pos in pillar_positions:
        p = single_pillar.copy()
        p.translate(pos)
        all_pillars.append(p)
        
    # Fuse all pillars to Hub
    for p in all_pillars:
        hub_body = hub_body.fuse(p)
        
    # 10. PogoPin PCB Pillars
    # Dimensions
    pogo_outer_r = 5.0 / 2
    pogo_hole_r = 2.0 / 2
    pogo_height = 9.7 # Length of pillar sitting on floor
    
    # Positions
    # Reference line Y = 16.65
    y_ref = 16.65
    y_offset = 7.5
    
    # X offsets
    x_left = -6.0
    x_right = 5.0
    
    # Coordinates (X, Y)
    pogo_positions = [
        FreeCAD.Vector(x_left, y_ref + y_offset, 0),  # Top-Left
        FreeCAD.Vector(x_left, y_ref - y_offset, 0),  # Bottom-Left
        FreeCAD.Vector(x_right, y_ref + y_offset, 0), # Top-Right
        FreeCAD.Vector(x_right, y_ref - y_offset, 0)  # Bottom-Right
    ]
    
    # Create Geometry
    # We create solid pillars first, fuse them, then cut the holes.
    
    # Solid Pillar
    # Sits on floor (Z=2.0)
    pogo_pillar_solid = Part.makeCylinder(pogo_outer_r, pogo_height)
    pogo_pillar_solid.translate(FreeCAD.Vector(0, 0, floor_height))
    
    # Fuse pillars
    for pos in pogo_positions:
        p = pogo_pillar_solid.copy()
        p.translate(pos)
        hub_body = hub_body.fuse(p)
        
    # Cut Holes
    # Through hole means through pillar AND floor? 
    # User Request: "nicht durchgehend" (Sackloch).
    # So we cut from floor_height upwards.
    hole_cutter_shape = Part.makeCylinder(pogo_hole_r, pogo_height + 5) # Length covers pillar
    hole_cutter_shape.translate(FreeCAD.Vector(0, 0, floor_height)) # Start at floor top
    
    # Combine all hole cutters
    all_pogo_holes = []
    for pos in pogo_positions:
        h = hole_cutter_shape.copy()
        h.translate(pos)
        all_pogo_holes.append(h)
        
    if all_pogo_holes:
        combined_holes = all_pogo_holes[0]
        for h in all_pogo_holes[1:]:
            combined_holes = combined_holes.fuse(h)
            
        hub_body = hub_body.cut(combined_holes)
    
    # 11. Hub Controller PCB Pillars (Optional Feature)
    if features.get('controller_mounts', False):
        # Dimensions
        ctrl_outer_r = 5.0 / 2
        ctrl_hole_r = 2.0 / 2
        ctrl_height = 5.0 # Height from inner floor
        
        # Positions (X, Y) based on user image
        ctrl_positions = [
            FreeCAD.Vector(-16, 28, 0),  # Top-Left
            FreeCAD.Vector(16, 28, 0),   # Top-Right
            FreeCAD.Vector(-32, 0, 0),   # Mid-Left
            FreeCAD.Vector(32, 0, 0),    # Mid-Right
            FreeCAD.Vector(-17, -26, 0), # Bottom-Left
            FreeCAD.Vector(17, -26, 0)   # Bottom-Right
        ]
        
        # Create Geometry
        # Solid Pillar sitting on floor (Z=2.0)
        ctrl_pillar_solid = Part.makeCylinder(ctrl_outer_r, ctrl_height)
        ctrl_pillar_solid.translate(FreeCAD.Vector(0, 0, floor_height))
        
        # Fuse pillars
        for pos in ctrl_positions:
            p = ctrl_pillar_solid.copy()
            p.translate(pos)
            hub_body = hub_body.fuse(p)
            
        # Cut Holes
        # User Request: Sackloch (not through floor)
        ctrl_hole_cutter = Part.makeCylinder(ctrl_hole_r, ctrl_height + 5)
        ctrl_hole_cutter.translate(FreeCAD.Vector(0, 0, floor_height))
        
        all_ctrl_holes = []
        for pos in ctrl_positions:
            h = ctrl_hole_cutter.copy()
            h.translate(pos)
            all_ctrl_holes.append(h)
            
        if all_ctrl_holes:
            combined_ctrl_holes = all_ctrl_holes[0]
            for h in all_ctrl_holes[1:]:
                combined_ctrl_holes = combined_ctrl_holes.fuse(h)
                
            hub_body = hub_body.cut(combined_ctrl_holes)
            
    # 12. South PCB Pillars (Südliche Platine)
    if features.get('usb_mounts', False):
        # 4 Pillars, Square 14mm, Symmetric to Y-axis.
        # South pillars 3mm from inner south wall.
        
        # Calculate Y position of inner south wall
        # inner_flat_to_flat was calculated earlier
        # Y_south_wall = -inner_flat_to_flat / 2
        y_south_wall_inner = -inner_flat_to_flat / 2
        
        y_south_pillars = y_south_wall_inner + 3.0
        y_north_pillars = y_south_pillars + 14.0
        
        x_offset = 14.0 / 2 # 7.0
        
        south_pcb_positions = [
            FreeCAD.Vector(-x_offset, y_north_pillars, 0), # Top-Left
            FreeCAD.Vector(x_offset, y_north_pillars, 0),  # Top-Right
            FreeCAD.Vector(-x_offset, y_south_pillars, 0), # Bottom-Left
            FreeCAD.Vector(x_offset, y_south_pillars, 0)   # Bottom-Right
        ]
        
        # Dimensions
        spcb_outer_r = 4.0 / 2
        spcb_inner_r = 2.0 / 2
        spcb_height = 2.0 # Height above floor
        
        # Create Pillars
        # Solid cylinder from Z=2.0 to Z=4.0
        spcb_pillar_solid = Part.makeCylinder(spcb_outer_r, spcb_height)
        spcb_pillar_solid.translate(FreeCAD.Vector(0, 0, floor_height))
        
        for pos in south_pcb_positions:
            p = spcb_pillar_solid.copy()
            p.translate(pos)
            hub_body = hub_body.fuse(p)
            
        # Cut Holes
        # "Bohrung auch in 1mm in den Boden gehen"
        # Floor is Z=0 to Z=2.
        # Hole should go down to Z=1.0.
        # Top of hole is Z=4.0.
        # Length = 3.0mm (plus extra for safety at top).
        
        spcb_hole_cutter = Part.makeCylinder(spcb_inner_r, spcb_height + 1.0 + 5.0) # Enough length
        spcb_hole_cutter.translate(FreeCAD.Vector(0, 0, 1.0)) # Start at Z=1.0
        
        all_spcb_holes = []
        for pos in south_pcb_positions:
            h = spcb_hole_cutter.copy()
            h.translate(pos)
            all_spcb_holes.append(h)
            
        if all_spcb_holes:
            combined_spcb_holes = all_spcb_holes[0]
            for h in all_spcb_holes[1:]:
                combined_spcb_holes = combined_spcb_holes.fuse(h)
                
            hub_body = hub_body.cut(combined_spcb_holes)
            
        # 13. South Wall Cutout (Aussparung Südliche Wand)
        # Rectangle 13x7mm, Radius 2mm.
        # Centered in Width (X=0).
        # Height: 1.5mm material remaining at the top.
        # The top of the wall at the South face is z_south (calculated in Slope section).
        # If slope is not active (unlikely for this specific request), we use z_top_wall.
        
        # Recalculate z_south to be sure (or use variables if scope allows, but safer to recalc)
        slope_length_y = 29.0
        slope_angle_deg = 80.0
        z_top_wall = floor_height + wall_height
        angle_from_horizontal_rad = math.radians(90 - slope_angle_deg)
        delta_z = slope_length_y * math.tan(angle_from_horizontal_rad)
        z_south = z_top_wall - delta_z
        
        cutout_w = 13.0
        cutout_h = 7.0
        cutout_r = 2.0
        material_above = 2.0 # Changed from 1.5
        
        cutout_top_z = z_south - material_above
        cutout_bottom_z = cutout_top_z - cutout_h
        
        # Create Cutter Box
        # We need to cut through the wall but NOT hit the pillars inside.
        # Wall thickness is 2.4mm. Pillars are 3mm away from inner wall.
        # So we have plenty of space if we are careful.
        # Let's cut from outside inwards, stopping just after the inner wall.
        
        y_south_outer = -outer_flat_to_flat / 2
        y_south_inner = y_south_outer + wall_thickness
        
        # Cutter Y range: Start 1mm outside, End 0.5mm inside (to ensure clean cut)
        y_cut_start = y_south_outer - 1.0
        y_cut_end = y_south_inner + 0.5
        cutout_depth = y_cut_end - y_cut_start
        
        cutout_box = Part.makeBox(cutout_w, cutout_depth, cutout_h)
        
        # Position
        # X: Centered -> -w/2
        # Y: y_cut_start
        # Z: cutout_bottom_z
        
        cutout_box.translate(FreeCAD.Vector(-cutout_w/2, y_cut_start, cutout_bottom_z))
        
        # Fillet edges parallel to Y
        edges_to_fillet = []
        for edge in cutout_box.Edges:
            # Check if edge is parallel to Y
            tangent = edge.tangentAt(edge.FirstParameter)
            if abs(tangent.y) > 0.99: # Parallel to Y
                edges_to_fillet.append(edge)
                
        if edges_to_fillet:
            cutout_box = cutout_box.makeFillet(cutout_r, edges_to_fillet)
            
        hub_body = hub_body.cut(cutout_box)
    
    return {
        "Hub_Body": {
            "shape": hub_body,
            "color": (0.9, 0.9, 0.9) # Light Grey
        }
    }
