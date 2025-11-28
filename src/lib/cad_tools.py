import FreeCAD
import Part

def create_box(length, width, height):
    """
    Creates a simple box using FreeCAD Part module.
    """
    box = Part.makeBox(length, width, height)
    return box

def fillet_edges(shape, radius):
    """
    Fillets all edges of the given shape.
    """
    # Get all edges
    edges = shape.Edges
    # Apply fillet
    filleted_shape = shape.makeFillet(radius, edges)
    return filleted_shape

def create_cylinder(radius, height):
    """
    Creates a simple cylinder.
    """
    return Part.makeCylinder(radius, height)

def create_hexagon(flat_to_flat, height):
    """
    Creates a hexagon prism with the given flat-to-flat distance (diameter of inscribed circle).
    Orientation: Pointy sides at X-axis (0 deg), meaning Top and Bottom edges are horizontal.
    """
    import math
    # Circumradius R = (d/2) / cos(30) = d / sqrt(3)
    circumradius = flat_to_flat / math.sqrt(3)
    
    # Create the polygon wire
    # makePolygon expects a list of vectors. 
    # Or we can use makeRegularPolygon which is easier.
    # makeRegularPolygon(radius, sides, start_angle, center, normal)
    # Default start_angle puts a vertex at (R, 0, 0). 
    # For a hexagon, vertices at 0, 60, 120, 180, 240, 300.
    # Top edge is between 60 and 120 -> Horizontal. Correct.
    
    # Note: Part.makePolygon creates a wire from points. 
    # Part.makeRegularPolygon is not a direct function in some FreeCAD versions, 
    # usually we use Part.makePolygon with calculated points or Part.makeCircle(..., 6) is a trick? 
    # No, let's calculate points to be safe and explicit.
    
    points = []
    for i in range(6):
        angle_deg = i * 60
        angle_rad = math.radians(angle_deg)
        x = circumradius * math.cos(angle_rad)
        y = circumradius * math.sin(angle_rad)
        points.append(FreeCAD.Vector(x, y, 0))
    
    # Close the polygon
    points.append(points[0])
    
    wire = Part.makePolygon(points)
    face = Part.Face(wire)
    prism = face.extrude(FreeCAD.Vector(0, 0, height))
    return prism

def create_prism_from_points(points, extrusion_vec):
    """
    Creates a prism by extruding a polygon defined by 'points' along 'extrusion_vec'.
    Points should be a list of FreeCAD.Vector or tuples.
    """
    # Ensure points are Vectors
    vec_points = []
    for p in points:
        if isinstance(p, FreeCAD.Vector):
            vec_points.append(p)
        else:
            vec_points.append(FreeCAD.Vector(p[0], p[1], p[2]))
            
    # Close polygon if not closed
    if vec_points[0] != vec_points[-1]:
        vec_points.append(vec_points[0])
        
    wire = Part.makePolygon(vec_points)
    face = Part.Face(wire)
    prism = face.extrude(extrusion_vec)
    return prism
