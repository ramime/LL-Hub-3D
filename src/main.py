import sys
import os
import json
import traceback

# Debug: Write to a file immediately to prove execution started
debug_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'debug_exec.txt')
with open(debug_log_path, 'w') as f:
    f.write("Script execution started.\n")

# Add the current directory to path so we can import from lib
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    import FreeCAD
except ImportError:
    with open(debug_log_path, 'a') as f:
        f.write("Error: FreeCAD module not found.\n")
    sys.exit(1)

def log(message):
    """Log to both console and file."""
    msg = str(message) + "\n"
    FreeCAD.Console.PrintMessage(msg)
    print(msg) # Fallback
    with open(debug_log_path, 'a') as f:
        f.write(msg)

try:
    from lib import cad_tools, export_tools
    log("Libraries imported successfully.")
except Exception as e:
    log(f"Error importing libraries: {e}")
    log(traceback.format_exc())
    sys.exit(1)

def load_config(config_path):
    with open(config_path, 'r') as f:
        return json.load(f)

def main():
    try:
        # Setup paths
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, 'config', 'parameters.json')
        output_dir_step = os.path.join(base_dir, 'output', 'step')
        output_dir_stl = os.path.join(base_dir, 'output', 'stl')

        log(f"Base Dir: {base_dir}")
        
        # Load Global Dimensions
        common_dims_path = os.path.abspath(os.path.join(base_dir, '..', 'LL-Common', 'GLOBAL_DIMENSIONS.json'))
        log(f"Loading global dimensions from {common_dims_path}...")
        if os.path.exists(common_dims_path):
            global_dims = load_config(common_dims_path)
            log(f"Global dimensions loaded. System grid: {global_dims.get('system', {}).get('tile_grid_size_mm')}")
        else:
            log("WARNING: Global dimensions file not found!")

        # Load parameters
        log(f"Loading parameters from {config_path}...")
        if not os.path.exists(config_path):
            log(f"ERROR: Config file not found at {config_path}")
            return

        params = load_config(config_path)
        hw_params = params['hello_world']
        log(f"Parameters loaded: {hw_params}")

        # --- BUILD HELLO WORLD EXAMPLE ---
        # log("Building Hello World Model...")
        # from models import hello_world
        # hw_parts = hello_world.create_model(hw_params)
        
        # Export Hello World
        # export_parts(hw_parts, "hello_world_assembly", output_dir_step, output_dir_stl, os.path.join(base_dir, 'output', '3mf'))


        # --- BUILD HUB MODEL ---
        log("Building Hub Model...")
        from models import hub
        hub_parts = hub.create_model(params.get('hub', {}), global_dims)
        if hub_parts:
            export_parts(hub_parts, "hub_assembly", output_dir_step, output_dir_stl, os.path.join(base_dir, 'output', '3mf'))
        
        log("Done successfully!")
        
    except Exception as e:
        log(f"CRITICAL ERROR in main: {e}")
        log(traceback.format_exc())

def export_parts(parts_dict, assembly_name, step_dir, stl_dir, threemf_dir):
    """
    Helper to export a dictionary of parts.
    parts_dict format: 
    {
        "PartName": { "shape": <Shape>, "color": (r,g,b) },
        ...
    }
    """
    import FreeCAD
    from lib import export_tools
    
    doc_name = "ExportDoc_" + assembly_name
    if FreeCAD.ActiveDocument:
        doc = FreeCAD.ActiveDocument
    else:
        doc = FreeCAD.newDocument(doc_name)
    
    export_objects = []
    
    for name, data in parts_dict.items():
        shape = data['shape']
        color = data.get('color', (0.5, 0.5, 0.5))
        
        # 1. Export individual STEP/STL
        export_tools.export_to_step(shape, f"{assembly_name}_{name}", step_dir)
        # export_tools.export_to_stl(shape, f"{assembly_name}_{name}", stl_dir) # Optional: Export individual STLs
        
        # 2. Add to Doc for 3MF
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
        
        if obj.ViewObject:
            obj.ViewObject.ShapeColor = color
        
        export_objects.append(obj)
        
    doc.recompute()
    
    # 3. Export Assembly 3MF
    export_tools.export_to_3mf(export_objects, assembly_name, threemf_dir)

    # 4. Export FreeCAD Document (.FCStd)
    fcstd_dir = os.path.join(os.path.dirname(threemf_dir), 'fcstd')
    if not os.path.exists(fcstd_dir):
        os.makedirs(fcstd_dir)
    export_tools.export_to_fcstd(doc, assembly_name, fcstd_dir)

# Log the scope name to understand how FreeCAD runs this

# Log the scope name to understand how FreeCAD runs this
log(f"Scope name is: {__name__}")

if __name__ == "main":
    main()
else:
    # If FreeCAD runs this as an embedded script, __name__ might be different (e.g. 'main' or filename)
    # We force execution here for debugging purposes
    log("Not running as __main__, but forcing main() execution...")
    main()
