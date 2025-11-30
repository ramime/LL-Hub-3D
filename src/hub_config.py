
# Hub Configuration Definitions

# Slot Types
SLOT_BASIC = 'basic'
SLOT_CONTROLLER = 'controller'
SLOT_USB = 'usb'
SLOT_USB_LEFT = 'usb_left'   # SW (-60 deg)
SLOT_USB_RIGHT = 'usb_right' # SE (+60 deg)

# Hub Types
HUB_TYPE_A = 'A'
HUB_TYPE_B = 'B'

# Slot Configuration for each Hub Type
# Format: { HubType: { SlotID: SlotType } }
# Default is SLOT_BASIC if not specified.
HUB_SLOT_CONFIG = {
    HUB_TYPE_A: {
        2: SLOT_CONTROLLER,
        1: SLOT_USB_LEFT
    },
    HUB_TYPE_B: {
        5: SLOT_CONTROLLER,
        3: SLOT_USB_RIGHT
    }
}

def get_slot_features(hub_type, slot_id):
    """
    Returns the feature dictionary for a given slot in a specific hub type.
    """
    slot_type = HUB_SLOT_CONFIG.get(hub_type, {}).get(slot_id, SLOT_BASIC)
    
    # Initialize connectors with defaults (N/S)
    conns = _get_connectors(hub_type, slot_id)
    
    # Hub Type A Configuration
    if hub_type == HUB_TYPE_A:
        if slot_id == 5:
            # Old NE (0) -> New 2
            # Old NW (2) -> New 6
            conns[2] = 'male'
            conns[6] = 'male'
        elif slot_id == 1:
            # Old SE (5) -> New 3
            conns[3] = 'female'
        elif slot_id == 3:
            # Old SW (3) -> New 5
            conns[5] = 'female'
            
    # Hub Type B Configuration
    elif hub_type == HUB_TYPE_B:
        if slot_id == 4:
            # Old NE (0) -> New 2
            conns[2] = 'male'
        elif slot_id == 6:
            # Old NW (2) -> New 6
            conns[6] = 'male'
        elif slot_id == 2:
            # Old SE (5) -> New 3
            # Old SW (3) -> New 5
            conns[3] = 'female'
            conns[5] = 'female'

    # USB Configuration
    usb_enabled = False
    usb_angle = 0.0
    
    if slot_type == SLOT_USB:
        usb_enabled = True
        usb_angle = 0.0
    elif slot_type == SLOT_USB_LEFT:
        usb_enabled = True
        usb_angle = -60.0 # SW (Clockwise)
    elif slot_type == SLOT_USB_RIGHT:
        usb_enabled = True
        usb_angle = 60.0 # SE (Counter-Clockwise)

    return {
        'controller_mounts': (slot_type == SLOT_CONTROLLER),
        'usb_config': {
            'enabled': usb_enabled,
            'angle': usb_angle
        },
        'connectors': conns
    }

def _get_connectors(hub_type, slot_id):
    """Returns the connector configuration for a slot."""
    conns = {}
    
    # Common for all hubs
    # Side 1 (N): Male
    # Side 4 (S): Female
    conns[1] = 'male'
    conns[4] = 'female'
        
    return conns

