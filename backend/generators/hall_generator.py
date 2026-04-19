from models import HallParameters, Component3D
from .column_factory import ColumnFactory
from .roof_factory import RoofFactory
from .foundation_factory import FoundationFactory
from .floor_factory import FloorFactory
from .cladding_factory import CladdingFactory
from .plinth_factory import PlinthFactory # Dodany import

class HallGenerator:
    def __init__(self, params: HallParameters):
        self.params = params

    def generate_all_components(self) -> list[Component3D]:
        components = []
        if self.params.hall_type == "complex":
            return []
            
        components.extend(FloorFactory.generate(self.params))
        components.extend(FoundationFactory.generate(self.params))
        components.extend(PlinthFactory.generate(self.params)) # Wywołanie podwalin
        components.extend(ColumnFactory.generate(self.params))
        components.extend(RoofFactory.generate(self.params))
        components.extend(CladdingFactory.generate(self.params))
        
        return components