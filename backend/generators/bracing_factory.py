"""
BracingFactory — generuje stężenia ścienne (X-bracing) i połaciowe dachowe.

Stężenia ścienne są pomijane w przęsłach z dokami/bramami.
Stężenia dachowe generowane w pierwszym i ostatnim polu dachu.
"""

import math
from models import Component3D, HallParameters
from core.grid_system import GridSystem3D
from core.defaults import DEFAULTS


class BracingFactory:
    @staticmethod
    def generate(grid: GridSystem3D, params: HallParameters) -> list[Component3D]:
        elements = []

        bracing_config = params.bracing_config

        # 1. STĘŻENIA ŚCIENNE (X-bracing na ścianach bocznych)
        wall_bays = bracing_config.wall_bracing_bays if bracing_config.wall_bracing_bays else BracingFactory._auto_select_wall_bays(grid, params)

        for bay_idx in wall_bays:
            if bay_idx < 0 or bay_idx >= grid.num_bays:
                continue
            elements.extend(BracingFactory._generate_wall_bracing(grid, params, bay_idx))

        # 2. STĘŻENIA POŁACIOWE (na dachu)
        if bracing_config.roof_bracing:
            elements.extend(BracingFactory._generate_roof_bracing(grid, params))

        return elements

    @staticmethod
    def _auto_select_wall_bays(grid: GridSystem3D, params: HallParameters) -> list:
        """
        Automatyczny dobór przęseł ze stężeniami ściennymi.
        Reguła: pierwsze i ostatnie przęsło + co ~30m w środku.
        Pomija przęsła z dokami.
        """
        bays = []
        # Pierwsze przęsło
        if not BracingFactory._bay_has_openings(grid, 0):
            bays.append(0)
        # Ostatnie przęsło
        last = grid.num_bays - 1
        if not BracingFactory._bay_has_openings(grid, last):
            bays.append(last)
        # Środkowe co ~30m
        interval = max(1, int(30.0 / params.bay_spacing))
        for i in range(interval, grid.num_bays - 1, interval):
            if i not in bays and not BracingFactory._bay_has_openings(grid, i):
                bays.append(i)
        return sorted(set(bays))

    @staticmethod
    def _bay_has_openings(grid: GridSystem3D, bay_idx: int) -> bool:
        """Sprawdza czy w przęśle (po obu stronach) są jakiekolwiek otwory."""
        for side in ["left", "right"]:
            for slot_idx in range(grid.slots_per_bay):
                if grid.get_dock_type_at_slot(side, bay_idx, slot_idx) != "none":
                    return True
        return False

    @staticmethod
    def _generate_wall_bracing(grid: GridSystem3D, params: HallParameters, bay_idx: int) -> list[Component3D]:
        """Generuje stężenie X na ścianach bocznych w danym przęśle."""
        elements = []

        z1 = grid.axes_z[bay_idx]
        z2 = grid.axes_z[bay_idx + 1]
        z_mid = (z1 + z2) / 2

        # Profil stężenia (cienki pręt/rura)
        brace_t = 0.06  # grubość przekroju

        for side in ["left", "right"]:
            # Sprawdź czy ta strona nie ma otworów w tym przęśle
            has_opening = False
            for slot_idx in range(grid.slots_per_bay):
                if grid.get_dock_type_at_slot(side, bay_idx, slot_idx) != "none":
                    has_opening = True
                    break

            if has_opening:
                continue

            x_pos = -grid.half_width if side == "left" else grid.half_width

            # Wysokość stężenia: od plinth_top (0.30) do clear_height
            y_bot = params.plinth_top_level
            y_top = params.clear_height

            # Stężenie X: dwie przekątne
            # Przekątna 1: (z1, y_bot) → (z2, y_top)
            diag_len = math.sqrt((z2 - z1) ** 2 + (y_top - y_bot) ** 2)
            diag_angle = math.atan2(y_top - y_bot, z2 - z1)
            cx1 = (z1 + z2) / 2
            cy1 = (y_bot + y_top) / 2

            elements.append(Component3D(
                type="bracing",
                position=[x_pos, cy1, cx1],
                rotation=[diag_angle, 0, 0],
                scale=[brace_t, brace_t, diag_len]
            ))

            # Przekątna 2: (z1, y_top) → (z2, y_bot)
            diag_angle2 = math.atan2(y_bot - y_top, z2 - z1)
            elements.append(Component3D(
                type="bracing",
                position=[x_pos, cy1, cx1],
                rotation=[diag_angle2, 0, 0],
                scale=[brace_t, brace_t, diag_len]
            ))

        return elements

    @staticmethod
    def _generate_roof_bracing(grid: GridSystem3D, params: HallParameters) -> list[Component3D]:
        """Generuje stężenia połaciowe na dachu (w pierwszym i ostatnim polu)."""
        elements = []

        brace_t = 0.05  # Cieńszy profil na dachu
        roof_y = grid.z_levels["Z_Eave"]  # Poziom oparcia na dźwigarach

        # Stężenia w pierwszym i ostatnim przęśle
        bracing_bays = [0, grid.num_bays - 1]
        # Dodaj środkowe co ~30m
        interval = max(1, int(30.0 / params.bay_spacing))
        for i in range(interval, grid.num_bays - 1, interval):
            if i not in bracing_bays:
                bracing_bays.append(i)

        for bay_idx in bracing_bays:
            if bay_idx >= grid.num_bays:
                continue

            z1 = grid.axes_z[bay_idx]
            z2 = grid.axes_z[bay_idx + 1]

            # Stężenie jako X w płaszczyźnie poziomej (XZ) na poziomie dachu
            # Rozciągamy na pół szerokości hali (od osi 0 do krawędzi)
            for x_sign in [-1, 1]:
                x1 = 0
                x2 = x_sign * grid.half_width

                # Przekątna 1: (x1, z1) → (x2, z2)
                dx = x2 - x1
                dz = z2 - z1
                diag_len = math.sqrt(dx ** 2 + dz ** 2)
                cx = (x1 + x2) / 2
                cz = (z1 + z2) / 2

                # Obrót wokół Y (w płaszczyźnie XZ)
                angle_y = math.atan2(dx, dz)

                elements.append(Component3D(
                    type="bracing_roof",
                    position=[cx, roof_y, cz],
                    rotation=[0, angle_y, 0],
                    scale=[brace_t, brace_t, diag_len]
                ))

                # Przekątna 2: (x1, z2) → (x2, z1)
                angle_y2 = math.atan2(dx, z1 - z2)
                elements.append(Component3D(
                    type="bracing_roof",
                    position=[cx, roof_y, cz],
                    rotation=[0, angle_y2, 0],
                    scale=[brace_t, brace_t, diag_len]
                ))

        return elements
