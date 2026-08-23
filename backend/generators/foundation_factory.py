"""
FoundationFactory — generuje stopy fundamentowe pod wszystkie typy słupów.

Zrefaktoryzowany: korzysta z GridSystem3D zamiast samodzielnych obliczeń siatki.
"""

from models import Component3D, HallParameters
from core.grid_system import GridSystem3D
from core.defaults import DEFAULTS


class FoundationFactory:
    # Zachowujemy DEFAULT_SIZES jako atrybut klasy dla kompatybilności wstecznej
    # (PlinthFactory jeszcze może go potrzebować w fazie przejściowej)
    DEFAULT_SIZES = DEFAULTS.foundation_sizes

    @staticmethod
    def generate(grid: GridSystem3D, params: HallParameters) -> list[Component3D]:
        elements = []

        # Dobór gabarytów (manual / default)
        manual_sizes = params.manual_sizes if params.manual_sizes else {}

        def _get_size(category):
            if params.foundation_method == "manual":
                return manual_sizes.get(category, DEFAULTS.foundation_sizes.get(category, [2.0, 2.0, 0.5]))
            return DEFAULTS.foundation_sizes.get(category, [2.0, 2.0, 0.5])

        # 1. STOPY POD RAMY GŁÓWNE
        for frame_idx in range(grid.num_frames):
            for axis_idx in range(len(grid.axes_x)):
                node = grid.get_node(frame_idx, axis_idx)

                is_corner = node.is_external and (frame_idx == 0 or frame_idx == grid.num_frames - 1)
                if is_corner:
                    size = _get_size("external_corner")
                elif node.is_external:
                    size = _get_size("external_main")
                else:
                    size = _get_size("internal_main")

                y_pos = node.y_foundation + (size[2] / 2)

                elements.append(Component3D(
                    type="foundation",
                    position=[node.x, y_pos, node.z],
                    rotation=[0, 0, 0],
                    scale=[size[0], size[2], size[1]]
                ))

        # 2. STOPY SZCZYTOWE
        for z_pos in [grid.axes_z[0], grid.axes_z[-1]]:
            for x_pos in grid.gable_xs:
                y_pos = -params.foundation_depth + (_get_size("external_intermediate_cladding")[2] / 2)
                elements.append(Component3D(
                    type="foundation",
                    position=[x_pos, y_pos, z_pos],
                    rotation=[0, 0, 0],
                    scale=[_get_size("external_intermediate_cladding")[0], _get_size("external_intermediate_cladding")[2], _get_size("external_intermediate_cladding")[1]]
                ))

        # 3. STOPY POŚREDNIE WZDŁUŻNE
        if params.bay_spacing >= 8.0:
            for bay_idx in range(grid.num_bays):
                z_mid = grid.get_intermediate_z(bay_idx)

                for side_str, x_pos in [("left", -grid.half_width), ("right", grid.half_width)]:
                    is_dock = grid.has_dock_in_bay(bay_idx, side_str)
                    depth = params.dock_foundation_depth if is_dock else params.foundation_depth

                    y_pos = -depth + (_get_size("external_intermediate_cladding")[2] / 2)

                    elements.append(Component3D(
                        type="foundation",
                        position=[x_pos, y_pos, z_mid],
                        rotation=[0, 0, 0],
                        scale=[_get_size("external_intermediate_cladding")[0], _get_size("external_intermediate_cladding")[2], _get_size("external_intermediate_cladding")[1]]
                    ))

        return elements
