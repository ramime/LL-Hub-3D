import FreeCAD
import Part
import os

def export_to_step(shape, filename, output_dir):
    """
    Exports a shape to a STEP file.
    """
    path = os.path.join(output_dir, filename + ".step")
    shape.exportStep(path)
    print(f"Exported STEP to {path}")

def export_to_stl(shape, filename, output_dir):
    """
    Exports a shape to an STL file.
    """
    path = os.path.join(output_dir, filename + ".stl")
    shape.exportStl(path)
    print(f"Exported STL to {path}")
