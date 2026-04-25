from pydantic import BaseModel
from typing import List, Dict, Optional

class HallParameters(BaseModel):
    hall_type: str = "simple"
    length: float
    width: float
    clear_height: float 
    number_of_aisles: int = 1
    roof_angle: float
    bay_spacing: float
    
    # Posadzka
    floor_thickness: float = 0.2 
    floor_base_type: str = "lean_concrete" 
    floor_base_thickness: float = 0.15 

    # Fundamenty i Doki (ZMODYFIKOWANE)
    foundation_method: str = "default" 
    foundation_depth: float = 1.0 
    dock_foundation_depth: float = 2.0 
    
    # NOWA KONFIGURACJA DOKÓW: Słownik typu { "left-0": "dock", "right-2": "gate" }
    docks_config: Dict[str, str] = {} 
    
    manual_sizes: Dict[str, List[float]] = {
        "external_main": [2.5, 4.0, 0.45], "internal_main": [2.5, 2.5, 0.45],
        "intermediate_cladding": [1.5, 1.5, 0.40], "external_dock": [2.7, 3.5, 0.45], "internal_dock": [2.5, 3.7, 0.45]
    }

    # Słupy i Podwaliny
    column_method: str = "default"
    manual_column_sections: Dict[str, List[float]] = {
        "external_main": [0.4, 0.4], "internal_main": [0.4, 0.4], "intermediate_cladding": [0.3, 0.3], "external_dock": [0.5, 0.5], "internal_dock": [0.5, 0.5]
    }
    plinth_thickness: float = 0.24 
    plinth_top_level: float = 0.30 

    # Obudowa
    has_cladding: bool = True
    cladding_orientation: str = "horizontal" 
    cladding_panel_id: str = "SP2B_E_PIR_100"
    cladding_thickness: float = 0.1 
    cladding_bottom_level: float = 0.25 

    # Dach i Odwodnienie
    roof_drainage_type: str = "gravity" # "gravity" (dwuspadowy) lub "vacuum" (podciśnieniowy)
    drainage_zones_x: int = 2 # Liczba zlewni na szerokości
    drainage_zones_z: int = 4 # Liczba zlewni na długości
    roof_slope_percent: float = 2.0 # Spadek do wpustów [%]
    truss_depth: float = 0.6 
    purlin_spacing: float = 2.0 
    roof_panel_thickness: float = 0.15 

class Component3D(BaseModel):
    type: str
    position: List[float]
    rotation: List[float]
    scale: List[float]
    meta: Optional[Dict[str, str]] = None