"""
FireWallFactory — generuje ściany oddzielenia pożarowego (ŚOP).

ŚOP to nadrzędne elementy dzielące model na osobne strefy pożarowe.
Generowane na wybranych osiach Z (ramach) z automatyczną geometrią:
- Ściana od fundamentu do Z_Eave + attyka (0.30m ponad dach)
- Opcjonalnie: pas dachu nierozprzestrzeniającego ognia (8m) zamiast attyki
"""

from models import Component3D, HallParameters, FireWallConfig
from core.grid_system import GridSystem3D
from core.defaults import DEFAULTS


class FireWallFactory:
    @staticmethod
    def generate(grid: GridSystem3D, params: HallParameters) -> list[Component3D]:
        elements = []

        if not params.fire_walls:
            return elements

        for fw_config in params.fire_walls:
            elements.extend(FireWallFactory._build_fire_wall(grid, params, fw_config))

        return elements

    @staticmethod
    def _build_fire_wall(grid: GridSystem3D, params: HallParameters, config: FireWallConfig) -> list[Component3D]:
        """Generuje pojedynczą ścianę oddzielenia pożarowego na danej osi."""
        elements = []

        axis_index = config.axis_index

        # Walidacja — oś musi być w zakresie
        if axis_index < 0 or axis_index >= grid.num_frames:
            return elements

        z_pos = grid.axes_z[axis_index]

        # Wymiary ściany
        wall_thickness = 0.24  # Typowa grubość ściany ŚOP (beton/cegła)
        wall_width = grid.width  # Pełna szerokość hali

        # Rzędne
        foundation_depth = params.foundation_depth
        wall_base_y = -foundation_depth

        if config.top_type == "parapet_above_roof":
            # Ściana wystaje 0.30m ponad najwyższy punkt dachu
            parapet_h = grid.get_parapet_height()
            wall_top_y = parapet_h + 0.10  # Lekko ponad attykę obudowy
        else:
            # Ściana do poziomu dachu (bez wystania)
            wall_top_y = grid.get_parapet_height() - DEFAULTS.parapet_extension

        wall_height = wall_top_y - wall_base_y

        # Główna ściana ŚOP
        elements.append(Component3D(
            type="fire_wall",
            position=[0, wall_base_y + wall_height / 2, z_pos],
            rotation=[0, 0, 0],
            scale=[wall_width, wall_height, wall_thickness],
            meta={
                "fire_rating": config.rei_class,
                "element_type": "fire_separation_wall",
                "top_type": config.top_type,
            }
        ))

        # Jeśli typ "non_combustible_strip" — generujemy pas niepalny na dachu
        if config.top_type == "non_combustible_strip":
            strip_width = 8.0  # 4m na każdą stronę od osi ściany
            strip_thickness = params.roof_panel_thickness
            roof_y = grid.z_levels["Z_Eave"] + strip_thickness / 2

            elements.append(Component3D(
                type="fire_strip_roof",
                position=[0, roof_y, z_pos],
                rotation=[0, 0, 0],
                scale=[wall_width, strip_thickness, strip_width],
                meta={
                    "fire_rating": config.rei_class,
                    "element_type": "non_combustible_roof_strip",
                    "description": "Pas dachu z materialow niepalnych (welna mineralna)",
                }
            ))

        return elements
