"""
Stałe projektowe i domyślne gabaryty elementów.
Centralne miejsce na wartości, które były dotychczas hardcoded w wielu fabrykach.
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class ProjectDefaults:
    """Niezmienne stałe projektowe dla generatora hal."""

    # --- Szerokość słupa (używana do obliczeń lica obudowy) ---
    col_width: float = 0.5

    # --- Rozstaw słupów szczytowych ---
    gable_column_spacing: float = 6.0

    # --- Wymiary otworów ---
    dock_door_width: float = 3.0
    dock_door_height: float = 3.0
    gate_door_width: float = 4.0
    gate_door_height: float = 4.0

    # --- Podział przęsła na sloty ---
    slot_target_width: float = 4.0  # Docelowa szerokość slotu [m]

    # --- Domyślne gabaryty fundamentów [A, B, H] ---
    foundation_sizes: Dict[str, List[float]] = field(default_factory=lambda: {
        "external_main": [2.0, 2.0, 0.5],
        "external_corner": [2.0, 2.0, 0.5],
        "external_intermediate_cladding": [1.2, 1.2, 0.5],
        "internal_main": [1.5, 1.5, 0.5],
    })

    # --- Domyślne przekroje słupów [bx, bz] ---
    column_sections: Dict[str, List[float]] = field(default_factory=lambda: {
        "external_main": [0.4, 0.4],
        "external_corner": [0.4, 0.4],
        "external_intermediate_cladding": [0.3, 0.3],
        "internal_main": [0.4, 0.4],
    })

    # --- Parametry dachu (kratownica) ---
    truss_chord_thickness: float = 0.15
    truss_web_thickness: float = 0.08
    purlin_chord_thickness: float = 0.10
    purlin_web_thickness: float = 0.06

    # --- Dok / Fartuch ---
    dock_shelter_depth: float = 0.6

    # --- Attyka ---
    parapet_extension: float = 0.20  # Nadwyżka attyki ponad dach [m]


# Singleton — jedna instancja stałych dla całego programu
DEFAULTS = ProjectDefaults()
