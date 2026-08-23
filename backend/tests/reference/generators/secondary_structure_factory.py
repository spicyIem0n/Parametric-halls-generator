"""
SecondaryStructureFactory — generuje rygle ścienne i wymiany wokół otworów.

Rygle ścienne (girts): poziome profile co ~2.5m wysokości na ścianach bocznych
i szczytowych, służące jako podpora dla płyt warstwowych.

Wymiany (trimmers): ramki (nadproże + słupki boczne) otaczające otwory
na doki i bramy, dające krawędź oparcia płytom warstwowym.
"""

from models import Component3D, HallParameters
from core.grid_system import GridSystem3D
from core.defaults import DEFAULTS


class SecondaryStructureFactory:
    # Parametry rygli
    GIRT_SPACING = 2.5      # Rozstaw rygli [m]
    GIRT_SECTION = 0.08     # Przekrój rygla (grubość profilu Z/C)
    TRIMMER_SECTION = 0.10  # Przekrój wymianów

    @staticmethod
    def generate(grid: GridSystem3D, params: HallParameters) -> list[Component3D]:
        elements = []

        # 1. RYGLE ŚCIENNE NA ŚCIANACH BOCZNYCH
        elements.extend(SecondaryStructureFactory._generate_wall_girts(grid, params))

        # 2. RYGLE NA ŚCIANACH SZCZYTOWYCH
        elements.extend(SecondaryStructureFactory._generate_gable_girts(grid, params))

        # 3. WYMIANY WOKÓŁ OTWORÓW
        elements.extend(SecondaryStructureFactory._generate_trimmers(grid, params))

        return elements

    @staticmethod
    def _generate_wall_girts(grid: GridSystem3D, params: HallParameters) -> list[Component3D]:
        """Generuje rygle ścienne na ścianach bocznych (left/right)."""
        elements = []
        t = SecondaryStructureFactory.GIRT_SECTION
        parapet_h = grid.get_parapet_height()

        # Oblicz rzędne rygli (co GIRT_SPACING od plinth_top do parapet)
        girt_levels = []
        y = params.plinth_top_level + SecondaryStructureFactory.GIRT_SPACING
        while y < parapet_h - 0.5:
            girt_levels.append(y)
            y += SecondaryStructureFactory.GIRT_SPACING

        for side in ["left", "right"]:
            x_pos = -grid.half_width if side == "left" else grid.half_width

            for bay_idx in range(grid.num_bays):
                z1 = grid.axes_z[bay_idx]
                z2 = grid.axes_z[bay_idx + 1]
                bay_len = z2 - z1
                z_center = (z1 + z2) / 2

                # Sprawdź czy w tym przęśle są otwory
                has_any_opening = False
                for slot_idx in range(grid.slots_per_bay):
                    if grid.get_dock_type_at_slot(side, bay_idx, slot_idx) != "none":
                        has_any_opening = True
                        break

                if not has_any_opening:
                    # Pełne rygle na całej długości przęsła
                    for y_pos in girt_levels:
                        elements.append(Component3D(
                            type="girt",
                            position=[x_pos, y_pos, z_center],
                            rotation=[0, 0, 0],
                            scale=[t, t, bay_len]
                        ))
                # Jeśli są otwory — rygle generowane przez _generate_trimmers (powyżej otworów)

        return elements

    @staticmethod
    def _generate_gable_girts(grid: GridSystem3D, params: HallParameters) -> list[Component3D]:
        """Generuje rygle na ścianach szczytowych (front/back)."""
        elements = []
        t = SecondaryStructureFactory.GIRT_SECTION
        parapet_h = grid.get_parapet_height()

        girt_levels = []
        y = params.plinth_top_level + SecondaryStructureFactory.GIRT_SPACING
        while y < parapet_h - 0.5:
            girt_levels.append(y)
            y += SecondaryStructureFactory.GIRT_SPACING

        for z_pos in [grid.axes_z[0], grid.axes_z[-1]]:
            for y_pos in girt_levels:
                elements.append(Component3D(
                    type="girt",
                    position=[0, y_pos, z_pos],
                    rotation=[0, 0, 0],
                    scale=[grid.width, t, t]
                ))

        return elements

    @staticmethod
    def _generate_trimmers(grid: GridSystem3D, params: HallParameters) -> list[Component3D]:
        """Generuje wymiany (ramki) wokół otworów — nadproże + słupki boczne."""
        elements = []
        t = SecondaryStructureFactory.TRIMMER_SECTION

        for side in ["left", "right"]:
            x_pos = -grid.half_width if side == "left" else grid.half_width

            for bay_idx in range(grid.num_bays):
                for slot_idx in range(grid.slots_per_bay):
                    dock_type = grid.get_dock_type_at_slot(side, bay_idx, slot_idx)
                    if dock_type == "none":
                        continue

                    z_center = grid.get_slot_center_z(bay_idx, slot_idx)
                    door_w = DEFAULTS.dock_door_width if dock_type == "dock" else DEFAULTS.gate_door_width
                    door_h = DEFAULTS.dock_door_height if dock_type == "dock" else DEFAULTS.gate_door_height

                    # Nadproże (belka pozioma nad otworem)
                    lintel_y = door_h + t / 2
                    elements.append(Component3D(
                        type="trimmer",
                        position=[x_pos, lintel_y, z_center],
                        rotation=[0, 0, 0],
                        scale=[t, t, door_w + 0.2]  # Lekko szersze niż otwór
                    ))

                    # Słupki boczne (pionowe po bokach otworu)
                    for z_offset in [-door_w / 2, door_w / 2]:
                        post_h = door_h
                        elements.append(Component3D(
                            type="trimmer",
                            position=[x_pos, post_h / 2, z_center + z_offset],
                            rotation=[0, 0, 0],
                            scale=[t, post_h, t]
                        ))

                    # Rygle powyżej otworu (od nadproża do attyki)
                    parapet_h = grid.get_parapet_height()
                    y = lintel_y + SecondaryStructureFactory.GIRT_SPACING
                    while y < parapet_h - 0.5:
                        elements.append(Component3D(
                            type="girt",
                            position=[x_pos, y, z_center],
                            rotation=[0, 0, 0],
                            scale=[t, t, grid.slot_width]
                        ))
                        y += SecondaryStructureFactory.GIRT_SPACING

        return elements
