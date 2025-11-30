import FreeCAD
import Part
from lib import cad_tools

def create_pogo_pin_attachment():
    """
    Creates the PogoPinAufsatz part.
    Dimensions:
    X: -10 to 7.5
    Y: -10 to 10
    Z: 0 to 0.8
    """
    
    # Define the base rectangle points
    x_min = -10.0
    x_max = 7.5
    y_min = -10.0
    y_max = 10.0
    height = 0.8
    
    # Create box using makeBox and translate
    # makeBox creates from (0,0,0) to (L, W, H)
    length = x_max - x_min
    width = y_max - y_min
    
    box = Part.makeBox(length, width, height)
    
    # Translate to correct position
    # The box starts at (0,0,0), we want it at (x_min, y_min, 0)
    box.translate(FreeCAD.Vector(x_min, y_min, 0))
    
    # --- Holes ---
    # Diameter 2.3mm -> Radius 1.15mm
    # Chamfer 0.8mm at top.
    # Since plate height is 0.8mm, the hole is a cone from r=1.15 to r=1.15+0.8=1.95
    
    hole_radius = 2.3 / 2.0
    chamfer_size = 0.8
    top_radius = hole_radius + chamfer_size
    
    # Hole positions (centers)
    # Rectangle edges: x=-6, x=5, y=-7.5, y=7.5
    hole_positions = [
        FreeCAD.Vector(-6.0, -7.5, 0),
        FreeCAD.Vector( 5.0, -7.5, 0),
        FreeCAD.Vector( 5.0,  7.5, 0),
        FreeCAD.Vector(-6.0,  7.5, 0)
    ]
    
    holes = []
    for pos in hole_positions:
        # Create cone: Radius1 (bottom), Radius2 (top), Height
        # Part.makeCone(radius1, radius2, height)
        cone = Part.makeCone(hole_radius, top_radius, height)
        cone.translate(pos)
        holes.append(cone)
        
    # Cut holes from box
    if holes:
        fused_holes = holes[0]
        for h in holes[1:]:
            fused_holes = fused_holes.fuse(h)
        
        base_plate = box.cut(fused_holes)
    else:
        base_plate = box
        
    # --- Top Block (Aufsatz) ---
    # Dimensions:
    # X: +/- 2.15
    # Y: +/- 8.45
    # Height: 4.5mm above base plate (starts at 0.8, ends at 0.8 + 4.5 = 5.3)
    
    block_x_half = 2.15
    block_y_half = 8.45
    block_height = 4.5
    
    block_shape = Part.makeBox(block_x_half * 2, block_y_half * 2, block_height)
    # Center the block in X and Y, and place on top of base (Z=0.8)
    block_shape.translate(FreeCAD.Vector(-block_x_half, -block_y_half, height))
    
    # Fillet the top block
    # We want to fillet vertical edges and top edges.
    # We should avoid the bottom edges (z=height=0.8) to ensure clean fusion.
    fillet_radius = 0.6
    edges_to_fillet = []
    for edge in block_shape.Edges:
        # Check Z height of the edge center
        # The block goes from Z=0.8 to Z=5.3
        # Edges at Z=0.8 are the bottom ones.
        # We want everything else.
        z_center = (edge.Vertexes[0].Point.z + edge.Vertexes[1].Point.z) / 2.0
        if z_center > (height + 0.01): # Slightly above 0.8
            edges_to_fillet.append(edge)
            
    if edges_to_fillet:
        block_shape = block_shape.makeFillet(fillet_radius, edges_to_fillet)
    
    # Fuse Base and Block
    main_body = base_plate.fuse(block_shape)
    
    # --- Pin Holes ---
    # 6 Holes, Diameter 1.8mm
    # Spacing 2.54mm
    # Hole 3 and 4 are +/- 1.27mm from center Y.
    # Y Positions:
    # 3: -1.27
    # 4: +1.27
    # 2: -1.27 - 2.54 = -3.81
    # 1: -3.81 - 2.54 = -6.35
    # 5: +1.27 + 2.54 = +3.81
    # 6: +3.81 + 2.54 = +6.35
    
    pin_hole_radius = 1.8 / 2.0
    # Make holes long enough to cut through everything (Base + Block)
    # Total height is 5.3. Let's make them 10mm to be safe.
    pin_hole_height = 10.0 
    
    # Chamfer from bottom: 1mm
    # This means a cone at the bottom.
    chamfer_height = 1.0
    chamfer_radius_bottom = pin_hole_radius + 1.0 # 1mm chamfer
    
    y_positions = [-6.35, -3.81, -1.27, 1.27, 3.81, 6.35]
    pin_holes = []
    
    for y_pos in y_positions:
        # Create cylinder
        p_hole = Part.makeCylinder(pin_hole_radius, pin_hole_height)
        # Center at (0, y_pos), and start slightly below Z=0 to ensure clean cut
        p_hole.translate(FreeCAD.Vector(0, y_pos, -1.0))
        
        # Create chamfer cone
        # Cone from Z=0 to Z=1 (relative to part origin, but we are cutting)
        # Actually, we want the cut to be wider at the bottom.
        # So the "negative" shape (the tool) must be a cone.
        # Bottom (Z=0): R = 1.9
        # Top (Z=1): R = 0.9
        chamfer_cone = Part.makeCone(chamfer_radius_bottom, pin_hole_radius, chamfer_height)
        chamfer_cone.translate(FreeCAD.Vector(0, y_pos, 0))
        
        # Fuse cylinder and cone to make the full cutter
        full_cutter = p_hole.fuse(chamfer_cone)
        
        pin_holes.append(full_cutter)
        
    # Cut Pin Holes from Main Body
    if pin_holes:
        fused_pin_holes = pin_holes[0]
        for ph in pin_holes[1:]:
            fused_pin_holes = fused_pin_holes.fuse(ph)
            
        final_shape = main_body.cut(fused_pin_holes)
    else:
        final_shape = main_body
    
    return {
        "PogoPinAufsatz": {
            "shape": final_shape,
            "color": (0.8, 0.8, 0.2) # Yellowish
        }
    }
