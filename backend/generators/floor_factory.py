from models import Component3D, HallParameters

class FloorFactory:
    @staticmethod
    def generate(params: HallParameters) -> list[Component3D]:
        elements = []
        
        # Płyta posadzki betonowej (wierzch na Y=0)
        elements.append(Component3D(
            type="floor_slab",
            position=[0, -params.floor_thickness / 2, 0],
            rotation=[0, 0, 0],
            scale=[params.width, params.floor_thickness, params.length]
        ))
        
        # Podbudowa (chudy beton lub grunt stabilizowany)
        base_y_center = -params.floor_thickness - (params.floor_base_thickness / 2)
        elements.append(Component3D(
            type=f"floor_base_{params.floor_base_type}",
            position=[0, base_y_center, 0],
            rotation=[0, 0, 0],
            scale=[params.width, params.floor_base_thickness, params.length]
        ))
        
        return elements