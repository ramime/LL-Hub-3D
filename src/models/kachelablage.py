import FreeCAD
import Part
import math
from lib import cad_tools

def create_model():
    """
    Creates the Kachelablage (Tile Tray) model.
    """
    # Parameters
    tile_edge = 49.0
    tile_thickness = 12.0
    
    # Tray parameters
    tray_height = 30.0
    tray_wall_thickness = 3.0 # Wall thickness around the tile
    tray_floor_thickness = 3.0 # Thickness below the tile (in profile)
    
    # Spacing parameters
    tile_gap = 20.0
    pitch = tile_thickness + tile_gap # 32mm
    
    tray_depth = pitch 
    
    tilt_angle = 20.0 # degrees
    
    base_width = 100.0
    base_thickness = 3.0
    
    num_trays = 3
    
    # 1. Create the Tray Profile (Cross-section in XZ plane)
    
    # Inner Profile (Tile shape)
    # Bottom width = 49.0
    # Height = tray_height
    # Angle = 60 degrees
    
    p1_in = FreeCAD.Vector(-tile_edge/2, 0, tray_floor_thickness)
    p2_in = FreeCAD.Vector(tile_edge/2, 0, tray_floor_thickness)
    
    dx_in = tray_height / math.tan(math.radians(60))
    
    p3_in = FreeCAD.Vector(tile_edge/2 + dx_in, 0, tray_floor_thickness + tray_height)
    p4_in = FreeCAD.Vector(-tile_edge/2 - dx_in, 0, tray_floor_thickness + tray_height)
    
    inner_wire = Part.makePolygon([p1_in, p2_in, p3_in, p4_in, p1_in])
    inner_face = Part.Face(inner_wire)
    
    # Extrude inner face to create the cutout volume
    cutout_thickness = tile_thickness + 1.0 # Tolerance
    cutout_solid = inner_face.extrude(FreeCAD.Vector(0, cutout_thickness, 0))
    
    # Center the cutout in Y relative to the tray depth
    y_offset = (tray_depth - cutout_thickness) / 2
    cutout_solid.translate(FreeCAD.Vector(0, y_offset, 0))
    
    
    # 2. Create the Outer Tray Body
    # We extend the outer profile downwards significantly to ensure that after tilting,
    # we still have material reaching the base plate.
    
    extra_depth = 20.0 # Extend down by 20mm
    
    dx_wall = tray_wall_thickness / math.sin(math.radians(60))
    
    # Outer Points
    # Bottom is at Z = -extra_depth
    p1_out = FreeCAD.Vector(-tile_edge/2 - dx_wall, 0, -extra_depth)
    p2_out = FreeCAD.Vector(tile_edge/2 + dx_wall, 0, -extra_depth)
    
    # Top Points
    # Same top height as before
    total_height = tray_floor_thickness + tray_height
    # Calculate X at top for outer wall
    # We want constant wall thickness.
    # The outer wall is parallel to inner wall.
    # Inner wall passes through (edge/2, floor) and (edge/2+dx, floor+height).
    # Outer wall is shifted by dx_wall in X (at same Z? No, perpendicular distance).
    # But here we just offset X by dx_wall at the bottom (Z=0 originally).
    # Let's keep the simple logic: Top X is calculated from Bottom X with 60 deg slope.
    
    # Height from -extra_depth to total_height
    full_height = total_height + extra_depth
    dx_total = full_height / math.tan(math.radians(60))
    
    p3_out = FreeCAD.Vector(p2_out.x + dx_total, 0, total_height)
    p4_out = FreeCAD.Vector(p1_out.x - dx_total, 0, total_height)
    
    outer_wire = Part.makePolygon([p1_out, p2_out, p3_out, p4_out, p1_out])
    outer_face = Part.Face(outer_wire)
    
    # Extrude outer face
    tray_block = outer_face.extrude(FreeCAD.Vector(0, tray_depth, 0))
    
    # Cut the slot
    tray = tray_block.cut(cutout_solid)
    
    
    # 3. Tilt the Tray
    # Rotate around X axis by -20 degrees (to tilt back)
    tray.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0), -tilt_angle)
    
    
    # 4. Calculate Z-Shift
    # We want the lowest point of the slot floor to be at Z = base_thickness.
    # Slot floor in profile is at Z = tray_floor_thickness (3.0).
    # Slot extends in Y from y_offset to y_offset + cutout_thickness.
    # Y_end = y_offset + cutout_thickness.
    y_end = y_offset + cutout_thickness
    
    # Z of slot floor at Y_end after rotation:
    # Z_rot = Y * sin(-angle) + Z_orig * cos(-angle)
    rad_angle = math.radians(tilt_angle)
    # Note: rotate(-20) means angle is -20.
    sin_a = math.sin(-rad_angle)
    cos_a = math.cos(-rad_angle)
    
    z_slot_lowest = y_end * sin_a + tray_floor_thickness * cos_a
    
    # We want this to be at Z = base_thickness
    # Shift = Target - Current
    z_shift = base_thickness - z_slot_lowest
    
    
    # 5. Create Assembly of Trays
    trays = []
    
    # Y-Shift for stacking
    # We stack them such that the "front" of the next tray is at the "back" of the previous tray?
    # Or based on pitch?
    # "Abstand von 20mm". Pitch = 32mm.
    # If we shift by `pitch` along the tilted axis?
    # No, we shift along Y (horizontal on the table).
    # The trays are identical.
    # If we shift by Y_step, the distance between corresponding points is Y_step.
    # We want the distance between the tiles to be `pitch`.
    # Since tiles are tilted, the perpendicular distance is what matters?
    # Or just the horizontal spacing?
    # "Kacheln sollen einen Abstand von 20mm haben".
    # Usually this means the gap between them.
    # If tiles are 12mm thick. Gap 20mm. Pitch = 32mm.
    # If we place them with Y-spacing = 32mm / cos(20)?
    # Or just 32mm?
    # If we assume the user means "Distance along the stacking direction", and stacking is horizontal.
    # Let's use Y_shift = pitch / cos(20).
    # This ensures the perpendicular distance between the planes of the tiles is `pitch`.
    # Distance_perp = Y_shift * cos(20).
    # So Y_shift = 32 / cos(20) = 34.05mm.
    
    y_shift_stack = pitch / math.cos(rad_angle)
    
    final_trays = None
    
    for i in range(num_trays):
        t = tray.copy()
        # Shift in Y
        t.translate(FreeCAD.Vector(0, i * y_shift_stack, 0))
        # Lift to correct height
        t.translate(FreeCAD.Vector(0, 0, z_shift))
        
        if final_trays is None:
            final_trays = t
        else:
            final_trays = final_trays.fuse(t)
            
            
    # 6. Cut the Trays at Base Plate Level
    # We want to remove everything below Z = base_thickness.
    # Create a large box below Z=3.
    
    # Bounding box to know size
    bbox = final_trays.BoundBox
    
    cut_box = Part.makeBox(bbox.XLength + 20, bbox.YLength + 20, 100) # Height 100
    # Position it so top face is at Z=base_thickness
    cut_box.translate(FreeCAD.Vector(bbox.XMin - 10, bbox.YMin - 10, base_thickness - 100))
    
    final_trays_cut = final_trays.cut(cut_box)
    
    
    # 7. Create Base Plate
    # Width = 100mm
    # Thickness = 3mm
    # Length covers the trays.
    
    bbox_cut = final_trays_cut.BoundBox
    min_y = bbox_cut.YMin
    max_y = bbox_cut.YMax
    
    padding = 10.0
    plate_length = (max_y - min_y) + 2 * padding
    
    plate = Part.makeBox(base_width, plate_length, base_thickness)
    
    # Center X
    plate.translate(FreeCAD.Vector(-base_width/2, 0, 0))
    # Align Y
    plate.translate(FreeCAD.Vector(0, min_y - padding, 0))
    
    # Fuse everything
    final_model = final_trays_cut.fuse(plate)
    
    return final_model
