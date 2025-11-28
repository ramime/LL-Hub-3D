import sys
import os
import json

# Add the current directory to path so we can import from lib
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    import FreeCAD
except ImportError:
    print("Error: FreeCAD module not found.")
    print("Please run this script using the FreeCAD Python executable or ensure FreeCAD is in your PYTHONPATH.")
    print("Example: 'C:\\Program Files\\FreeCAD 0.21\\bin\\freecadcmd.exe' src/main.py")
    sys.exit(1)

from lib import cad_tools, export_tools

def load_config(config_path):
    with open(config_path, 'r') as f:
        return json.load(f)

def main():
    # Setup paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, 'config', 'parameters.json')
    output_dir_step = os.path.join(base_dir, 'output', 'step')
    output_dir_stl = os.path.join(base_dir, 'output', 'stl')

    # Load parameters
    print(f"Loading parameters from {config_path}...")
    params = load_config(config_path)
    hw_params = params['hello_world']

    # Create Geometry
    print("Creating geometry...")
    box = cad_tools.create_box(
        hw_params['length'],
        hw_params['width'],
        hw_params['height']
    )

    # Modify Geometry (Fillet)
    print("Applying fillets...")
    final_shape = cad_tools.fillet_edges(box, hw_params['fillet_radius'])

    # Export
    print("Exporting files...")
    export_tools.export_to_step(final_shape, "hello_world_box", output_dir_step)
    export_tools.export_to_stl(final_shape, "hello_world_box", output_dir_stl)

    print("Done!")

if __name__ == "__main__":
    main()
