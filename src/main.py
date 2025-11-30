import sys
import os
import json
import traceback
import math

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
    with open(debug_log_path, 'a') as f:
        f.write(msg)

try:
    from lib import cad_tools, export_tools
    from models import hub, lids, pogo_attachment
    import hub_config
    log("Libraries imported successfully.")
except Exception as e:
    log(f"Error importing libraries: {e}")
    log(traceback.format_exc())
    sys.exit(1)

def load_config(config_path):
    with open(config_path, 'r') as f:
        return json.load(f)

def calculate_grid_spacing(global_dims):
    """Calculates dx and dy for the hexagonal grid."""
    # d = flat_to_flat (inner) + 2 * rim (0.5)
    flat_to_flat_outer = global_dims['hub']['outer_flat_to_flat_mm'] + 1.0 
    circumradius_outer = flat_to_flat_outer / math.sqrt(3)
    
    # Horizontal spacing (Point-to-Point orientation would be different, 
    # but here we have Flat-Top orientation)
    # Col spacing = 1.5 * R
    dx = 1.5 * circumradius_outer
    dy = flat_to_flat_outer
    return dx, dy

def calculate_slot_position(col, row, dx, dy, shift_dir):
    """Calculates the (x, y) position for a slot."""
    pos_x = col * dx
    pos_y = -row * dy # Row 0 is top, Row 1 is below
    
    # Apply Column Shift for odd columns (Column 1 is the middle one)
    if col == 1: 
        pos_y += shift_dir * (dy / 2)
        
    return FreeCAD.Vector(pos_x, pos_y, 0)

def main():
    try:
        # Setup paths
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, 'config', 'parameters.json')
        output_dir_step = os.path.join(base_dir, 'output', 'step')
        output_dir_3mf = os.path.join(base_dir, 'output', '3mf')

        # Ensure output directories exist
        for d in [output_dir_step, output_dir_3mf]:
            if not os.path.exists(d):
                os.makedirs(d)

        log(f"Base Dir: {base_dir}")
        
        # Load Global Dimensions
        common_dims_path = os.path.abspath(os.path.join(base_dir, '..', 'LL-Common', 'GLOBAL_DIMENSIONS.json'))
        log(f"Loading global dimensions from {common_dims_path}...")
        if os.path.exists(common_dims_path):
            global_dims = load_config(common_dims_path)
            log(f"Global dimensions loaded.")
        else:
            log("WARNING: Global dimensions file not found!")
            return

        # Load parameters
        log(f"Loading parameters from {config_path}...")
        if not os.path.exists(config_path):
            log(f"ERROR: Config file not found at {config_path}")
            return

        params = load_config(config_path)

        # Helper to export a single part dictionary
        def build_and_export(name, parts, formats=None):
            if parts:
                log(f"Exporting {name}...")
                export_parts(parts, name, output_dir_step, output_dir_3mf, formats=formats)

        # --- 1. Solo Slot komplett (Test-Assembly) ---
        # 1 Slot mit allen Features aktiv + Deckel
        log("Building 1. Solo Slot (Full Features)...")
        features_full = {
            'controller_mounts': True, 
            'usb_mounts': True, 
            'conn_ne': True,
            'conn_nw': True,
            'conn_e': False,
            'conn_sw': True,
            'conn_se': True
        }
        solo_slot_parts = hub.create_model(params.get('hub', {}), global_dims, features=features_full)
        
        # Extract Modifier
        solo_modifier = {}
        if "Modifier" in solo_slot_parts:
            solo_modifier["Modifier"] = solo_slot_parts.pop("Modifier")
            
        solo_slot_parts.update(lids.create_horizontal_lid(global_dims))
        solo_slot_parts.update(lids.create_sloped_lid(global_dims))
        
        build_and_export("1_Hub_Solo_Slot_Full", solo_slot_parts)
        
        # Export Modifier separately (3MF only)
        if solo_modifier:
            build_and_export("1_Hub_Solo_Slot_Full_Modifier", solo_modifier, formats=['3mf'])

        # --- 2. Slot Basic ---
        log("Building 2. Slot Basic...")
        slot_basic_parts = hub.create_model(params.get('hub', {}), global_dims, features={})
        # Rename key for clarity in export
        slot_basic = {"Slot_Basic": slot_basic_parts["Hub_Body"]}
        build_and_export("2_Slot_Basic", slot_basic)

        # --- 3. Slot Controller ---
        log("Building 3. Slot Controller...")
        slot_ctrl_parts = hub.create_model(params.get('hub', {}), global_dims, features={'controller_mounts': True})
        slot_ctrl = {"Slot_Controller": slot_ctrl_parts["Hub_Body"]}
        build_and_export("3_Slot_Controller", slot_ctrl)

        # --- 4. Slot USB ---
        log("Building 4. Slot USB...")
        slot_usb_parts = hub.create_model(params.get('hub', {}), global_dims, features={'usb_mounts': True})
        slot_usb = {"Slot_USB": slot_usb_parts["Hub_Body"]}
        build_and_export("4_Slot_USB", slot_usb)

        # --- 5. Deckel Horizontal ---
        log("Building 5. Lid Horizontal...")
        lid_h = lids.create_horizontal_lid(global_dims)
        build_and_export("5_Lid_Horizontal", lid_h)

        # --- 6. Deckel Schräg ---
        log("Building 6. Lid Sloped...")
        lid_s = lids.create_sloped_lid(global_dims)
        build_and_export("6_Lid_Sloped", lid_s)

        # --- 7 & 8. Hub Type A & B ---
        dx, dy = calculate_grid_spacing(global_dims)
        
        hub_types = [
            (hub_config.HUB_TYPE_A, 1, "7_Hub_Type_A"), 
            (hub_config.HUB_TYPE_B, -1, "8_Hub_Type_B")
        ]
        
        slots_grid = [
            {'id': 1, 'col': 0, 'row': 1},
            {'id': 2, 'col': 1, 'row': 1},
            {'id': 3, 'col': 2, 'row': 1},
            {'id': 4, 'col': 0, 'row': 0},
            {'id': 5, 'col': 1, 'row': 0},
            {'id': 6, 'col': 2, 'row': 0},
        ]
        
        for hub_type, shift_dir, export_name in hub_types:
            log(f"Building {export_name}...")
            
            hub_assembly_parts = {}
            all_slot_shapes = []
            all_modifiers = []
            
            # Calculate open sides for all slots first
            # We need the positions of all slots to determine neighbors
            slot_positions = {}
            for slot in slots_grid:
                pos = calculate_slot_position(slot['col'], slot['row'], dx, dy, shift_dir)
                slot_positions[slot['id']] = pos

            for slot in slots_grid:
                # Get Features
                features = hub_config.get_slot_features(hub_type, slot['id'])
                
                # Calculate neighbors
                my_pos = slot_positions[slot['id']]
                open_sides = []
                
                # Check against all other slots
                for other_slot in slots_grid:
                    if slot['id'] == other_slot['id']:
                        continue
                        
                    other_pos = slot_positions[other_slot['id']]
                    diff = other_pos.sub(my_pos)
                    dist = diff.Length
                    
                    # Check if neighbor (distance approx flat_to_flat_outer = dy)
                    # Use a tolerance
                    if abs(dist - dy) < 2.0:
                        # Calculate angle
                        angle_deg = math.degrees(math.atan2(diff.y, diff.x))
                        if angle_deg < 0:
                            angle_deg += 360.0
                            
                        # Map to side index
                        # Side 0: 30, Side 1: 90, ...
                        # We allow some angular tolerance
                        side_angles = {
                            0: 30,
                            1: 90,
                            2: 150,
                            3: 210,
                            4: 270,
                            5: 330
                        }
                        
                        for s_idx, s_angle in side_angles.items():
                            if abs(angle_deg - s_angle) < 5.0:
                                open_sides.append(s_idx)
                                break
                
                features['open_sides'] = open_sides
                
                # Create Part
                parts = hub.create_model(params.get('hub', {}), global_dims, features=features)
                slot_shape = parts['Hub_Body']['shape']
                
                # Position
                slot_shape.translate(my_pos)
                all_slot_shapes.append(slot_shape)
                
                # Handle Modifier
                if 'Modifier' in parts:
                    mod_shape = parts['Modifier']['shape']
                    mod_shape.translate(my_pos)
                    all_modifiers.append(mod_shape)
                
            # Fuse all slots
            if all_slot_shapes:
                fused_hub = all_slot_shapes[0]
                for s in all_slot_shapes[1:]:
                    fused_hub = fused_hub.fuse(s)
                
                hub_assembly_parts[f"{export_name}_Body"] = {
                    "shape": fused_hub,
                    "color": (0.9, 0.9, 0.9)
                }
                
            # Export Main Body
            build_and_export(export_name, hub_assembly_parts)

            # Fuse modifiers and Export Separately
            if all_modifiers:
                fused_mods = all_modifiers[0]
                for m in all_modifiers[1:]:
                    fused_mods = fused_mods.fuse(m)
                
                modifier_parts = {
                    f"{export_name}_Modifier": {
                        "shape": fused_mods,
                        "color": (0.2, 0.8, 0.2)
                    }
                }
                # Export Modifier (3MF only)
                build_and_export(f"{export_name}_Modifier", modifier_parts, formats=['3mf'])

        # --- 9. PogoPinAufsatz ---
        log("Building 9. PogoPinAufsatz...")
        pogo_parts = pogo_attachment.create_pogo_pin_attachment()
        build_and_export("9_PogoPinAufsatz", pogo_parts)
        
        # Cleanup .FCBak files
        fcstd_dir = os.path.join(base_dir, 'output', 'fcstd')
        if os.path.exists(fcstd_dir):
            log("Cleaning up .FCBak files...")
            for f in os.listdir(fcstd_dir):
                if f.endswith(".FCBak"):
                    try:
                        os.remove(os.path.join(fcstd_dir, f))
                    except Exception as e:
                        log(f"Warning: Could not delete backup file {f}: {e}")

        log("Done successfully!")
        
    except Exception as e:
        log(f"CRITICAL ERROR in main: {e}")
        log(traceback.format_exc())

def export_parts(parts_dict, assembly_name, step_dir, threemf_dir, formats=None):
    """Helper to export a dictionary of parts."""
    import FreeCAD
    from lib import export_tools
    
    # Default to all formats if not specified
    if formats is None:
        formats = ['step', '3mf', 'fcstd']
    
    doc_name = "ExportDoc_" + assembly_name
    if FreeCAD.ActiveDocument:
        doc = FreeCAD.ActiveDocument
    else:
        doc = FreeCAD.newDocument(doc_name)
    
    export_objects = []
    
    for name, data in parts_dict.items():
        shape = data['shape']
        color = data.get('color', (0.5, 0.5, 0.5))
        
        # 1. Export individual STEP
        if 'step' in formats:
            export_tools.export_to_step(shape, f"{name}", step_dir)
        
        # 2. Add to Doc for 3MF
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
        
        if obj.ViewObject:
            obj.ViewObject.ShapeColor = color
            obj.ViewObject.Visibility = True
        
        export_objects.append(obj)
        
    doc.recompute()
    
    # 3. Export Assembly 3MF
    if '3mf' in formats:
        export_tools.export_to_3mf(export_objects, assembly_name, threemf_dir)

    # 4. Export FreeCAD Document (.FCStd)
    if 'fcstd' in formats:
        fcstd_dir = os.path.join(os.path.dirname(threemf_dir), 'fcstd')
        if not os.path.exists(fcstd_dir):
            os.makedirs(fcstd_dir)
        export_tools.export_to_fcstd(doc, assembly_name, fcstd_dir)

# Log the scope name to understand how FreeCAD runs this
log(f"Scope name is: {__name__}")

if __name__ == "__main__":
    main()
else:
    # If FreeCAD runs this as an embedded script
    log("Not running as __main__, but forcing main() execution...")
    main()
