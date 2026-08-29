"""
HallGenerator — główny orkiestrator generacji modelu 3D hali.

Tworzy GridSystem3D i deleguje generowanie elementów do poszczególnych fabryk.
Obsługuje zarówno tryb "simple" (pojedyncza bryła) jak i "complex" (wielobryłowość).
Integruje FireSafetyManager do przypisywania wymogów PPOŻ.
"""

import math
from models import HallParameters, Component3D, BlockDefinition
from core.grid_system import GridSystem3D
from core.fire_safety import FireSafetyManager
from .column_factory import ColumnFactory
from .roof_factory import RoofFactory
from .foundation_factory import FoundationFactory
from .floor_factory import FloorFactory
from .cladding_factory import CladdingFactory
from .plinth_factory import PlinthFactory
from .dock_factory import DockFactory
from .fire_wall_factory import FireWallFactory
from .bracing_factory import BracingFactory
from .secondary_structure_factory import SecondaryStructureFactory
from .technical_room_factory import TechnicalRoomFactory
from .external_office_factory import ExternalOfficeFactory
from .internal_office_factory import InternalOfficeFactory
from .reserve_zone_factory import ReserveZoneFactory
from .roof_light_factory import RoofLightFactory


def _mat_mult(A, B):
    """Mnozenie macierzy 3x3."""
    return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def _rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return [[1, 0, 0], [0, c, -s], [0, s, c]]


def _rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, 0, s], [0, 1, 0], [-s, 0, c]]


def _rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


def _euler_xyz_to_matrix(rx, ry, rz):
    """Macierz rotacji dla katow Eulera w konwencji Three.js 'XYZ': R = Rx * Ry * Rz."""
    return _mat_mult(_mat_mult(_rot_x(rx), _rot_y(ry)), _rot_z(rz))


def _matrix_to_euler_xyz(R):
    """Rozklada macierz rotacji na katy Eulera (rx, ry, rz) w konwencji Three.js 'XYZ'.
    Odpowiada Three.js Euler.setFromRotationMatrix z order='XYZ'.
    Dla R = Rx*Ry*Rz: ry = asin(R[0][2]); jesli |R[0][2]| < 1: rx = atan2(-R[1][2], R[2][2]),
    rz = atan2(-R[0][1], R[0][0]); w przeciwnym razie gimbal lock."""
    m02 = max(-1.0, min(1.0, R[0][2]))
    ry = math.asin(m02)
    if abs(m02) < 0.999999:
        rx = math.atan2(-R[1][2], R[2][2])
        rz = math.atan2(-R[0][1], R[0][0])
    else:
        # gimbal lock
        rx = math.atan2(R[2][1], R[1][1])
        rz = 0.0
    return rx, ry, rz


def _mat_vec(R, v):
    """Mnozenie macierz 3x3 * wektor 3."""
    return [
        R[0][0]*v[0] + R[0][1]*v[1] + R[0][2]*v[2],
        R[1][0]*v[0] + R[1][1]*v[1] + R[1][2]*v[2],
        R[2][0]*v[0] + R[2][1]*v[1] + R[2][2]*v[2],
    ]


class HallGenerator:
    def __init__(self, params: HallParameters):
        self.params = params

    def generate_all_components(self) -> list[Component3D]:
        if self.params.hall_type == "complex":
            return self._generate_complex()
        else:
            return self._generate_simple()

    def _generate_simple(self) -> list[Component3D]:
        """Generacja pojedynczej bryły hali (tryb simple)."""
        # Tworzenie centralnej siatki — "single source of truth"
        grid = GridSystem3D(self.params)

        # Synchronizujemy długość hali z zatrzaśniętą siatką
        self.params.length = grid.length

        components = []
        components.extend(FloorFactory.generate(grid, self.params))
        components.extend(FoundationFactory.generate(grid, self.params))
        components.extend(PlinthFactory.generate(grid, self.params))
        components.extend(ColumnFactory.generate(grid, self.params))
        components.extend(RoofFactory.generate(grid, self.params))
        components.extend(CladdingFactory.generate(grid, self.params))
        components.extend(DockFactory.generate(grid, self.params))
        components.extend(FireWallFactory.generate(grid, self.params))
        components.extend(BracingFactory.generate(grid, self.params))
        components.extend(SecondaryStructureFactory.generate(grid, self.params))
        components.extend(TechnicalRoomFactory.generate(grid, self.params))
        components.extend(ExternalOfficeFactory.generate(grid, self.params))
        components.extend(InternalOfficeFactory.generate(grid, self.params))
        components.extend(ReserveZoneFactory.generate(grid, self.params))
        components.extend(RoofLightFactory.generate(grid, self.params))

        # Aplikuj wymogi PPOŻ do metadanych komponentów
        components = self._apply_fire_safety(components, grid)

        return components

    def _generate_complex(self) -> list[Component3D]:
        """
        Generacja hali złożonej (wielobryłowej) — tryb complex.
        
        Każdy blok (BlockDefinition) generuje osobną halę z własnym GridSystem3D,
        a następnie wszystkie elementy są transformowane o offset i rotację bloku.
        Na stykach bloków generowane są podwójne słupy (dylatacja) lub
        ściany oddzielenia pożarowego.
        """
        if not self.params.blocks:
            return []

        all_components = []

        for block in self.params.blocks:
            # Tworzymy tymczasowe parametry dla tego bloku
            block_params = self._block_to_params(block)

            # Generujemy siatkę i elementy dla bloku
            grid = GridSystem3D(block_params)
            block_params.length = grid.length

            block_components = []
            block_components.extend(FloorFactory.generate(grid, block_params))
            block_components.extend(FoundationFactory.generate(grid, block_params))
            block_components.extend(PlinthFactory.generate(grid, block_params))
            block_components.extend(ColumnFactory.generate(grid, block_params))
            block_components.extend(RoofFactory.generate(grid, block_params))
            block_components.extend(CladdingFactory.generate(grid, block_params))
            block_components.extend(DockFactory.generate(grid, block_params))
            block_components.extend(FireWallFactory.generate(grid, block_params))
            block_components.extend(BracingFactory.generate(grid, block_params))
            block_components.extend(SecondaryStructureFactory.generate(grid, block_params))
            block_components.extend(TechnicalRoomFactory.generate(grid, block_params))
            block_components.extend(ExternalOfficeFactory.generate(grid, block_params))
            block_components.extend(InternalOfficeFactory.generate(grid, block_params))
            block_components.extend(ReserveZoneFactory.generate(grid, block_params))
            block_components.extend(RoofLightFactory.generate(grid, block_params))

            # Aplikuj PPOŻ per blok
            block_components = self._apply_fire_safety(block_components, grid)

            # Offset docelowy modulu w ukladzie globalnym.
            # Nowy edytor: position_x/position_z. Starsze projekty: position_offset (fallback).
            offset = block.position_offset
            rot_y = block.rotation_y  # legacy
            if block.position_x != 0.0 or block.position_z != 0.0 or block.frame_orientation != 0:
                offset = [block.position_x, 0.0, block.position_z]
                rot_y = float(block.frame_orientation)
            transformed = self._transform_components(
                block_components,
                offset=offset,
                rotation_y=rot_y,
                block_id=block.block_id
            )
            all_components.extend(transformed)

        # Post-processing: usun sciany wewnetrzne na stykach dylatacji/scalenia
        # oraz generuj attyki przy roznych wysokosciach
        all_components = self._process_connections(all_components)

        return all_components

    def _block_to_params(self, block: BlockDefinition) -> HallParameters:
        """
        Konwertuje BlockDefinition na pełny HallParameters.
        Kopiuje globalne parametry (materiały, grubości) z self.params,
        nadpisuje geometrię z definicji bloku.
        """
        # Kopiujemy bazowe parametry (materiały, stałe)
        base_dict = self.params.model_dump()

        # Moduł generowany z ORYGINALNYMI wymiarami w lokalnym ukladzie.
        # Obrot (frame_orientation) realizuje _transform_components przez
        # rotacje wokol osi Y - NIE przez zamiane wymiarow.
        # width = rozpietosc ram (lokalna os X), length = powtarzalnosc (lokalna os Z).
        w = block.width
        l = block.length


        base_dict.update({
            "hall_type": "simple",  # Wewnętrznie generujemy jako simple
            "width": w,
            "length": l,
            "clear_height": block.clear_height,
            "bay_spacing": block.bay_spacing,
            "roof_angle": block.roof_angle,
            "roof_drainage_type": block.roof_drainage_type,
            "number_of_aisles": block.number_of_aisles,
            # Strefa dokowa per modul
            "dock_zone_enabled": block.dock_zone_enabled,
            "dock_zone_side": block.dock_zone_side,
            "dock_zone_width": block.dock_zone_width,
            "dock_zone_aisles": block.dock_zone_aisles,
            "docks_config": block.docks_config or {},
            # Obudowa per modul
            "has_cladding": block.has_cladding,
            "cladding_orientation": block.cladding_orientation,
            "cladding_panel_id": block.cladding_panel_id,
            "cladding_thickness": block.cladding_thickness,
            "cladding_bottom_level": block.cladding_bottom_level,
            # Dach per modul
            "truss_depth": block.truss_depth,
            "purlin_spacing": block.purlin_spacing,
            "roof_sheet_id": block.roof_sheet_id,
            "roof_panel_thickness": block.roof_panel_thickness,
            "drainage_zones_x": block.drainage_zones_x,
            "drainage_zones_z": block.drainage_zones_z,
            "roof_slope_percent": block.roof_slope_percent,
            # Konstrukcja per modul
            "column_method": block.column_method,
            "manual_column_sections": block.manual_column_sections,
            "foundation_method": block.foundation_method,
            "manual_sizes": block.manual_sizes,
            "foundation_depth": block.foundation_depth,
            "dock_foundation_depth": block.dock_foundation_depth,
            "plinth_thickness": block.plinth_thickness,
            "plinth_top_level": block.plinth_top_level,
            # Posadzka per modul
            "floor_thickness": block.floor_thickness,
            "floor_base_type": block.floor_base_type,
            "floor_base_thickness": block.floor_base_thickness,
            # PPOZ per modul
            "fire_load_qd": block.fire_load_qd,
            "has_sprinklers": block.has_sprinklers,
            "fire_walls": block.fire_walls or [],
            # Doswietlenie - jesli block ma wlasne, uzyj ich; inaczej puste
            "roof_lights": block.roof_lights if block.roof_lights is not None else [],
            # Pomieszczenia per modul
            "technical_rooms": block.technical_rooms or [],
            "external_offices": block.external_offices or [],
            "internal_offices": block.internal_offices or [],
            "office_reserve_zones": block.office_reserve_zones or [],
            # Czyścimy wielobryłowość (zapobiegamy rekurencji)
            "blocks": [],
            "module_connections": [],
        })

        return HallParameters(**base_dict)

    def _transform_components(
        self,
        components: list[Component3D],
        offset: list[float],
        rotation_y: float,
        block_id: str
    ) -> list[Component3D]:
        """
        Transformuje listę komponentów o offset [x, y, z] i rotację wokół osi Y.
        Dodaje block_id do metadanych.
        """
        if rotation_y == 0 and offset == [0, 0, 0]:
            # Bez transformacji — tylko dodajemy meta
            for c in components:
                if c.meta is None:
                    c.meta = {}
                c.meta["block_id"] = block_id
            return components

        R_mod = _rot_y(math.radians(rotation_y))
        ox, oy, oz = offset

        transformed = []
        for c in components:
            # Rotacja pozycji: obrot wokol Y * pozycja lokalna, potem offset
            px, py, pz = c.position
            rpx, rpy, rpz = _mat_vec(R_mod, [px, py, pz])
            new_x = rpx + ox
            new_y = rpy + oy
            new_z = rpz + oz

            # Rotacja elementu: ZLOZENIE macierzy R_mod * R_element,
            # potem rozklad na katy Eulera XYZ (konwencja Three.js).
            rx, ry, rz = c.rotation
            R_elem = _euler_xyz_to_matrix(rx, ry, rz)
            R_final = _mat_mult(R_mod, R_elem)
            new_rx, new_ry, new_rz = _matrix_to_euler_xyz(R_final)

            # Skala BEZ ZMIAN — wymiary wlasne elementu zachowane.
            sx, sy, sz = c.scale

            meta = dict(c.meta) if c.meta else {}
            meta["block_id"] = block_id

            transformed.append(Component3D(
                type=c.type,
                position=[round(new_x, 6), round(new_y, 6), round(new_z, 6)],
                rotation=[round(new_rx, 6), round(new_ry, 6), round(new_rz, 6)],
                scale=[sx, sy, sz],
                meta=meta
            ))

        return transformed

    def _process_connections(self, components: list[Component3D]) -> list[Component3D]:
        """
        Przetwarza polaczenia miedzy modulami:
        - expansion_joint: usuwa sciany (sandwich_panel, plinth) na linii styku wewnatrz,
          zachowuje/dodaje attyk? przy roznicy wysokosci
        - none: usuwa sciany na linii styku
        - internal_wall: zachowuje sciany bez odpornosci ogniowej
        - fire_wall: zachowuje sciany, dodaje nadwyzke ponad dach
        """
        connections = self.params.module_connections or []
        blocks = self.params.blocks or []
        if not connections or not blocks:
            return components

        # Oblicz granice kazdego bloku
        block_bounds = {}
        for block in blocks:
            w, l = block.width, block.length
            if block.frame_orientation == 90:
                w, l = l, w
            px = block.position_x if (block.position_x != 0 or block.position_z != 0
                                      or block.frame_orientation != 0) else block.position_offset[0]
            pz = block.position_z if (block.position_x != 0 or block.position_z != 0
                                      or block.frame_orientation != 0) else block.position_offset[2]
            block_bounds[block.block_id] = {
                'x_min': px - w / 2, 'x_max': px + w / 2,
                'z_min': pz - l / 2, 'z_max': pz + l / 2,
                'height': block.clear_height, 'px': px, 'pz': pz,
            }

        # Okresl strefy usuwania scian
        remove_zones = []  # lista (axis, coord, range_min, range_max, conn_type, h_a, h_b, bid_a, bid_b)
        for conn in connections:
            if not isinstance(conn, dict):
                conn = conn if hasattr(conn, 'get') else {}
            mod_a_idx = conn.get('moduleA', 0)
            mod_b_idx = conn.get('moduleB', 1)
            conn_type = conn.get('type', 'expansion_joint')

            if mod_a_idx >= len(blocks) or mod_b_idx >= len(blocks):
                continue
            bid_a = blocks[mod_a_idx].block_id
            bid_b = blocks[mod_b_idx].block_id
            if bid_a not in block_bounds or bid_b not in block_bounds:
                continue

            ba = block_bounds[bid_a]
            bb = block_bounds[bid_b]

            # Usuwamy sciany tylko przy expansion_joint i none
            if conn_type not in ('expansion_joint', 'none'):
                continue

            tolerance = 0.5
            # Styk w osi X (prawa A = lewa B lub odwrotnie)
            if abs(ba['x_max'] - bb['x_min']) < tolerance:
                x_coord = ba['x_max']
                z_min = max(ba['z_min'], bb['z_min'])
                z_max = min(ba['z_max'], bb['z_max'])
                if z_max > z_min:
                    remove_zones.append(('x', x_coord, z_min, z_max, conn_type,
                                         ba['height'], bb['height'], bid_a, bid_b))
            elif abs(ba['x_min'] - bb['x_max']) < tolerance:
                x_coord = ba['x_min']
                z_min = max(ba['z_min'], bb['z_min'])
                z_max = min(ba['z_max'], bb['z_max'])
                if z_max > z_min:
                    remove_zones.append(('x', x_coord, z_min, z_max, conn_type,
                                         ba['height'], bb['height'], bid_a, bid_b))
            # Styk w osi Z
            if abs(ba['z_max'] - bb['z_min']) < tolerance:
                z_coord = ba['z_max']
                x_min = max(ba['x_min'], bb['x_min'])
                x_max = min(ba['x_max'], bb['x_max'])
                if x_max > x_min:
                    remove_zones.append(('z', z_coord, x_min, x_max, conn_type,
                                         ba['height'], bb['height'], bid_a, bid_b))
            elif abs(ba['z_min'] - bb['z_max']) < tolerance:
                z_coord = ba['z_min']
                x_min = max(ba['x_min'], bb['x_min'])
                x_max = min(ba['x_max'], bb['x_max'])
                if x_max > x_min:
                    remove_zones.append(('z', z_coord, x_min, x_max, conn_type,
                                         ba['height'], bb['height'], bid_a, bid_b))

        if not remove_zones:
            return components

        # Filtruj/przycinaj elementy scian na stykach
        wall_types = {'sandwich_panel', 'plinth', 'girt'}
        filtered = []
        for c in components:
            action = 'keep'
            trim_y_min = None
            if c.type in wall_types:
                px, py, pz = c.position
                sy = c.scale[1] if len(c.scale) > 1 else 1.0
                panel_top = py + sy / 2
                block_id = c.meta.get("block_id", "") if c.meta else ""

                for zone in remove_zones:
                    (axis, coord, rng_min, rng_max, ctype,
                     h_a, h_b, bid_a, bid_b) = zone
                    lower_h = min(h_a, h_b)
                    higher_h = max(h_a, h_b)
                    # Okresl czy panel nalezy do wyzszego czy nizszego modulu
                    is_higher = ((block_id == bid_a and h_a >= h_b) or
                                 (block_id == bid_b and h_b >= h_a))

                    in_zone = False
                    if axis == 'x':
                        in_zone = (abs(px - coord) < 2.0 and
                                   rng_min - 1 < pz < rng_max + 1)
                    else:
                        in_zone = (abs(pz - coord) < 2.0 and
                                   rng_min - 1 < px < rng_max + 1)

                    if in_zone and (block_id == bid_a or block_id == bid_b):
                        if lower_h >= higher_h - 0.5:
                            # Obie hale o tej samej wysokosci -> usun w calosci
                            action = 'remove'
                        elif is_higher:
                            # Panel wyzszego modulu: przytnij do attyki (powyzej lower_h)
                            if panel_top <= lower_h + 0.3:
                                action = 'remove'
                            else:
                                action = 'trim'
                                trim_y_min = lower_h
                        else:
                            # Panel nizszego modulu: usun w calosci
                            action = 'remove'
                        break

            if action == 'remove':
                continue
            elif action == 'trim' and trim_y_min is not None:
                sx, sy_orig, sz = c.scale
                py_orig = c.position[1]
                panel_top = py_orig + sy_orig / 2
                new_sy = panel_top - trim_y_min
                if new_sy < 0.3:
                    continue
                new_py = trim_y_min + new_sy / 2
                trimmed = Component3D(
                    type=c.type,
                    position=[c.position[0], new_py, c.position[2]],
                    rotation=c.rotation,
                    scale=[sx, new_sy, sz],
                    meta=c.meta,
                )
                filtered.append(trimmed)
            else:
                filtered.append(c)

        return filtered

    def _apply_fire_safety(self, components: list[Component3D], grid: GridSystem3D) -> list[Component3D]:
        """
        Aplikuje wymogi bezpieczeństwa pożarowego do metadanych komponentów.
        
        Na podstawie fire_load_qd i powierzchni hali, FireSafetyManager klasyfikuje
        budynek i nadpisuje meta["fire_rating"] dla elementów wymagających ochrony.
        """
        # Obliczamy powierzchnię strefy pożarowej (cała hala = jedna strefa)
        zone_area = grid.width * grid.length

        fire_mgr = FireSafetyManager(
            fire_load_qd=self.params.fire_load_qd,
            zone_area=zone_area,
            has_sprinklers=self.params.has_sprinklers
        )

        fire_class = fire_mgr.fire_class

        # Dla klasy E — brak wymogów, pomijamy iterację
        if fire_class == "E":
            return components

        # Nadpisujemy meta dla elementów z wymaganym fire_rating
        for component in components:
            req = fire_mgr.get_requirement(component.type)
            if req.requires_protection:
                if component.meta is None:
                    component.meta = {}
                component.meta["fire_rating"] = req.fire_rating
                component.meta["fire_class"] = fire_class
                if req.material_constraint:
                    component.meta["material_constraint"] = req.material_constraint

        return components
