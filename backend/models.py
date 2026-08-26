from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from enum import Enum


# --- ENUMS (używane przez modele Pydantic i frontend) ---

class ElementCategoryEnum(str, Enum):
    """Kategorie elementów — mapowane na warstwy widoczności."""
    STRUCTURE = "structure"
    CLADDING = "cladding"
    ROOF = "roof"
    FOUNDATION = "foundation"
    FIRE_SEPARATION = "fire_separation"
    TECHNICAL = "technical"
    OFFICE = "office"
    BRACING = "bracing"
    OTHER = "other"


class FireRatingEnum(str, Enum):
    """Klasy odporności ogniowej."""
    NONE = "none"
    R15 = "R15"
    R30 = "R30"
    R60 = "R60"
    R120 = "R120"
    R240 = "R240"
    REI30 = "REI30"
    REI60 = "REI60"
    REI120 = "REI120"
    REI240 = "REI240"
    EI30 = "EI30"
    EI60 = "EI60"
    EI120 = "EI120"
    EI240 = "EI240"


class BuildingFireClass(str, Enum):
    """Klasy odporności pożarowej budynku wg polskich WT."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


# --- MODELE KONFIGURACYJNE (nowe moduły) ---

class FireWallConfig(BaseModel):
    """Konfiguracja pojedynczej ściany oddzielenia pożarowego."""
    axis_index: int                         # Na której osi Z (ramie) stoi ŚOP
    rei_class: str = "REI120"               # Wymagana klasa odporności
    top_type: str = "parapet_above_roof"    # "parapet_above_roof" | "non_combustible_strip"


class BlockDefinition(BaseModel):
    """Definicja pojedynczego bloku (bryły) w halach złożonych."""
    block_id: str = "A"
    width: float = 30.0
    length: float = 60.0
    clear_height: float = 10.0
    bay_spacing: float = 6.0
    roof_angle: float = 5.0
    roof_drainage_type: str = "gravity"
    number_of_aisles: int = 1
    position_offset: List[float] = [0.0, 0.0, 0.0]  # [x, y, z] offset (legacy)
    rotation_y: float = 0.0  # legacy
    connection_type: str = "expansion_joint"  # "expansion_joint" | "fire_wall" | "merged"
    # Nowe pola - edytor modulowy
    position_x: float = 0.0
    position_z: float = 0.0
    frame_orientation: int = 0  # 0 = ramy wzdluz szerokosci, 90 = ramy wzdluz dlugosci
    # Pola opcjonalne - pełna konfiguracja per moduł (jak w Simple)
    dock_zone_enabled: bool = False
    dock_zone_side: str = "left"
    dock_zone_width: float = 12.0
    dock_zone_aisles: int = 1
    docks_config: Dict[str, str] = {}
    has_cladding: bool = True
    cladding_orientation: str = "horizontal"
    cladding_panel_id: str = "SP2B_E_PIR_100"
    truss_depth: float = 0.6
    purlin_spacing: float = 2.0
    roof_sheet_id: str = "T85_08"
    roof_lights: Optional[List[Any]] = None  # None = uzyj globalnych, [] = puste
    fire_walls: List[Any] = []
    bracing_config: Optional[Dict[str, Any]] = None


class BracingConfig(BaseModel):
    """Konfiguracja stężeń ściennych i dachowych."""
    wall_bracing_bays: List[int] = []       # Indeksy przęseł ze stężeniami
    roof_bracing: bool = True
    bracing_type: str = "x_cross"           # "x_cross" | "portal_frame"


class TechnicalRoomConfig(BaseModel):
    """Konfiguracja pomieszczenia technicznego."""
    room_id: str = "tech_1"
    width: float = 6.0
    length: float = 4.0
    height: float = 3.0
    position_anchor: str = "corner_left_front"  # corner_left_front/right_front/left_back/right_back/custom
    position_offset: List[float] = [0.0, 0.0, 0.0]
    fire_rating: str = "REI120"
    has_own_roof: bool = True
    floor_level: float = 0.0


class ExternalOfficeConfig(BaseModel):
    """Konfiguracja zewnętrznego modułu biurowego."""
    office_id: str = "office_ext_1"
    width: float = 8.0                      # Głębokość (prostopadle do hali)
    length: float = 24.0                    # Wzdłuż ściany hali
    floor_height: float = 3.3
    num_floors: int = 2
    attached_wall: str = "right"            # "left" | "right" | "front" | "back"
    position_along_wall: float = 0.0        # Offset od początku ściany [m]
    fire_separation: str = "REI60"
    has_windows: bool = True
    window_ratio: float = 0.4


class InternalOfficeConfig(BaseModel):
    """Konfiguracja antresoli biurowej wewnątrz hali."""
    office_id: str = "office_int_1"
    width: float = 18.0
    length: float = 12.0
    floor_height: float = 3.0
    num_floors: int = 2
    position_x: float = 0.0                 # Środek antresoli X
    position_z: float = 0.0                 # Środek antresoli Z
    fire_separation: str = "REI60"          # "REI60" | "REI120" | "none"
    column_grid_x: float = 6.0
    column_grid_z: float = 6.0
    has_stairs_internal: bool = True


class OfficeReserveZone(BaseModel):
    """Konfiguracja strefy rezerwy pod biura w dachu."""
    zone_id: str = "reserve_1"
    start_bay_index: int = 2
    end_bay_index: int = 4
    start_axis_index: int = 0
    end_axis_index: int = 1
    roof_type_override: Optional[str] = None
    truss_fire_rating: str = "R60"
    purlin_doubling_gap: float = 0.30       # Odległość między zdublowanymi płatwiami [m]
    separate_drainage: bool = False


class RoofLightItem(BaseModel):
    """Pojedyncza pozycja doswietlenia/oddymiania."""
    item_id: str = "light_1"
    item_type: str = "skylight"         # "skylight" | "smoke_vent" | "light_strip" | "light_strip_with_vents"
    width: float = 2.0                  # Szerokość [m] (prostopadle do pasma = między płatwiami)
    length: float = 3.0                 # Długość [m] (wzdłuż pasma / hali)
    quantity: int = 4                   # Ilość sztuk
    # Dla pasma świetlnego z klapami:
    vent_count: int = 2                 # Ilość klap w pasmie
    vent_length: float = 2.0            # Długość jednej klapy [m] (szer = width pasma)


class RoofLightZoneConfig(BaseModel):
    """Konfiguracja doswietlenia i oddymiania dla jednej strefy (magazyn lub doki)."""
    zone_id: str = "main"              # "main" | "dock_zone"
    items: List[RoofLightItem] = []


# --- GŁÓWNY MODEL PARAMETRÓW ---

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

    # Fundamenty i Doki
    foundation_method: str = "default"
    foundation_depth: float = 1.0
    dock_foundation_depth: float = 2.0

    # Konfiguracja doków: { "left-0-1": "dock", "right-2-0": "gate" }
    docks_config: Dict[str, str] = {}

    # Strefa dokowa (dla hal wielonawowych)
    dock_zone_enabled: bool = False
    dock_zone_side: str = "left"                # "left" | "right" | "both"
    dock_zone_width: float = 12.0               # Szerokość strefy dokowej [m] (nawa skrajna)
    dock_zone_aisles: int = 1                   # Ile naw skrajnych tworzy strefę dokową

    manual_sizes: Dict[str, List[float]] = {
        "external_main": [2.5, 4.0, 0.45], "external_corner": [2.5, 4.0, 0.45],
        "external_intermediate_cladding": [1.5, 1.5, 0.40], "internal_main": [2.5, 2.5, 0.45]
    }

    # Słupy i Podwaliny
    column_method: str = "default"
    manual_column_sections: Dict[str, List[float]] = {
        "external_main": [0.4, 0.4], "external_corner": [0.4, 0.4],
        "external_intermediate_cladding": [0.3, 0.3], "internal_main": [0.4, 0.4]
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
    roof_drainage_type: str = "gravity"     # "gravity" (dwuspadowy) lub "vacuum" (podciśnieniowy)
    drainage_zones_x: int = 2
    drainage_zones_z: int = 4
    roof_slope_percent: float = 2.0
    truss_depth: float = 0.6
    purlin_spacing: float = 2.0
    roof_panel_thickness: float = 0.15

    # --- NOWE: Bezpieczeństwo pożarowe ---
    fire_load_qd: float = 500.0             # Obciążenie ogniowe [MJ/m²]
    has_sprinklers: bool = False
    fire_walls: List[FireWallConfig] = []

    # --- NOWE: Stężenia ---
    bracing_config: BracingConfig = BracingConfig()

    # --- NOWE: Wielobryłowość (tryb complex) ---
    blocks: List[BlockDefinition] = []
    module_connections: List[Dict[str, Any]] = []  # Polaczenia miedzy modulami

    # --- NOWE: Pomieszczenia techniczne ---
    technical_rooms: List[TechnicalRoomConfig] = []

    # --- NOWE: Moduły biurowe ---
    external_offices: List[ExternalOfficeConfig] = []
    internal_offices: List[InternalOfficeConfig] = []

    # --- NOWE: Rezerwa pod biura ---
    office_reserve_zones: List[OfficeReserveZone] = []

    # --- NOWE: Doświetlenie i oddymianie ---
    roof_lights: List[RoofLightZoneConfig] = []


# --- MODEL WYJŚCIOWY (bez zmian — kontrakt z frontendem) ---

class Component3D(BaseModel):
    type: str
    position: List[float]
    rotation: List[float]
    scale: List[float]
    meta: Optional[Dict[str, str]] = None
