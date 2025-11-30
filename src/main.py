import sys
import os
import json
import traceback
import math

# Add the current directory to path so we can import from lib
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    import FreeCAD
except ImportError:
    sys.exit(1)

def log(message):
    """Log to console."""
    msg = str(message) + "\n"
    FreeCAD.Console.PrintMessage(msg)

try:
    from lib import cad_tools, export_tools
    from lib.grid_system import GridSystem
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

        # Initialize Grid System
        grid = GridSystem(global_dims)

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
            
            # Find neighbors using GridSystem
            neighbors_map = grid.find_neighbors(slots_grid, shift_dir)

            for slot in slots_grid:
                # Get Features
                features = hub_config.get_slot_features(hub_type, slot['id'])
                
                # Set open sides from neighbors map
                neighbors = neighbors_map.get(slot['id'], [])
                features['open_sides'] = neighbors
                
                # Filter connectors: Only allow connectors on sides that have neighbors
                if 'connectors' in features:
                    valid_connectors = {}
                    for side, ctype in features['connectors'].items():
                        if side in neighbors:
                            valid_connectors[side] = ctype
                    features['connectors'] = valid_connectors
                    
                    # Remove connector sides from open_sides (Cable Channels)
                    # We don't want to cut a cable channel where we have a connector
                    features['open_sides'] = [s for s in neighbors if s not in valid_connectors]
                
                # Create Part
                parts = hub.create_model(params.get('hub', {}), global_dims, features=features)
                slot_shape = parts['Hub_Body']['shape']
                
                # Position
                pos = grid.get_slot_position(slot['col'], slot['row'], shift_dir)
                slot_shape.translate(pos)
                all_slot_shapes.append(slot_shape)
                
                # Handle Modifier
                if 'Modifier' in parts:
                    mod_shape = parts['Modifier']['shape']
                    mod_shape.translate(pos)
                    all_modifiers.append(mod_shape)
                
            # Fuse all slots
            if all_slot_shapes:
                fused_hub = cad_tools.fuse_all(all_slot_shapes[0], all_slot_shapes[1:])
                
                hub_assembly_parts[f"{export_name}_Body"] = {
                    "shape": fused_hub,
                    "color": (0.9, 0.9, 0.9)
                }
                
            # Export Main Body
            build_and_export(export_name, hub_assembly_parts)

            # Fuse modifiers and Export Separately
            if all_modifiers:
                fused_mods = cad_tools.fuse_all(all_modifiers[0], all_modifiers[1:])
                
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
