import FreeCAD
import Part
import math
from lib import cad_tools

def create_model():
    """
    Creates the Kachelboden model.
    """
    # Dimensions
    flat_to_flat = 81.0
    height = 2.2
    
    magnet_dist = 33.5
    magnet_dia = 10.0
    magnet_depth = 1.8
    
    rect_width = 5.6
    rect_length = 17.9
    rect_bottom_dist = 7.7
    
    # 1. Base Hexagon
    # cad_tools.create_hexagon creates pointy sides at X-axis (0 deg).
    # Edges are at 90, 150, 210, 270, 330, 30.
    body = cad_tools.create_hexagon(flat_to_flat, height)
    
    # 2. Magnets
    # Center
    center_magnet = Part.makeCylinder(magnet_dia/2, magnet_depth)
    center_magnet.translate(FreeCAD.Vector(0, 0, height - magnet_depth))
    body = body.cut(center_magnet)
    
    # Radial Magnets (6x)
    # Aligned with edges (90, 150, etc.)
    # Angles: 30, 90, 150, 210, 270, 330
    angles = [30, 90, 150, 210, 270, 330]
    
    magnet_cutter = Part.makeCylinder(magnet_dia/2, magnet_depth)
    magnet_cutter.translate(FreeCAD.Vector(0, 0, height - magnet_depth))
    
    for angle in angles:
        m = magnet_cutter.copy()
        # Translate to distance along Y (North) then rotate
        # Or just calculate position
        rad = math.radians(angle)
        x = magnet_dist * math.cos(rad)
        y = magnet_dist * math.sin(rad)
        m.translate(FreeCAD.Vector(x, y, 0))
        body = body.cut(m)
        
    # 3. Rectangular Cutouts
    # "6 Stück mit dem ersten direkt nach Norden zur Kante 1 zeigend."
    # North is 90 degrees.
    # "Untere Kante des Rechtecks hat einen Abstand von 7.7 mm."
    # We create one at North and rotate it.
    
    # Rectangle at North (aligned with Y axis)
    # Width (X) = 5.6
    # Length (Y) = 17.9
    # Bottom (Y) = 7.7
    # Z = through hole (height + extra)
    
    cutout_shape = Part.makeBox(rect_width, rect_length, height + 2.0)
    # Center X
    cutout_shape.translate(FreeCAD.Vector(-rect_width/2, 0, 0))
    # Move Y to start at 7.7
    cutout_shape.translate(FreeCAD.Vector(0, rect_bottom_dist, 0))
    # Move Z to -1.0 to cut through
    cutout_shape.translate(FreeCAD.Vector(0, 0, -1.0))
    
    # Rotate for all 6 positions
    # Angles same as magnets (aligned to edges)
    # North is 90.
    # The box is created along +Y (which is 90 deg).
    # So for 90 deg, we rotate by 0 relative to creation?
    # Wait, creation is along +Y.
    # If we want it at 90, it's already there.
    # If we want it at 30, we rotate by -60?
    # Let's just create it at +X (0 deg) and rotate by angles.
    
    # Re-create at +X (0 deg)
    # Length along X, Width along Y
    cutout_shape_x = Part.makeBox(rect_length, rect_width, height + 2.0)
    cutout_shape_x.translate(FreeCAD.Vector(0, -rect_width/2, -1.0))
    cutout_shape_x.translate(FreeCAD.Vector(rect_bottom_dist, 0, 0))
    
    # Now rotate by angles
    # Angles: 30, 90, 150, 210, 270, 330
    for angle in angles:
        c = cutout_shape_x.copy()
        c.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), angle)
        body = body.cut(c)
        
    # 4. Mounting Bolts
    # 6x, alternating variants.
    # Position: Towards corners (0, 60, 120...), distance 35mm.
    # Height: 1.5mm above floor (Z = height + 1.5 = 3.7)
    
    bolt_dist = 35.0
    bolt_outer_r = 5.0 / 2
    bolt_height_above = 1.5
    bolt_z_top = height + bolt_height_above
    
    # Variant 1: 2.5mm through hole, 0.8mm bottom chamfer
    v1_hole_r = 2.5 / 2
    v1_chamfer = 0.8
    
    # Variant 2: 2.0mm blind hole, 0.2mm top chamfer
    v2_hole_r = 2.0 / 2
    v2_chamfer = 0.2
    v2_hole_bottom = 0.4 # 0.4mm above Z=0
    
    for i in range(6):
        angle = i * 60
        rad = math.radians(angle)
        x = bolt_dist * math.cos(rad)
        y = bolt_dist * math.sin(rad)
        pos = FreeCAD.Vector(x, y, 0)
        
        # Base Bolt Solid
        # Cylinder from Z=height to Z=bolt_z_top
        # Actually, we can just fuse a cylinder at Z=height
        bolt = Part.makeCylinder(bolt_outer_r, bolt_height_above)
        bolt.translate(FreeCAD.Vector(0, 0, height))
        bolt.translate(pos)
        body = body.fuse(bolt)
        
        # Hole
        if i % 2 == 0:
            # Variant 1 (Even: 0, 2, 4)
            # Through hole
            # Create negative shape for chamfer + hole
            
            # Chamfer at bottom (Cone)
            # Height 0.8
            # Bottom R = 1.25 + 0.8 = 2.05
            # Top R = 1.25
            chamfer_cone = Part.makeCone(v1_hole_r + v1_chamfer, v1_hole_r, v1_chamfer)
            
            # Hole Cylinder (rest of the way up)
            # From Z=0.8 to Z=bolt_z_top + 1.0 (clearance)
            hole_cyl = Part.makeCylinder(v1_hole_r, bolt_z_top + 1.0)
            hole_cyl.translate(FreeCAD.Vector(0, 0, v1_chamfer))
            
            cutter = chamfer_cone.fuse(hole_cyl)
            cutter.translate(pos)
            body = body.cut(cutter)
            
        else:
            # Variant 2 (Odd: 1, 3, 5)
            # Blind hole from Z=0.4 up
            # Chamfer at top
            
            # Hole Cylinder
            # From Z=0.4 to Z=bolt_z_top - 0.2
            cyl_height = (bolt_z_top - v2_chamfer) - v2_hole_bottom
            hole_cyl = Part.makeCylinder(v2_hole_r, cyl_height)
            hole_cyl.translate(FreeCAD.Vector(0, 0, v2_hole_bottom))
            
            # Chamfer at top (Cone)
            # Height 0.2
            # Bottom R = 1.0
            # Top R = 1.0 + 0.2 = 1.2
            # Starts at Z = bolt_z_top - 0.2
            chamfer_cone = Part.makeCone(v2_hole_r, v2_hole_r + v2_chamfer, v2_chamfer)
            chamfer_cone.translate(FreeCAD.Vector(0, 0, bolt_z_top - v2_chamfer))
            
            cutter = hole_cyl.fuse(chamfer_cone)
            cutter.translate(pos)
            body = body.cut(cutter)
        
    return body
