import FreeCAD
import Part
import math
from lib import cad_tools, constants

def create_mounting_pillars(positions, height_func=None):
    """
    Creates mounting pillars at given positions.
    height_func: function(pos) -> height. If None, uses constant height.
    """
    pillars = []
    holes = []
    
    # Default height for horizontal lid
    default_len = constants.Z_LID_BOTTOM - constants.FLOOR_HEIGHT
    
    for pos in positions:
        if height_func:
            length = height_func(pos)
        else:
            length = default_len
            
        # Solid Pillar
        p = Part.makeCylinder(constants.PILLAR_RADIUS_OUTER, length)
        p.translate(FreeCAD.Vector(0, 0, constants.FLOOR_HEIGHT))
        p.translate(pos)
        pillars.append(p)
        
        # Hole (Sackloch)
        h = Part.makeCylinder(constants.PILLAR_RADIUS_INNER, length)
        h.translate(FreeCAD.Vector(0, 0, constants.FLOOR_HEIGHT))
        h.translate(pos)
        holes.append(h)
        
    return pillars, holes

def create_magnet_recesses(global_dims, z_start):
    """
    Creates magnet recesses.
    """
    magnet_dist = global_dims['system']['magnet_mounting_radius_mm']
    
    mag_positions = [
        FreeCAD.Vector(0, 0, 0), # Center
        FreeCAD.Vector(0, magnet_dist, 0) # North
    ]
    
    # Calculate the other two (Rotated +/- 60 from North)
    v_north = FreeCAD.Vector(0, magnet_dist, 0)
    
    m = FreeCAD.Matrix()
    m.rotateZ(math.radians(60))
    mag_positions.append(m.multVec(v_north)) # Left
    
    m = FreeCAD.Matrix()
    m.rotateZ(math.radians(-60))
    mag_positions.append(m.multVec(v_north)) # Right
    
    recess_depth = constants.LID_THICKNESS - constants.MAGNET_RECESS_REMAINING_MATERIAL
    
    cutters = []
    base_cutter = Part.makeCylinder(constants.MAGNET_RECESS_RADIUS, recess_depth)
    base_cutter.translate(FreeCAD.Vector(0, 0, z_start))
    
    for pos in mag_positions:
        c = base_cutter.copy()
        c.translate(pos)
        cutters.append(c)
        
    return cutters

def create_pogo_cutout():
    """
    Creates the pogo pin cutout.
    """
    pogo_cutter = Part.makeBox(constants.POGO_WIDTH, constants.POGO_HEIGHT, 50)
    pogo_cutter.translate(FreeCAD.Vector(-constants.POGO_WIDTH/2, constants.POGO_Y_START, -10))
    return pogo_cutter
