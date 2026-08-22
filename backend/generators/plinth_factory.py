"""
PlinthFactory — generuje podwaliny (belki podwalinowe) wokół obwodu hali.

Zrefaktoryzowany: korzysta z GridSystem3D i DEFAULTS zamiast importu z FoundationFactory.
"""

from models import Component3D, HallParameters
from core.grid_system import GridSystem3D
from core.defaults import DEFAULTS


class PlinthFactory:
    @staticmethod
    def generate(grid: GridSystem3D, params: HallParameters) -> list[Component3D]:
        elements = []
        pt = params.plinth_thickness

        # Wysokość stopy fundamentowej (potrzebna do obliczenia górnej krawędzi fundamentu)
        found_size_main = params.manual_sizes.get(
            "external_main", DEFAULTS.foundation_sizes["external_main"]
        ) if params.foundation_method == "manual" else DEFAULTS.foundation_sizes["external_main"]
        found_h = found_size_main[2]

        # 1. Ściany szczytowe
        found_top_gable = -params.foundation_depth + found_h
        plinth_h_gable = params.plinth_top_level - found_top_gable

        for z_pos in [grid.axes_z[0], grid.axes_z[-1]]:
            elements.append(Component3D(
                type="plinth",
                position=[0, found_top_gable + plinth_h_gable / 2, z_pos],
                rotation=[0, 0, 0],
                scale=[params.width, plinth_h_gable, pt]
            ))

        # 2. Ściany boczne (slot po slocie)
        for bay_idx in range(grid.num_bays):
            for side in ["left", "right"]:
                x_pos = -grid.half_width if side == "left" else grid.half_width

                for slot_idx in range(grid.slots_per_bay):
                    config_val = grid.get_dock_type_at_slot(side, bay_idx, slot_idx)
                    z_center = grid.get_slot_center_z(bay_idx, slot_idx)

                    is_dock = (config_val == "dock")
                    depth = params.dock_foundation_depth if is_dock else params.foundation_depth
                    found_top = -depth + found_h

                    if config_val == "none":
                        plinth_h = params.plinth_top_level - found_top
                        elements.append(Component3D(
                            type="plinth",
                            position=[x_pos, found_top + plinth_h / 2, z_center],
                            rotation=[0, 0, 0],
                            scale=[pt, plinth_h, grid.slot_width]
                        ))
                    else:
                        door_w = DEFAULTS.dock_door_width if config_val == "dock" else DEFAULTS.gate_door_width
                        side_w = (grid.slot_width - door_w) / 2
                        plinth_h_side = params.plinth_top_level - found_top

                        # Wąsy boczne (do plinth_top_level)
                        if side_w > 0:
                            elements.append(Component3D(
                                type="plinth",
                                position=[x_pos, found_top + plinth_h_side / 2, z_center - grid.slot_width / 2 + side_w / 2],
                                rotation=[0, 0, 0],
                                scale=[pt, plinth_h_side, side_w]
                            ))
                            elements.append(Component3D(
                                type="plinth",
                                position=[x_pos, found_top + plinth_h_side / 2, z_center + grid.slot_width / 2 - side_w / 2],
                                rotation=[0, 0, 0],
                                scale=[pt, plinth_h_side, side_w]
                            ))

                        # Podwalina pod bramą/dokiem (tylko do 0.00)
                        plinth_h_mid = 0.0 - found_top
                        if plinth_h_mid > 0:
                            elements.append(Component3D(
                                type="plinth",
                                position=[x_pos, found_top + plinth_h_mid / 2, z_center],
                                rotation=[0, 0, 0],
                                scale=[pt, plinth_h_mid, door_w]
                            ))

        return elements
