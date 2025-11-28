import FreeCAD
import Part
from lib import cad_tools

def create_model(params):
    """
    Creates the Hello World assembly (Box + Cylinder Insert).
    Returns a dictionary of parts: {'part_name': shape}
    """
    # Create Geometry (Box)
    box_shape = cad_tools.create_box(
        params['length'],
        params['width'],
        params['height']
    )
    box_shape = cad_tools.fillet_edges(box_shape, params['fillet_radius'])

    # Create Geometry (Cylinder)
    cyl_radius = params['width'] / 4
    cyl_height = params['height']
    cyl_shape = cad_tools.create_cylinder(cyl_radius, cyl_height)
    
    # Move cylinder to center
    center_vec = FreeCAD.Vector(params['length']/2, params['width']/2, 0)
    cyl_shape.translate(center_vec)

    # Boolean Operation: Cut cylinder from box
    box_with_hole = box_shape.cut(cyl_shape)

    return {
        "Box_Body": {
            "shape": box_with_hole,
            "color": (0.8, 0.2, 0.2)
        },
        "Cylinder_Insert": {
            "shape": cyl_shape,
            "color": (0.2, 0.2, 0.8)
        }
    }
