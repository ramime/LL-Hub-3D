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
