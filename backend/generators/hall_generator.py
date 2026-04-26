from models import HallParameters, Component3D
from .column_factory import ColumnFactory
from .roof_factory import RoofFactory
from .foundation_factory import FoundationFactory
from .floor_factory import FloorFactory
from .cladding_factory import CladdingFactory
from .plinth_factory import PlinthFactory
from .dock_factory import DockFactory

class HallGenerator:
    def __init__(self, params: HallParameters):
        self.params = params

    def generate_all_components(self) -> list[Component3D]:
        if self.params.hall_type == "complex":
            return []
            
        # KOREKTA 1: "Zatrzaśnięcie" długości hali do pełnej wielokrotności siatki słupów
        num_bays = max(1, round(self.params.length / self.params.bay_spacing))
        self.params.length = num_bays * self.params.bay_spacing
        
        components = []
        components.extend(FloorFactory.generate(self.params))
        components.extend(FoundationFactory.generate(self.params))
        components.extend(PlinthFactory.generate(self.params)) 
        components.extend(ColumnFactory.generate(self.params))
        components.extend(RoofFactory.generate(self.params))
        components.extend(CladdingFactory.generate(self.params))
        components.extend(DockFactory.generate(self.params)) # Aktywacja bram i doków
        
              
        return components