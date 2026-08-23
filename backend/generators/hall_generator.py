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

            # Aplikuj PPOŻ per blok
            block_components = self._apply_fire_safety(block_components, grid)

            # Transformacja: offset + rotacja
            transformed = self._transform_components(
                block_components,
                offset=block.position_offset,
                rotation_y=block.rotation_y,
                block_id=block.block_id
            )
            all_components.extend(transformed)

        return all_components

    def _block_to_params(self, block: BlockDefinition) -> HallParameters:
        """
        Konwertuje BlockDefinition na pełny HallParameters.
        Kopiuje globalne parametry (materiały, grubości) z self.params,
        nadpisuje geometrię z definicji bloku.
        """
        # Kopiujemy bazowe parametry (materiały, stałe)
        base_dict = self.params.model_dump()

        # Nadpisujemy geometrię z bloku
        base_dict.update({
            "hall_type": "simple",  # Wewnętrznie generujemy jako simple
            "width": block.width,
            "length": block.length,
            "clear_height": block.clear_height,
            "bay_spacing": block.bay_spacing,
            "roof_angle": block.roof_angle,
            "roof_drainage_type": block.roof_drainage_type,
            "number_of_aisles": block.number_of_aisles,
            # Bloki nie mają doków domyślnie (mogą być dodane osobno)
            "docks_config": {},
            # Czyścimy zagnieżdżone konfiguracje
            "blocks": [],
            "fire_walls": [],
            "technical_rooms": [],
            "external_offices": [],
            "internal_offices": [],
            "office_reserve_zones": [],
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

        cos_a = math.cos(math.radians(rotation_y))
        sin_a = math.sin(math.radians(rotation_y))
        ox, oy, oz = offset

        transformed = []
        for c in components:
            px, py, pz = c.position

            # Rotacja wokół Y (w płaszczyźnie XZ)
            new_x = px * cos_a - pz * sin_a
            new_z = px * sin_a + pz * cos_a

            # Offset
            new_x += ox
            new_y = py + oy
            new_z += oz

            # Rotacja elementu (dodajemy rotację Y do istniejącej)
            rx, ry, rz = c.rotation
            new_ry = ry + math.radians(rotation_y)

            # Skala — dla rotacji 90° zamieniamy X i Z
            sx, sy, sz = c.scale
            if abs(rotation_y) % 180 == 90:
                sx, sz = sz, sx

            meta = dict(c.meta) if c.meta else {}
            meta["block_id"] = block_id

            transformed.append(Component3D(
                type=c.type,
                position=[round(new_x, 6), round(new_y, 6), round(new_z, 6)],
                rotation=[rx, round(new_ry, 6), rz],
                scale=[sx, sy, sz],
                meta=meta
            ))

        return transformed

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
