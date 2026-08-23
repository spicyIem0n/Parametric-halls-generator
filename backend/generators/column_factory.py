"""
ColumnFactory — generuje słupy ram głównych, szczytowe i pośrednie wzdłużne.

Zrefaktoryzowany: korzysta z GridSystem3D zamiast samodzielnych obliczeń siatki.
"""

import math
from models import Component3D, HallParameters
from core.grid_system import GridSystem3D
from core.defaults import DEFAULTS


class ColumnFactory:
    @staticmethod
    def generate(grid: GridSystem3D, params: HallParameters) -> list[Component3D]:
        columns = []

        # Dobór przekrojów (manual / default)
        manual_sections = params.manual_column_sections if params.manual_column_sections else {}

        def _get_section(category):
            if params.column_method == "manual":
                return manual_sections.get(category, DEFAULTS.column_sections.get(category, [0.4, 0.4]))
            return DEFAULTS.column_sections.get(category, [0.4, 0.4])

        # 1. SŁUPY RAM GŁÓWNYCH
        for frame_idx in range(grid.num_frames):
            for axis_idx in range(len(grid.axes_x)):
                node = grid.get_node(frame_idx, axis_idx)

                # Rozpoznanie kategorii: narożnik vs główny zewnętrzny vs wewnętrzny
                is_corner = node.is_external and (frame_idx == 0 or frame_idx == grid.num_frames - 1)
                if is_corner:
                    section = _get_section("external_corner")
                elif node.is_external:
                    section = _get_section("external_main")
                else:
                    section = _get_section("internal_main")

                column_top_y = node.y_roof
                column_base_y = node.y_foundation
                column_height = column_top_y - column_base_y

                columns.append(Component3D(
                    type="column",
                    position=[node.x, column_base_y + (column_height / 2), node.z],
                    rotation=[0, 0, 0],
                    scale=[section[0], column_height, section[1]]
                ))

        # 2. SŁUPY SZCZYTOWE (wiatrowe)
        for z_pos in [grid.axes_z[0], grid.axes_z[-1]]:
            for x_pos in grid.gable_xs:
                h_roof = grid.get_roof_height_at(x_pos)

                column_base_y = -params.foundation_depth
                column_height = h_roof - column_base_y

                columns.append(Component3D(
                    type="column_gable",
                    position=[x_pos, column_base_y + (column_height / 2), z_pos],
                    rotation=[0, 0, 0],
                    scale=[_get_section("external_intermediate_cladding")[0], column_height, _get_section("external_intermediate_cladding")[1]]
                ))

        # 3. SŁUPY POŚREDNIE WZDŁUŻNE
        if params.bay_spacing >= 8.0:
            for bay_idx in range(grid.num_bays):
                z_mid = grid.get_intermediate_z(bay_idx)

                for side_str, x_pos in [("left", -grid.half_width), ("right", grid.half_width)]:
                    is_dock = grid.has_dock_in_bay(bay_idx, side_str)
                    depth = params.dock_foundation_depth if is_dock else params.foundation_depth

                    column_base_y = -depth
                    h_roof = grid.get_roof_height_at(x_pos)
                    column_height = h_roof - column_base_y

                    columns.append(Component3D(
                        type="column_gable",
                        position=[x_pos, column_base_y + (column_height / 2), z_mid],
                        rotation=[0, 0, 0],
                        scale=[_get_section("external_intermediate_cladding")[0], column_height, _get_section("external_intermediate_cladding")[1]]
                    ))

        return columns
