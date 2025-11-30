
# Hub Configuration Definitions

# Slot Types
SLOT_BASIC = 'basic'
SLOT_CONTROLLER = 'controller'
SLOT_USB = 'usb'

# Hub Types
HUB_TYPE_A = 'A'
HUB_TYPE_B = 'B'

# Slot Configuration for each Hub Type
# Format: { HubType: { SlotID: SlotType } }
# Default is SLOT_BASIC if not specified.
HUB_SLOT_CONFIG = {
    HUB_TYPE_A: {
        2: SLOT_CONTROLLER,
        3: SLOT_USB
    },
    HUB_TYPE_B: {
        5: SLOT_CONTROLLER,
        3: SLOT_USB
    }
}

def get_slot_features(hub_type, slot_id):
    """
    Returns the feature dictionary for a given slot in a specific hub type.
    """
    slot_type = HUB_SLOT_CONFIG.get(hub_type, {}).get(slot_id, SLOT_BASIC)
    
    # Connector Flags
    conn_ne = False
    conn_nw = False
    conn_se = False
    conn_sw = False
    
    # Hub Type A Configuration
    if hub_type == HUB_TYPE_A:
        if slot_id == 5:
            conn_ne = True
            conn_nw = True
        elif slot_id == 1:
            conn_se = True
        elif slot_id == 3:
            conn_sw = True
            
    # Hub Type B Configuration
    elif hub_type == HUB_TYPE_B:
        if slot_id == 4:
            conn_ne = True
        elif slot_id == 6:
            conn_nw = True
        elif slot_id == 2:
            conn_se = True
            conn_sw = True

    return {
        'controller_mounts': (slot_type == SLOT_CONTROLLER),
        'usb_mounts': (slot_type == SLOT_USB),
        'conn_ne': conn_ne,
        'conn_nw': conn_nw,
        'conn_se': conn_se,
        'conn_sw': conn_sw,
        'connectors': _get_connectors(hub_type, slot_id)
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

