
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
    
    return {
        'controller_mounts': (slot_type == SLOT_CONTROLLER),
        'usb_mounts': (slot_type == SLOT_USB),
        'connectors': _get_connectors(hub_type, slot_id)
    }

def _get_connectors(hub_type, slot_id):
    """Returns the connector configuration for a slot."""
    # Default: No connectors
    # We want to test the new system.
    # Let's configure Hub A and B to have connectors.
    # Hub A: North (Side 1) = Male, South (Side 4) = Female.
    # Hub B: North (Side 1) = Male, South (Side 4) = Female.
    # This allows chaining A -> B -> A ...
    
    # Also test diagonal?
    # Let's add Side 0 (NE) = Male, Side 3 (SW) = Female to Hub A.
    
    conns = {}
    
    # Common for all hubs (for testing)
    # Side 1 (N): Male
    # Side 4 (S): Female
    conns[1] = 'male'
    conns[4] = 'female'
    
    # Test Diagonal on Hub A
    # if hub_type == HUB_TYPE_A:
    #     conns[0] = 'male' # NE
    #     conns[3] = 'female' # SW
        
    return conns

