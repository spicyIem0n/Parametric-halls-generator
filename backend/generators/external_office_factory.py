"""
ExternalOfficeFactory — generuje zewnętrzne moduły biurowe ("doklejone" do hali).

Biuro zewnętrzne to wielokondygnacyjna dobudówka przylegająca do wybranej ściany hali.
Generuje: własną siatkę słupów, stropy między kondygnacjami, ściany zewnętrzne,
ścianę wspólną z halą (ppoż), stropodach płaski, schody (box symboliczny).
"""

from models import Component3D, HallParameters, ExternalOfficeConfig
from core.grid_system import GridSystem3D


class ExternalOfficeFactory:
    COL_GRID = 6.0          # Rozstaw słupów biurowych [m]
    COL_SECTION = 0.3       # Przekrój słupa biurowego [m]
    SLAB_THICKNESS = 0.22   # Grubość stropu [m]
    WALL_THICKNESS = 0.15   # Grubość ściany zewnętrznej biura [m]
    FIRE_WALL_THICKNESS = 0.24  # Ściana ppoż z halą [m]
    STAIR_WIDTH = 3.0       # Szerokość klatki schodowej [m]
    STAIR_DEPTH = 6.0       # Głębokość klatki schodowej [m]

    @staticmethod
    def generate(grid: GridSystem3D, params: HallParameters) -> list[Component3D]:
        elements = []

        if not params.external_offices:
            return elements

        for office_config in params.external_offices:
            elements.extend(ExternalOfficeFactory._build_office(grid, params, office_config))

        return elements

    @staticmethod
    def _compute_office_origin(grid: GridSystem3D, config: ExternalOfficeConfig) -> tuple:
        """
        Oblicza punkt odniesienia biura (środek rzutu w XZ).
        Biuro jest "doklejone" do ściany hali — jego krawędź przylega do lica hali.
        """
        hw = grid.half_width
        hl = grid.half_length
        depth = config.width  # Głębokość biura (prostopadle do hali)
        length = config.length  # Długość wzdłuż ściany

        wall = config.attached_wall
        pos_along = config.position_along_wall

        if wall == "left":
            # Biuro na lewo od hali (X ujemne)
            cx = -hw - depth / 2
            cz = -hl + pos_along + length / 2
        elif wall == "right":
            # Biuro na prawo od hali (X dodatnie)
            cx = hw + depth / 2
            cz = -hl + pos_along + length / 2
        elif wall == "front":
            # Biuro z przodu (Z ujemne)
            cx = -hw + pos_along + length / 2
            cz = -hl - depth / 2
        elif wall == "back":
            # Biuro z tyłu (Z dodatnie)
            cx = -hw + pos_along + length / 2
            cz = hl + depth / 2
        else:
            cx, cz = 0, 0

        return cx, cz, wall

    @staticmethod
    def _build_office(grid: GridSystem3D, params: HallParameters, config: ExternalOfficeConfig) -> list[Component3D]:
        """Generuje kompletny moduł biurowy zewnętrzny."""
        elements = []
        cx, cz, wall = ExternalOfficeFactory._compute_office_origin(grid, config)

        depth = config.width   # Głębokość (prostopadle)
        length = config.length  # Wzdłuż ściany
        floor_h = config.floor_height
        num_floors = config.num_floors
        total_h = num_floors * floor_h

        # Orientacja: dla left/right biuro rozciąga się wzdłuż Z, głębokość w X
        # Dla front/back biuro rozciąga się wzdłuż X, głębokość w Z
        is_side = wall in ("left", "right")

        office_meta = {
            "element_type": "external_office",
            "office_id": config.office_id,
        }

        # --- 1. SŁUPY BIUROWE ---
        col_grid = ExternalOfficeFactory.COL_GRID
        cs = ExternalOfficeFactory.COL_SECTION

        if is_side:
            # Siatka słupów w XZ: głębokość w X, długość w Z
            cols_x = [cx - depth / 2]
            x = cx - depth / 2 + col_grid
            while x < cx + depth / 2 - 0.1:
                cols_x.append(x)
                x += col_grid
            cols_x.append(cx + depth / 2)

            cols_z = [cz - length / 2]
            z = cz - length / 2 + col_grid
            while z < cz + length / 2 - 0.1:
                cols_z.append(z)
                z += col_grid
            cols_z.append(cz + length / 2)
        else:
            cols_x = [cx - length / 2]
            x = cx - length / 2 + col_grid
            while x < cx + length / 2 - 0.1:
                cols_x.append(x)
                x += col_grid
            cols_x.append(cx + length / 2)

            cols_z = [cz - depth / 2]
            z = cz - depth / 2 + col_grid
            while z < cz + depth / 2 - 0.1:
                cols_z.append(z)
                z += col_grid
            cols_z.append(cz + depth / 2)

        for col_x in cols_x:
            for col_z in cols_z:
                elements.append(Component3D(
                    type="office_column",
                    position=[col_x, total_h / 2, col_z],
                    rotation=[0, 0, 0],
                    scale=[cs, total_h, cs],
                    meta=dict(office_meta)
                ))

        # --- 2. STROPY MIĘDZY KONDYGNACJAMI ---
        slab_t = ExternalOfficeFactory.SLAB_THICKNESS
        if is_side:
            slab_scale = [depth, slab_t, length]
        else:
            slab_scale = [length, slab_t, depth]

        for floor_idx in range(1, num_floors):
            slab_y = floor_idx * floor_h
            elements.append(Component3D(
                type="office_slab",
                position=[cx, slab_y, cz],
                rotation=[0, 0, 0],
                scale=slab_scale,
                meta=dict(office_meta)
            ))

        # --- 3. STROPODACH PŁASKI ---
        elements.append(Component3D(
            type="office_roof",
            position=[cx, total_h + slab_t / 2, cz],
            rotation=[0, 0, 0],
            scale=slab_scale,
            meta=dict(office_meta)
        ))

        # --- 4. ŚCIANY ZEWNĘTRZNE (3 strony — czwarta = ściana wspólna z halą) ---
        wt = ExternalOfficeFactory.WALL_THICKNESS

        if is_side:
            # Ściana frontowa (Z-)
            elements.append(Component3D(
                type="office_wall",
                position=[cx, total_h / 2, cz - length / 2 - wt / 2],
                rotation=[0, 0, 0],
                scale=[depth, total_h, wt],
                meta=dict(office_meta)
            ))
            # Ściana tylna (Z+)
            elements.append(Component3D(
                type="office_wall",
                position=[cx, total_h / 2, cz + length / 2 + wt / 2],
                rotation=[0, 0, 0],
                scale=[depth, total_h, wt],
                meta=dict(office_meta)
            ))
            # Ściana zewnętrzna (daleka od hali)
            far_x = cx + depth / 2 + wt / 2 if wall == "right" else cx - depth / 2 - wt / 2
            elements.append(Component3D(
                type="office_wall",
                position=[far_x, total_h / 2, cz],
                rotation=[0, 0, 0],
                scale=[wt, total_h, length],
                meta=dict(office_meta)
            ))
        else:
            # Ściana lewa (X-)
            elements.append(Component3D(
                type="office_wall",
                position=[cx - length / 2 - wt / 2, total_h / 2, cz],
                rotation=[0, 0, 0],
                scale=[wt, total_h, depth],
                meta=dict(office_meta)
            ))
            # Ściana prawa (X+)
            elements.append(Component3D(
                type="office_wall",
                position=[cx + length / 2 + wt / 2, total_h / 2, cz],
                rotation=[0, 0, 0],
                scale=[wt, total_h, depth],
                meta=dict(office_meta)
            ))
            # Ściana zewnętrzna (daleka od hali)
            far_z = cz + depth / 2 + wt / 2 if wall == "back" else cz - depth / 2 - wt / 2
            elements.append(Component3D(
                type="office_wall",
                position=[cx, total_h / 2, far_z],
                rotation=[0, 0, 0],
                scale=[length, total_h, wt],
                meta=dict(office_meta)
            ))

        # --- 5. ŚCIANA WSPÓLNA Z HALĄ (PPOŻ) ---
        fw_t = ExternalOfficeFactory.FIRE_WALL_THICKNESS
        fire_meta = {
            "fire_rating": config.fire_separation,
            "element_type": "office_fire_wall",
            "office_id": config.office_id,
        }

        if is_side:
            near_x = cx + depth / 2 + fw_t / 2 if wall == "left" else cx - depth / 2 - fw_t / 2
            elements.append(Component3D(
                type="office_fire_wall",
                position=[near_x, total_h / 2, cz],
                rotation=[0, 0, 0],
                scale=[fw_t, total_h, length],
                meta=fire_meta
            ))
        else:
            near_z = cz + depth / 2 + fw_t / 2 if wall == "front" else cz - depth / 2 - fw_t / 2
            elements.append(Component3D(
                type="office_fire_wall",
                position=[cx, total_h / 2, near_z],
                rotation=[0, 0, 0],
                scale=[length, total_h, fw_t],
                meta=fire_meta
            ))

        # --- 6. SCHODY (symboliczny box) ---
        if num_floors > 1:
            stair_w = min(ExternalOfficeFactory.STAIR_WIDTH, depth * 0.4)
            stair_d = min(ExternalOfficeFactory.STAIR_DEPTH, length * 0.3)

            if is_side:
                stair_pos = [cx, total_h / 2, cz + length / 2 - stair_d / 2 - 1.0]
                stair_scale = [stair_w, total_h, stair_d]
            else:
                stair_pos = [cx + length / 2 - stair_d / 2 - 1.0, total_h / 2, cz]
                stair_scale = [stair_d, total_h, stair_w]

            elements.append(Component3D(
                type="office_stairs",
                position=stair_pos,
                rotation=[0, 0, 0],
                scale=stair_scale,
                meta={**office_meta, "element_type": "stairs"}
            ))

        return elements
