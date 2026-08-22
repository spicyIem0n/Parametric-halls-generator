"""
FireSafetyManager — silnik przepisów bezpieczeństwa pożarowego.

Na podstawie obciążenia ogniowego (Qd), powierzchni strefy pożarowej
i obecności instalacji tryskaczowej klasyfikuje budynek wg polskich
Warunków Technicznych i przypisuje wymagania REI poszczególnym elementom.

Uproszczona implementacja oparta na:
- Rozporządzenie MI z 12.04.2002 (Warunki Techniczne)
- Tabela klas odporności pożarowej budynków (§212-§216 WT)
- Wymagania dla elementów budynku wg klasy odporności (§216 WT)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


# --- TABLICA KLASYFIKACJI WG POLSKICH WT ---

# Uproszczone progi obciążenia ogniowego [MJ/m²] → klasa budynku
# (dla budynków PM - produkcyjno-magazynowych, 1-kondygnacyjnych)
# Rzeczywiste przepisy uwzględniają też kategorię zagrożenia ludzi,
# liczbę kondygnacji i strefę pożarową — tu uproszczone.

FIRE_CLASS_THRESHOLDS = [
    # (max_qd, max_zone_area_no_sprinklers, max_zone_area_with_sprinklers, fire_class)
    (500, 8000, 16000, "E"),      # Qd <= 500 MJ/m² → klasa E
    (1000, 5000, 10000, "D"),     # 500 < Qd <= 1000 → klasa D
    (2000, 3000, 6000, "C"),      # 1000 < Qd <= 2000 → klasa C
    (4000, 2000, 4000, "B"),      # 2000 < Qd <= 4000 → klasa B
    (float('inf'), 1000, 2000, "A"),  # Qd > 4000 → klasa A
]

# Wymagania elementów budynku wg klasy odporności pożarowej (§216 WT)
# Format: klasa → {kategoria_elementu: wymagana_klasa_odporności}
FIRE_REQUIREMENTS = {
    "A": {
        "main_structure": "R240",    # Główna konstrukcja nośna
        "roof_structure": "R30",     # Konstrukcja dachu
        "external_wall": "EI240",    # Ściana zewnętrzna
        "internal_wall": "EI60",     # Ściana wewnętrzna
        "roof_covering": "RE30",     # Przekrycie dachu
        "fire_wall": "REI240",       # Ściana oddzielenia pożarowego
    },
    "B": {
        "main_structure": "R120",
        "roof_structure": "R30",
        "external_wall": "EI120",
        "internal_wall": "EI60",
        "roof_covering": "RE30",
        "fire_wall": "REI240",
    },
    "C": {
        "main_structure": "R60",
        "roof_structure": "R15",
        "external_wall": "EI60",
        "internal_wall": "EI30",
        "roof_covering": "RE15",
        "fire_wall": "REI120",
    },
    "D": {
        "main_structure": "R30",
        "roof_structure": "none",
        "external_wall": "EI30",
        "internal_wall": "none",
        "roof_covering": "none",
        "fire_wall": "REI120",
    },
    "E": {
        "main_structure": "none",
        "roof_structure": "none",
        "external_wall": "none",
        "internal_wall": "none",
        "roof_covering": "none",
        "fire_wall": "REI60",
    },
}

# Mapowanie typów komponentów 3D → kategorie pożarowe
COMPONENT_TO_FIRE_CATEGORY = {
    "column": "main_structure",
    "column_gable": "main_structure",
    "truss_chord": "roof_structure",
    "truss_web": "roof_structure",
    "purlin": "roof_structure",
    "purlin_strut": "roof_structure",
    "sandwich_panel": "external_wall",
    "roof_panel": "roof_covering",
    "foundation": None,          # Fundamenty nie mają wymagań ppoż
    "plinth": None,
    "floor_slab": None,
    "dock_door": None,
    "dock_shelter": None,
    "gate_door": None,
    "drainage_inlet": None,
}


@dataclass
class FireRequirements:
    """Wymagania pożarowe dla konkretnego elementu."""
    fire_rating: str          # np. "R60", "REI120", "none"
    requires_protection: bool  # Czy wymaga zabezpieczenia ogniochronnego
    material_constraint: Optional[str] = None  # np. "non_combustible" dla klasy A/B


@dataclass
class FireClassification:
    """Wynik klasyfikacji pożarowej budynku."""
    fire_class: str           # "A" / "B" / "C" / "D" / "E"
    fire_load_qd: float       # Obciążenie ogniowe [MJ/m²]
    zone_area: float          # Powierzchnia strefy [m²]
    has_sprinklers: bool
    max_zone_area: float      # Maks. dopuszczalna pow. strefy dla tej klasy


class FireSafetyManager:
    """
    Centralny menedżer bezpieczeństwa pożarowego.
    
    Workflow:
    1. Użytkownik podaje Qd i powierzchnię → classify() zwraca klasę budynku
    2. Dla każdego elementu → get_requirement() zwraca wymagane REI
    3. hall_generator nadpisuje meta["fire_rating"] w Component3D
    """

    def __init__(self, fire_load_qd: float, zone_area: float, has_sprinklers: bool = False):
        self.fire_load_qd = fire_load_qd
        self.zone_area = zone_area
        self.has_sprinklers = has_sprinklers
        self._classification: Optional[FireClassification] = None

    def classify(self) -> FireClassification:
        """
        Klasyfikuje budynek na podstawie Qd i powierzchni strefy.
        Zwraca FireClassification z klasą budynku.
        """
        if self._classification:
            return self._classification

        for max_qd, max_area_no_spr, max_area_spr, fire_class in FIRE_CLASS_THRESHOLDS:
            if self.fire_load_qd <= max_qd:
                max_area = max_area_spr if self.has_sprinklers else max_area_no_spr
                self._classification = FireClassification(
                    fire_class=fire_class,
                    fire_load_qd=self.fire_load_qd,
                    zone_area=self.zone_area,
                    has_sprinklers=self.has_sprinklers,
                    max_zone_area=max_area,
                )
                return self._classification

        # Fallback — nie powinno się zdarzyć
        self._classification = FireClassification(
            fire_class="A",
            fire_load_qd=self.fire_load_qd,
            zone_area=self.zone_area,
            has_sprinklers=self.has_sprinklers,
            max_zone_area=1000,
        )
        return self._classification

    @property
    def fire_class(self) -> str:
        """Zwraca klasę odporności pożarowej budynku."""
        return self.classify().fire_class

    def get_requirement(self, component_type: str) -> FireRequirements:
        """
        Zwraca wymagania pożarowe dla danego typu komponentu.
        
        Args:
            component_type: typ elementu z Component3D (np. "column", "truss_chord")
        
        Returns:
            FireRequirements z wymaganym fire_rating
        """
        classification = self.classify()
        requirements = FIRE_REQUIREMENTS[classification.fire_class]

        # Mapuj typ komponentu na kategorię pożarową
        fire_category = COMPONENT_TO_FIRE_CATEGORY.get(component_type)

        if fire_category is None:
            return FireRequirements(fire_rating="none", requires_protection=False)

        fire_rating = requirements.get(fire_category, "none")

        requires_protection = fire_rating != "none"
        material_constraint = None

        # Dla klas A i B — wymóg materiałów niepalnych
        if classification.fire_class in ("A", "B") and fire_category == "external_wall":
            material_constraint = "non_combustible"

        return FireRequirements(
            fire_rating=fire_rating,
            requires_protection=requires_protection,
            material_constraint=material_constraint,
        )

    def get_all_requirements(self) -> Dict[str, str]:
        """
        Zwraca słownik: kategoria_elementu → wymagane REI.
        Przydatne do wyświetlania w UI.
        """
        classification = self.classify()
        return dict(FIRE_REQUIREMENTS[classification.fire_class])

    def is_zone_area_exceeded(self) -> bool:
        """Sprawdza czy powierzchnia strefy przekracza dopuszczalną."""
        classification = self.classify()
        return self.zone_area > classification.max_zone_area

    def get_summary(self) -> Dict[str, str]:
        """Zwraca podsumowanie klasyfikacji do wyświetlenia w UI."""
        classification = self.classify()
        return {
            "fire_class": classification.fire_class,
            "fire_load_qd": f"{classification.fire_load_qd:.0f} MJ/m²",
            "zone_area": f"{classification.zone_area:.0f} m²",
            "max_zone_area": f"{classification.max_zone_area:.0f} m²",
            "zone_exceeded": "TAK" if self.is_zone_area_exceeded() else "NIE",
            "has_sprinklers": "TAK" if self.has_sprinklers else "NIE",
        }
