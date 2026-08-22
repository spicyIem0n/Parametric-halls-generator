"""
InternalOfficeFactory — generuje antresole biurowe wewnątrz hali.

Antresola to niezależny układ konstrukcyjny (słupy + stropy) wewnątrz hali,
z opcjonalnym wydzieleniem pożarowym. Waliduje czy mieści się w clear_height.
"""

from models import Component3D, HallParameters, InternalOfficeConfig
from core.grid_system import GridSystem3D


class InternalOfficeFactory:
    COL_SECTION = 0.25          # Przekrój słupa antresoli [m]
    SLAB_THICKNESS = 0.20       # Grubość stropu [m]
    FIRE_WALL_THICKNESS = 0.20  # Ściana ppoż wokół antresoli [m]
    BALUSTRADE_HEIGHT = 1.1     # Wysokość balustrady [m]
    BALUSTRADE_THICKNESS = 0.05
    STAIR_WIDTH = 2.5
    STAIR_DEPTH = 5.0

    @staticmethod
    def generate(grid: GridSystem3D, params: HallParameters) -> list[Component3D]:
        elements = []

        if not params.internal_offices:
            return elements

        for office_config in params.internal_offices:
            # Walidacja: antresola nie może być wyższa niż clear_height
            max_height = office_config.num_floors * office_config.floor_height
            if max_height > params.clear_height:
                # Pomijamy — zbyt wysoka (frontend powinien ostrzec)
                continue
            elements.extend(InternalOfficeFactory._build_mezzanine(grid, params, office_config))

        return elements

    @staticmethod
    def _build_mezzanine(grid: GridSystem3D, params: HallParameters, config: InternalOfficeConfig) -> list[Component3D]:
        """Generuje kompletną antresolę biurową."""
        elements = []

        cx = config.position_x
        cz = config.position_z
        width = config.width
        length = config.length
        floor_h = config.floor_height
        num_floors = config.num_floors
        total_h = num_floors * floor_h

        col_grid_x = config.column_grid_x
        col_grid_z = config.column_grid_z
        cs = InternalOfficeFactory.COL_SECTION

        mez_meta = {
            "element_type": "internal_office",
            "office_id": config.office_id,
        }

        # --- 1. SŁUPY ANTRESOLI ---
        cols_x = [cx - width / 2]
        x = cx - width / 2 + col_grid_x
        while x < cx + width / 2 - 0.1:
            cols_x.append(x)
            x += col_grid_x
        cols_x.append(cx + width / 2)

        cols_z = [cz - length / 2]
        z = cz - length / 2 + col_grid_z
        while z < cz + length / 2 - 0.1:
            cols_z.append(z)
            z += col_grid_z
        cols_z.append(cz + length / 2)

        for col_x in cols_x:
            for col_z in cols_z:
                elements.append(Component3D(
                    type="mezzanine_column",
                    position=[col_x, total_h / 2, col_z],
                    rotation=[0, 0, 0],
                    scale=[cs, total_h, cs],
                    meta=dict(mez_meta)
                ))

        # --- 2. STROPY ---
        slab_t = InternalOfficeFactory.SLAB_THICKNESS
        for floor_idx in range(1, num_floors + 1):
            slab_y = floor_idx * floor_h
            elements.append(Component3D(
                type="mezzanine_slab",
                position=[cx, slab_y, cz],
                rotation=[0, 0, 0],
                scale=[width, slab_t, length],
                meta=dict(mez_meta)
            ))

        # --- 3. WYDZIELENIE POŻAROWE (opcjonalne) ---
        if config.fire_separation != "none":
            fw_t = InternalOfficeFactory.FIRE_WALL_THICKNESS
            fire_meta = {
                "fire_rating": config.fire_separation,
                "element_type": "mezzanine_fire_wall",
                "office_id": config.office_id,
            }

            # Ściana lewa (X-)
            elements.append(Component3D(
                type="mezzanine_fire_wall",
                position=[cx - width / 2 - fw_t / 2, total_h / 2, cz],
                rotation=[0, 0, 0],
                scale=[fw_t, total_h, length],
                meta=dict(fire_meta)
            ))
            # Ściana prawa (X+)
            elements.append(Component3D(
                type="mezzanine_fire_wall",
                position=[cx + width / 2 + fw_t / 2, total_h / 2, cz],
                rotation=[0, 0, 0],
                scale=[fw_t, total_h, length],
                meta=dict(fire_meta)
            ))
            # Ściana frontowa (Z-)
            elements.append(Component3D(
                type="mezzanine_fire_wall",
                position=[cx, total_h / 2, cz - length / 2 - fw_t / 2],
                rotation=[0, 0, 0],
                scale=[width, total_h, fw_t],
                meta=dict(fire_meta)
            ))
            # Ściana tylna (Z+)
            elements.append(Component3D(
                type="mezzanine_fire_wall",
                position=[cx, total_h / 2, cz + length / 2 + fw_t / 2],
                rotation=[0, 0, 0],
                scale=[width, total_h, fw_t],
                meta=dict(fire_meta)
            ))
        else:
            # Bez wydzielenia — balustrada na ostatniej kondygnacji
            bal_h = InternalOfficeFactory.BALUSTRADE_HEIGHT
            bal_t = InternalOfficeFactory.BALUSTRADE_THICKNESS
            bal_y = total_h + bal_h / 2

            # 4 strony balustrady
            elements.append(Component3D(type="mezzanine_balustrade", position=[cx - width / 2, bal_y, cz], rotation=[0, 0, 0], scale=[bal_t, bal_h, length], meta=dict(mez_meta)))
            elements.append(Component3D(type="mezzanine_balustrade", position=[cx + width / 2, bal_y, cz], rotation=[0, 0, 0], scale=[bal_t, bal_h, length], meta=dict(mez_meta)))
            elements.append(Component3D(type="mezzanine_balustrade", position=[cx, bal_y, cz - length / 2], rotation=[0, 0, 0], scale=[width, bal_h, bal_t], meta=dict(mez_meta)))
            elements.append(Component3D(type="mezzanine_balustrade", position=[cx, bal_y, cz + length / 2], rotation=[0, 0, 0], scale=[width, bal_h, bal_t], meta=dict(mez_meta)))

        # --- 4. SCHODY (symboliczne) ---
        if config.has_stairs_internal:
            stair_w = min(InternalOfficeFactory.STAIR_WIDTH, width * 0.3)
            stair_d = min(InternalOfficeFactory.STAIR_DEPTH, length * 0.3)

            elements.append(Component3D(
                type="mezzanine_stairs",
                position=[cx + width / 2 - stair_w / 2, total_h / 2, cz - length / 2 + stair_d / 2],
                rotation=[0, 0, 0],
                scale=[stair_w, total_h, stair_d],
                meta={**mez_meta, "element_type": "stairs"}
            ))

        return elements
