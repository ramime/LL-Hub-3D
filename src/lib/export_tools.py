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

def export_to_3mf(objects, filename, output_dir):
    """
    Exports a list of objects to a 3MF file.
    Args:
        objects: List of FreeCAD objects (App.DocumentObject) or shapes.
                 Note: For colors to work, passing App.DocumentObject is better.
        filename: Name of the file without extension.
        output_dir: Target directory.
    """
    import Mesh
    path = os.path.join(output_dir, filename + ".3mf")
    
    # FreeCAD's 3MF export often works best with Mesh objects or by using the Mesh.export function
    # on a list of objects.
    
    # Ensure we are working with a list
    if not isinstance(objects, list):
        objects = [objects]
        
    try:
        Mesh.export(objects, path)
        print(f"Exported 3MF to {path}")
    except Exception as e:
        print(f"Error exporting 3MF: {e}")

def export_to_fcstd(doc, filename, output_dir):
    """
    Saves the FreeCAD document to an .FCStd file.
    Args:
        doc: The FreeCAD document object.
        filename: Name of the file without extension.
        output_dir: Target directory.
    """
    path = os.path.join(output_dir, filename + ".FCStd")
    try:
        doc.saveAs(path)
        print(f"Saved FCStd to {path}")
    except Exception as e:
        print(f"Error saving FCStd: {e}")
