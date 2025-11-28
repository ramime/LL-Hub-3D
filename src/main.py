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


        # --- BUILD SINGLE SLOT (FULL FEATURES) ---
        log("Building Single Slot (Full Features)...")
        from models import hub
        # Single slot gets controller mounts for testing
        single_slot_parts = hub.create_model(params.get('hub', {}), global_dims, features={'controller_mounts': True})
        if single_slot_parts:
            export_parts(single_slot_parts, "Hub_Single_Slot", output_dir_step, output_dir_stl, os.path.join(base_dir, 'output', '3mf'))

        # --- BUILD HUB TYPE A & B ---
        # Grid Layout:
        # 2 Rows, 3 Columns.
        # Slots 1-6. Slot 5 has controller.
        # Slot 1: Top-Left, Slot 2: Top-Mid, Slot 3: Top-Right
        # Slot 4: Bot-Left, Slot 5: Bot-Mid, Slot 6: Bot-Right
        
        # Grid Spacing:
        # X-Spacing: outer_flat_to_flat (84.2) + 2*rim (1.0) = 85.2?
        # Actually, hexagons pack differently.
        # But user says "aneinander gereiht".
        # If they are hexagons with flat sides touching:
        # Center-to-Center X distance = Flat-to-Flat distance.
        # Center-to-Center Y distance?
        # User says: "mittlere Spalte um eine halbe Kachel nach oben verschoben".
        # "halbe Kachel" usually means half height? Or half width?
        # Hexagon height (point-to-point) is 2*R.
        # Let's assume standard hexagonal packing or the specific layout described.
        
        # Let's calculate the grid based on "Flat-to-Flat" width W = 84.2 + 1.0 (rim) = 85.2
        # Height H = W / cos(30) = W * 1.1547
        
        # Wait, the orientation is "Horizontal edge top/bottom".
        # So Flat-to-Flat is Height (Y-direction)? No.
        # "6-Ecke, mit der Horizontalen Kante oben".
        # This means Pointy ends are Left/Right.
        # So Flat-to-Flat is the vertical dimension (Y).
        # Point-to-Point is the horizontal dimension (X).
        
        # Let's re-read: "6-Ecke, mit der Horizontalen Kante oben".
        # -> Top edge is horizontal.
        # -> Vertices are at 30, 90, 150, 210, 270, 330 degrees?
        # No, if top edge is horizontal, then vertices are at angles that make top edge horizontal.
        # Standard orientation (0 deg) usually puts vertex at X-axis.
        # If vertex is at X (0 deg), then edges are at 30, 90... -> Vertical edges?
        # Let's check create_hexagon:
        # "Orientation: Pointy sides at X-axis (0 deg), meaning Top and Bottom edges are horizontal."
        # Correct.
        # So:
        # Width (X) = Point-to-Point = 2 * R = 2 * (d / sqrt(3))
        # Height (Y) = Flat-to-Flat = d
        
        # d = 84.2 (inner) + 1.0 (rim) = 85.2 mm (Outer Rim Flat-to-Flat)
        # Let's use the full outer dimension including rim for spacing.
        flat_to_flat_outer = global_dims['hub']['outer_flat_to_flat_mm'] + 1.0 # 2*0.5 rim
        import math
        circumradius_outer = flat_to_flat_outer / math.sqrt(3)
        point_to_point_outer = 2 * circumradius_outer
        
        # Spacing:
        # X-Spacing: To tile horizontally, we place them side-by-side?
        # If pointy sides are left/right, they touch at points? No, that leaves gaps.
        # Hexagons tile by fitting the point of one into the V of the others.
        # But user says "2 horizontalen Reihen mit je 3 Slots".
        # And "mittlere Spalte um eine halbe Kachel nach oben verschoben".
        # This describes a honeycomb pattern.
        
        # Col 1 (Slots 1, 4): X = 0
        # Col 2 (Slots 2, 5): X = Width * 0.75 (standard hex spacing)
        # Col 3 (Slots 3, 6): X = Width * 1.5
        
        # Standard Hex Spacing (Pointy-Top orientation) is dx = W, dy = H*0.75.
        # Here we have Flat-Top orientation.
        # Spacing X = Width * 0.75? No.
        # For Flat-Top:
        # Columns are spaced by X = Width * 0.75 = (2*R) * 0.75 = 1.5 * R
        # Rows are spaced by Y = Flat-to-Flat = d
        # And odd columns are shifted by Y = d/2.
        
        # Let's implement this logic.
        # R = circumradius_outer
        # d = flat_to_flat_outer
        
        dx = 1.5 * circumradius_outer
        dy = flat_to_flat_outer
        
        # Type A: Middle column (Col 2) shifted UP by d/2.
        # Type B: Middle column (Col 2) shifted DOWN by d/2.
        
        for hub_type, shift_dir in [("A", 1), ("B", -1)]:
            log(f"Building Hub Type {hub_type}...")
            
            hub_assembly_parts = {}
            
            # Slots 1-6
            # New Numbering:
            # Row 1 (Bottom): Slot 1 (Left), Slot 2 (Mid), Slot 3 (Right)
            # Row 0 (Top):    Slot 4 (Left), Slot 5 (Mid), Slot 6 (Right)
            
            slots_config = [
                {'id': 1, 'col': 0, 'row': 1}, # Bottom-Left
                {'id': 2, 'col': 1, 'row': 1}, # Bottom-Mid
                {'id': 3, 'col': 2, 'row': 1}, # Bottom-Right
                {'id': 4, 'col': 0, 'row': 0}, # Top-Left
                {'id': 5, 'col': 1, 'row': 0}, # Top-Mid (Has Controller)
                {'id': 6, 'col': 2, 'row': 0}, # Top-Right
            ]
            
            all_slot_shapes = []
            
            for slot in slots_config:
                # Determine features
                has_controller = (slot['id'] == 5)
                
                # Generate Slot Shape
                parts = hub.create_model(params.get('hub', {}), global_dims, features={'controller_mounts': has_controller})
                slot_shape = parts['Hub_Body']['shape']
                
                # Calculate Position
                pos_x = slot['col'] * dx
                pos_y = -slot['row'] * dy # Row 0 is top, Row 1 is below
                
                # Apply Column Shift
                if slot['col'] == 1: # Middle Column
                    pos_y += shift_dir * (dy / 2)
                    
                # Translate
                slot_shape.translate(FreeCAD.Vector(pos_x, pos_y, 0))
                
                all_slot_shapes.append(slot_shape)
                
                # Add to Assembly (Optional: if we still want individual slots in the file)
                # part_name = f"Slot_{slot['id']}"
                # hub_assembly_parts[part_name] = {
                #     "shape": slot_shape,
                #     "color": (0.9, 0.9, 0.9)
                # }
            
            # Fuse all slots into one Hub Body
            if all_slot_shapes:
                fused_hub = all_slot_shapes[0]
                for s in all_slot_shapes[1:]:
                    fused_hub = fused_hub.fuse(s)
                
                # Add Fused Body to Export
                hub_assembly_parts[f"Hub_Type_{hub_type}_Body"] = {
                    "shape": fused_hub,
                    "color": (0.9, 0.9, 0.9)
                }
                
            # Export Hub Type
            export_parts(hub_assembly_parts, f"Hub_Type_{hub_type}", output_dir_step, output_dir_stl, os.path.join(base_dir, 'output', '3mf'))
        
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
            obj.ViewObject.Visibility = True
        
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
