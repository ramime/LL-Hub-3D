import FreeCAD
import Part
import math
from . import geometry
from . import features as feat_module


def create_model(params, global_dims, features={}):
    """
    Creates the Hub model.
    Returns a dictionary of parts: {'part_name': shape}
    features: dict of enabled features.
        - controller_mounts: bool
        - usb_mounts: bool
        - open_sides: list of int (0-5) - indices of walls to cut cable channels into.
    """
    # Extract dimensions
    dims = _extract_dimensions(global_dims)
    
    # 1. Create Base Body (Floor + Wall + Slope)
    hub_body = geometry.create_base_body(dims)
    
    # 2. Add Lid Recesses
    hub_body = geometry.create_lid_recesses(hub_body, dims)
    
    # 3. Add Spacer Rim
    hub_body = geometry.create_rim(hub_body, dims)
    
    # 4. Add Floor Mounting Holes
    hub_body = geometry.create_floor_holes(hub_body, dims)
    
    # 5. Add Magnet Pillars
    hub_body = feat_module.create_magnet_pillars(hub_body, dims)
    
    # 6. Add PogoPin Pillars
    hub_body = feat_module.create_pogo_pillars(hub_body, dims)
    
    # 7. Add Controller Mounts (Optional)
    if features.get('controller_mounts', False):
        hub_body = feat_module.create_controller_features(hub_body, dims)
        
    # 8. Add USB Mounts & Cutout (Optional)
    usb_conf = features.get('usb_config', {'enabled': False, 'angle': 0.0})
    # Backward compatibility if usb_mounts boolean still exists in some old code paths (optional)
    if features.get('usb_mounts', False):
         usb_conf = {'enabled': True, 'angle': 0.0}

    if usb_conf.get('enabled', False):
        hub_body = feat_module.create_usb_features(hub_body, dims, angle=usb_conf.get('angle', 0.0))

    # 9. Add Cable Channels (Cutouts)
    open_sides = features.get('open_sides', [])
    if open_sides:
        hub_body = geometry.create_cable_channels(hub_body, dims, open_sides)
        


    # 11. Add Magnet Features
    magnet_config = features.get('magnet_config', {})
    # Backwards compatibility for magnet_sides list
    if 'magnet_sides' in features:
        for side in features['magnet_sides']:
            if side not in magnet_config:
                magnet_config[side] = ['left', 'right']

    # Filter out magnet connectors on the USB wall to prevent collision
    # Mapping angles to Side IDs:
    # 0.0 -> 4 (South)
    # -60.0 -> 5 (SW)
    # 60.0 -> 3 (SE)
    if usb_conf.get('enabled', False):
        angle = usb_conf.get('angle', 0.0)
        usb_side = None
        
        # Determine side based on angle (tolerance for float comparison)
        if abs(angle - 0.0) < 0.1:
            usb_side = 4
        elif abs(angle - 60.0) < 0.1:
            usb_side = 3
        elif abs(angle - (-60.0)) < 0.1:
            usb_side = 5
            
        if usb_side is not None and usb_side in magnet_config:
            # Remove this side from magnet configuration
            del magnet_config[usb_side]
            # print(f"Removed magnet connectors from Side {usb_side} due to USB cutout collision.")

    if magnet_config:
        hub_body = feat_module.create_magnet_features(hub_body, dims, magnet_config)

    # 12. Create Modifier (for printing optimization)
    modifier = geometry.create_modifier(dims)
    
    return {
        "Hub_Body": {
            "shape": hub_body,
            "color": (0.9, 0.9, 0.9) # Light Grey
        },
        "Modifier": {
            "shape": modifier,
            "color": (0.2, 0.8, 0.2) # Greenish
        }
    }

def _extract_dimensions(global_dims):
    """Helper to extract and calculate common dimensions."""
    d = {}
    d['outer_flat_to_flat'] = global_dims['hub']['outer_flat_to_flat_mm']
    d['wall_thickness'] = global_dims['hub']['wall_thickness_mm']
    d['floor_height'] = 2.0
    d['wall_height'] = 14.0
    d['inner_flat_to_flat'] = d['outer_flat_to_flat'] - (2 * d['wall_thickness'])
    
    # Slope parameters
    d['slope_length_y'] = 29.0
    d['slope_angle_deg'] = 80.0
    
    # Calculate Z heights
    d['z_top_wall'] = d['floor_height'] + d['wall_height']
    
    angle_rad = math.radians(90 - d['slope_angle_deg'])
    d['delta_z_slope'] = d['slope_length_y'] * math.tan(angle_rad)
    d['z_south_wall'] = d['z_top_wall'] - d['delta_z_slope']
    

    
    return d
