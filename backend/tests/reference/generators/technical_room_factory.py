"""
TechnicalRoomFactory — generuje pomieszczenia techniczne wydzielone pożarowo.

Pomieszczenia techniczne (rozdzielnia, maszynownia, UPS, sprężarki) to
zamknięte boksy wewnątrz hali z pełnym wydzieleniem pożarowym (ściany REI).
Mogą być dostawione do narożnika hali (3 ściany wewnętrzne) lub wolnostojące (4 ściany).
"""

from models import Component3D, HallParameters, TechnicalRoomConfig
from core.grid_system import GridSystem3D


class TechnicalRoomFactory:
    WALL_THICKNESS = 0.24  # Grubość ściany ppoż [m]
    DOOR_WIDTH = 1.0       # Drzwi techniczne EI60 [m]
    DOOR_HEIGHT = 2.1      # Wysokość drzwi [m]

    @staticmethod
    def generate(grid: GridSystem3D, params: HallParameters) -> list[Component3D]:
        elements = []

        if not params.technical_rooms:
            return elements

        for room_config in params.technical_rooms:
            elements.extend(TechnicalRoomFactory._build_room(grid, params, room_config))

        return elements

    @staticmethod
    def _compute_room_position(grid: GridSystem3D, config: TechnicalRoomConfig) -> tuple:
        """Oblicza pozycję środka pomieszczenia na podstawie anchor."""
        hw = grid.half_width
        hl = grid.half_length
        rw = config.width / 2
        rl = config.length / 2
        t = TechnicalRoomFactory.WALL_THICKNESS

        anchor_map = {
            "corner_left_front": (-hw + rw + t, -hl + rl + t),
            "corner_right_front": (hw - rw - t, -hl + rl + t),
            "corner_left_back": (-hw + rw + t, hl - rl - t),
            "corner_right_back": (hw - rw - t, hl - rl - t),
            "custom": (config.position_offset[0], config.position_offset[2]),
        }

        x, z = anchor_map.get(config.position_anchor, (config.position_offset[0], config.position_offset[2]))

        if config.position_anchor != "custom":
            x += config.position_offset[0]
            z += config.position_offset[2]

        return x, z

    @staticmethod
    def _get_adjacent_walls(grid: GridSystem3D, cx: float, cz: float, config: TechnicalRoomConfig) -> dict:
        """
        Określa które ściany pomieszczenia przylegają do ścian hali.
        Jeśli krawędź pomieszczenia jest blisko ściany hali (< 0.5m), pomijamy tę ścianę wewnętrzną.
        """
        hw = grid.half_width
        hl = grid.half_length
        rw = config.width / 2
        rl = config.length / 2
        threshold = 0.5

        return {
            "left": abs((cx - rw) - (-hw)) < threshold,   # Pomieszczenie przy lewej ścianie
            "right": abs((cx + rw) - hw) < threshold,     # Pomieszczenie przy prawej ścianie
            "front": abs((cz - rl) - (-hl)) < threshold,  # Pomieszczenie przy ścianie frontowej
            "back": abs((cz + rl) - hl) < threshold,      # Pomieszczenie przy ścianie tylnej
        }

    @staticmethod
    def _build_room(grid: GridSystem3D, params: HallParameters, config: TechnicalRoomConfig) -> list[Component3D]:
        """Generuje pojedyncze pomieszczenie techniczne."""
        elements = []
        t = TechnicalRoomFactory.WALL_THICKNESS
        cx, cz = TechnicalRoomFactory._compute_room_position(grid, config)

        room_w = config.width
        room_l = config.length
        room_h = config.height
        floor_y = config.floor_level

        # Środek Y ścian
        wall_cy = floor_y + room_h / 2

        # Które ściany pomijamy (przylegają do ściany hali)
        adjacent = TechnicalRoomFactory._get_adjacent_walls(grid, cx, cz, config)

        meta = {
            "fire_rating": config.fire_rating,
            "element_type": "technical_room_wall",
            "room_id": config.room_id,
        }

        # --- ŚCIANY ---
        # Lewa ściana pomieszczenia (w osi X, patrząc od wewnątrz)
        if not adjacent["left"]:
            elements.append(Component3D(
                type="tech_room_wall",
                position=[cx - room_w / 2 - t / 2, wall_cy, cz],
                rotation=[0, 0, 0],
                scale=[t, room_h, room_l],
                meta=dict(meta)
            ))

        # Prawa ściana
        if not adjacent["right"]:
            elements.append(Component3D(
                type="tech_room_wall",
                position=[cx + room_w / 2 + t / 2, wall_cy, cz],
                rotation=[0, 0, 0],
                scale=[t, room_h, room_l],
                meta=dict(meta)
            ))

        # Frontowa ściana (Z-)
        if not adjacent["front"]:
            elements.append(Component3D(
                type="tech_room_wall",
                position=[cx, wall_cy, cz - room_l / 2 - t / 2],
                rotation=[0, 0, 0],
                scale=[room_w, room_h, t],
                meta=dict(meta)
            ))

        # Tylna ściana (Z+)
        if not adjacent["back"]:
            elements.append(Component3D(
                type="tech_room_wall",
                position=[cx, wall_cy, cz + room_l / 2 + t / 2],
                rotation=[0, 0, 0],
                scale=[room_w, room_h, t],
                meta=dict(meta)
            ))

        # --- STROP (opcjonalny) ---
        if config.has_own_roof:
            slab_thickness = 0.20
            elements.append(Component3D(
                type="tech_room_slab",
                position=[cx, floor_y + room_h + slab_thickness / 2, cz],
                rotation=[0, 0, 0],
                scale=[room_w + 2 * t, slab_thickness, room_l + 2 * t],
                meta={
                    "fire_rating": config.fire_rating,
                    "element_type": "technical_room_slab",
                    "room_id": config.room_id,
                }
            ))

        # --- DRZWI TECHNICZNE EI60 ---
        # Umieszczamy drzwi na ścianie, która NIE przylega do ściany hali
        # Priorytet: frontowa > lewa > prawa > tylna
        door_meta = {
            "fire_rating": "EI60",
            "element_type": "technical_door",
            "room_id": config.room_id,
        }

        door_placed = False
        if not adjacent["front"]:
            elements.append(Component3D(
                type="tech_room_door",
                position=[cx, floor_y + TechnicalRoomFactory.DOOR_HEIGHT / 2, cz - room_l / 2 - t / 2],
                rotation=[0, 0, 0],
                scale=[TechnicalRoomFactory.DOOR_WIDTH, TechnicalRoomFactory.DOOR_HEIGHT, 0.05],
                meta=door_meta
            ))
            door_placed = True
        elif not adjacent["left"]:
            elements.append(Component3D(
                type="tech_room_door",
                position=[cx - room_w / 2 - t / 2, floor_y + TechnicalRoomFactory.DOOR_HEIGHT / 2, cz],
                rotation=[0, 0, 0],
                scale=[0.05, TechnicalRoomFactory.DOOR_HEIGHT, TechnicalRoomFactory.DOOR_WIDTH],
                meta=door_meta
            ))
            door_placed = True
        elif not adjacent["right"]:
            elements.append(Component3D(
                type="tech_room_door",
                position=[cx + room_w / 2 + t / 2, floor_y + TechnicalRoomFactory.DOOR_HEIGHT / 2, cz],
                rotation=[0, 0, 0],
                scale=[0.05, TechnicalRoomFactory.DOOR_HEIGHT, TechnicalRoomFactory.DOOR_WIDTH],
                meta=door_meta
            ))
            door_placed = True
        elif not adjacent["back"]:
            elements.append(Component3D(
                type="tech_room_door",
                position=[cx, floor_y + TechnicalRoomFactory.DOOR_HEIGHT / 2, cz + room_l / 2 + t / 2],
                rotation=[0, 0, 0],
                scale=[TechnicalRoomFactory.DOOR_WIDTH, TechnicalRoomFactory.DOOR_HEIGHT, 0.05],
                meta=door_meta
            ))
            door_placed = True

        return elements
