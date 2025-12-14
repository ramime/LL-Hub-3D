import FreeCAD
import Part
from lib import cad_tools

def create_model():
    """
    Creates the Abstandshalter_PCB model.
    Dimensions: 18x5x3mm
    Holes: 6x 1mm diameter, centered, 2.54mm pitch
    """
    length = 18.0
    width = 5.0
    height = 3.0
    
    # 1. Create Base Box
    # Center X and Y, Z from 0 to height
    box = Part.makeBox(length, width, height)
    box.translate(FreeCAD.Vector(-length/2, -width/2, 0))
    
    # 2. Create Holes
    hole_diameter = 1.0
    hole_radius = hole_diameter / 2.0
    pitch = 2.54
    num_holes = 6
    
    # Calculate start position (centered)
    # Total span center-to-center = (N-1) * pitch
    span = (num_holes - 1) * pitch
    start_x = -span / 2.0
    
    holes = []
    for i in range(num_holes):
        x = start_x + i * pitch
        
        # Create cylinder for hole
        # Ensure it's slightly longer than height for clean cut
        cyl_height = height + 2.0
        cyl = Part.makeCylinder(hole_radius, cyl_height)
        
        # Position: X determined, Y=0 (centered), Z=-1 (to cut through)
        cyl.translate(FreeCAD.Vector(x, 0, -1.0))
        holes.append(cyl)
        
    # 3. Cut Holes from Box
    if holes:
        # Fuse holes first
        if len(holes) > 1:
            compound_holes = cad_tools.fuse_all(holes[0], holes[1:])
        else:
            compound_holes = holes[0]
            
        final_shape = box.cut(compound_holes)
    else:
        final_shape = box
        
    return final_shape
