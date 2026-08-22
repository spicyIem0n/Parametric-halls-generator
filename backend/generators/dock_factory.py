"""
DockFactory — generuje doki przeładunkowe i bramy kurierskie.

Zrefaktoryzowany: korzysta z GridSystem3D zamiast samodzielnych obliczeń.
"""

from models import Component3D, HallParameters
from core.grid_system import GridSystem3D
from core.defaults import DEFAULTS


class DockFactory:
    @staticmethod
    def generate(grid: GridSystem3D, params: HallParameters) -> list[Component3D]:
        elements = []

        for bay_idx in range(grid.num_bays):
            for slot_idx in range(grid.slots_per_bay):
                z_center = grid.get_slot_center_z(bay_idx, slot_idx)

                # --- LEWA ŚCIANA ---
                left_type = grid.get_dock_type_at_slot("left", bay_idx, slot_idx)
                if left_type == "dock":
                    elements.extend(DockFactory._build_dock(grid.get_ext_face_x("left"), z_center, -1))
                elif left_type == "gate":
                    elements.extend(DockFactory._build_gate(grid.get_ext_face_x("left"), z_center, -1))

                # --- PRAWA ŚCIANA ---
                right_type = grid.get_dock_type_at_slot("right", bay_idx, slot_idx)
                if right_type == "dock":
                    elements.extend(DockFactory._build_dock(grid.get_ext_face_x("right"), z_center, 1))
                elif right_type == "gate":
                    elements.extend(DockFactory._build_gate(grid.get_ext_face_x("right"), z_center, 1))

        return elements

    @staticmethod
    def _build_dock(x, z, direction):
        """Generuje model doku opuszczonego na poziom 0 z fartuchem uszczelniającym."""
        elements = []
        dock_h = 0.0

        door_w = DEFAULTS.dock_door_width
        door_h = DEFAULTS.dock_door_height

        # Brama (opuszczona)
        elements.append(Component3D(
            type="dock_door",
            position=[x, dock_h + door_h / 2, z],
            rotation=[0, 0, 0],
            scale=[0.1, door_h, door_w]
        ))

        # Fartuch uszczelniający
        shelter_depth = DEFAULTS.dock_shelter_depth
        shelter_x = x + (direction * shelter_depth / 2)

        # Górna belka fartucha
        elements.append(Component3D(
            type="dock_shelter",
            position=[shelter_x, dock_h + door_h + 0.15, z],
            rotation=[0, 0, 0],
            scale=[shelter_depth, 0.3, door_w + 0.6]
        ))
        # Boczne piony fartucha
        elements.append(Component3D(
            type="dock_shelter",
            position=[shelter_x, dock_h + door_h / 2, z - door_w / 2 - 0.15],
            rotation=[0, 0, 0],
            scale=[shelter_depth, door_h, 0.3]
        ))
        elements.append(Component3D(
            type="dock_shelter",
            position=[shelter_x, dock_h + door_h / 2, z + door_w / 2 + 0.15],
            rotation=[0, 0, 0],
            scale=[shelter_depth, door_h, 0.3]
        ))

        return elements

    @staticmethod
    def _build_gate(x, z, direction):
        """Generuje bramę kurierską z poziomu 0.00."""
        elements = []
        door_w = DEFAULTS.gate_door_width
        door_h = DEFAULTS.gate_door_height

        elements.append(Component3D(
            type="gate_door",
            position=[x, door_h / 2, z],
            rotation=[0, 0, 0],
            scale=[0.1, door_h, door_w]
        ))

        return elements
