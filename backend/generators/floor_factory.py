"""
FloorFactory — generuje posadzkę przemysłową (płyta + podbudowa).

Zrefaktoryzowany: korzysta z GridSystem3D dla wymiarów.
"""

from models import Component3D, HallParameters
from core.grid_system import GridSystem3D


class FloorFactory:
    @staticmethod
    def generate(grid: GridSystem3D, params: HallParameters) -> list[Component3D]:
        elements = []

        # Płyta posadzki betonowej (wierzch na Y=0)
        elements.append(Component3D(
            type="floor_slab",
            position=[0, -params.floor_thickness / 2, 0],
            rotation=[0, 0, 0],
            scale=[grid.width, params.floor_thickness, grid.length]
        ))

        # Podbudowa (chudy beton lub grunt stabilizowany)
        base_y_center = -params.floor_thickness - (params.floor_base_thickness / 2)
        elements.append(Component3D(
            type=f"floor_base_{params.floor_base_type}",
            position=[0, base_y_center, 0],
            rotation=[0, 0, 0],
            scale=[grid.width, params.floor_base_thickness, grid.length]
        ))

        return elements
