"""
CladdingFactory — generuje obudowę ścian z płyt warstwowych.

Zrefaktoryzowany: korzysta z GridSystem3D zamiast samodzielnych obliczeń.
"""

import math
from models import Component3D, HallParameters
from core.grid_system import GridSystem3D
from core.defaults import DEFAULTS


def _build_wall_with_hole(x, z_center, bay_len, t, parapet_h, hole_w, hole_h, hole_y_start):
    """Zestawia ścianę z paneli omijając otwór na dok/bramę."""
    pieces = []
    # 1. Lewy i prawy panel boczny
    side_w = (bay_len - hole_w) / 2
    if side_w > 0:
        pieces.append(Component3D(type="sandwich_panel", position=[x, parapet_h / 2, z_center - bay_len / 2 + side_w / 2], rotation=[0, 0, 0], scale=[t, parapet_h, side_w]))
        pieces.append(Component3D(type="sandwich_panel", position=[x, parapet_h / 2, z_center + bay_len / 2 - side_w / 2], rotation=[0, 0, 0], scale=[t, parapet_h, side_w]))

    # 2. Górny panel (nad otworem do attyki)
    hole_top = hole_y_start + hole_h
    top_h = parapet_h - hole_top
    if top_h > 0:
        pieces.append(Component3D(type="sandwich_panel", position=[x, hole_top + top_h / 2, z_center], rotation=[0, 0, 0], scale=[t, top_h, hole_w]))

    # 3. Dolny panel (pod dokiem)
    if hole_y_start > 0:
        pieces.append(Component3D(type="sandwich_panel", position=[x, hole_y_start / 2, z_center], rotation=[0, 0, 0], scale=[t, hole_y_start, hole_w]))

    return pieces


class CladdingFactory:
    @staticmethod
    def generate(grid: GridSystem3D, params: HallParameters) -> list[Component3D]:
        elements = []
        t = params.cladding_thickness
        parapet_h = grid.get_parapet_height()

        # --- ŚCIANY WZDŁUŻNE ---
        for bay_idx in range(grid.num_bays):
            for slot_idx in range(grid.slots_per_bay):
                z_center = grid.get_slot_center_z(bay_idx, slot_idx)

                for side in ["left", "right"]:
                    cladding_x = grid.get_cladding_x(side)
                    dock_type = grid.get_dock_type_at_slot(side, bay_idx, slot_idx)

                    if dock_type == "dock":
                        elements.extend(_build_wall_with_hole(
                            cladding_x, z_center, grid.slot_width, t, parapet_h,
                            DEFAULTS.dock_door_width, DEFAULTS.dock_door_height, 0.0
                        ))
                    elif dock_type == "gate":
                        elements.extend(_build_wall_with_hole(
                            cladding_x, z_center, grid.slot_width, t, parapet_h,
                            DEFAULTS.gate_door_width, DEFAULTS.gate_door_height, 0.0
                        ))
                    else:
                        elements.append(Component3D(
                            type="sandwich_panel",
                            position=[cladding_x, parapet_h / 2, z_center],
                            rotation=[0, 0, 0],
                            scale=[t, parapet_h, grid.slot_width]
                        ))

        # --- ZAMKNIĘCIE NAROŻNIKÓW (SZCZYTY) ---
        total_ext_width = grid.width + grid.col_width + (2 * t)

        elements.append(Component3D(
            type="sandwich_panel",
            position=[0, parapet_h / 2, -grid.half_length - grid.col_width / 2 - t / 2],
            rotation=[0, 0, 0],
            scale=[total_ext_width, parapet_h, t]
        ))
        elements.append(Component3D(
            type="sandwich_panel",
            position=[0, parapet_h / 2, grid.half_length + grid.col_width / 2 + t / 2],
            rotation=[0, 0, 0],
            scale=[total_ext_width, parapet_h, t]
        ))

        return elements
