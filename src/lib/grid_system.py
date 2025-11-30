import math
import FreeCAD
from lib import constants

class GridSystem:
    def __init__(self, global_dims):
        self.global_dims = global_dims
        self.dx, self.dy = self._calculate_grid_spacing()

    def _calculate_grid_spacing(self):
        """Calculates dx and dy for the hexagonal grid."""
        flat_to_flat_outer = self.global_dims['hub']['outer_flat_to_flat_mm'] + 1.0 
        circumradius_outer = flat_to_flat_outer / math.sqrt(3)
        
        # Horizontal spacing (Flat-Top orientation)
        # Col spacing = 1.5 * R
        dx = 1.5 * circumradius_outer
        dy = flat_to_flat_outer
        return dx, dy

    def get_slot_position(self, col, row, shift_dir):
        """Calculates the (x, y) position for a slot."""
        pos_x = col * self.dx
        pos_y = -row * self.dy # Row 0 is top, Row 1 is below
        
        # Apply Column Shift for odd columns (Column 1 is the middle one)
        if col == 1: 
            pos_y += shift_dir * (self.dy / 2)
            
        return FreeCAD.Vector(pos_x, pos_y, 0)

    def find_neighbors(self, slots_grid, shift_dir):
        """
        Identifies open sides for each slot in the grid.
        Returns a dictionary: {slot_id: [open_side_indices]}
        """
        slot_positions = {}
        for slot in slots_grid:
            pos = self.get_slot_position(slot['col'], slot['row'], shift_dir)
            slot_positions[slot['id']] = pos

        neighbors_map = {}

        for slot in slots_grid:
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
                if abs(dist - self.dy) < constants.GRID_NEIGHBOR_TOLERANCE:
                    # Calculate angle
                    angle_deg = math.degrees(math.atan2(diff.y, diff.x))
                    if angle_deg < 0:
                        angle_deg += 360.0
                        
                    # Map to side index (1-based, Clockwise from North)
                    # 1: 90 (N), 2: 30 (NE), 3: 330 (SE), 4: 270 (S), 5: 210 (SW), 6: 150 (NW)
                    side_angles = {
                        1: 90,
                        2: 30,
                        3: 330,
                        4: 270,
                        5: 210,
                        6: 150
                    }
                    
                    for s_idx, s_angle in side_angles.items():
                        if abs(angle_deg - s_angle) < constants.GRID_ANGLE_TOLERANCE:
                            open_sides.append(s_idx)
                            break
            
            neighbors_map[slot['id']] = open_sides
            
        return neighbors_map
