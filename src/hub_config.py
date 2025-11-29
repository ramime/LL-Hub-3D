
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
        'usb_mounts': (slot_type == SLOT_USB)
    }
