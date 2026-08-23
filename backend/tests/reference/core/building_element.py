"""
BuildingElement — klasa bazowa dla wszystkich elementów konstrukcyjnych hali.

Każdy element w modelu parametrycznym dziedziczy z tej klasy.
Zapewnia ujednolicony interfejs serializacji do Component3D (format wysyłany do frontendu)
oraz przechowuje metadane (priorytet kolizji, wymagania ppoż, relacja do węzła siatki).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

# Import modelu Pydantic — BuildingElement konwertuje się do Component3D
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import Component3D


# --- ENUMS ---

class ElementCategory(str, Enum):
    """Kategorie elementów — mapowane na warstwy widoczności w Scene3D."""
    STRUCTURE = "structure"
    CLADDING = "cladding"
    ROOF = "roof"
    FOUNDATION = "foundation"
    FIRE_SEPARATION = "fire_separation"
    TECHNICAL = "technical"
    OFFICE = "office"
    BRACING = "bracing"
    OTHER = "other"


class ElementPriority(int, Enum):
    """Priorytety elementów dla systemu detekcji kolizji."""
    IMMOVABLE = 1       # Siatka osi, słupy główne, stopy — nie do ruszenia
    ADAPTIVE = 2        # Stężenia, rygle — mogą się adaptować
    SUBORDINATE = 3     # Doki, bramy, okna — muszą się wpasować


class FireRating(str, Enum):
    """Klasy odporności ogniowej elementów wg polskich WT."""
    NONE = "none"
    R15 = "R15"
    R30 = "R30"
    R60 = "R60"
    R120 = "R120"
    R240 = "R240"
    RE15 = "RE15"
    RE30 = "RE30"
    RE60 = "RE60"
    REI15 = "REI15"
    REI30 = "REI30"
    REI60 = "REI60"
    REI120 = "REI120"
    REI240 = "REI240"
    EI15 = "EI15"
    EI30 = "EI30"
    EI60 = "EI60"
    EI120 = "EI120"
    EI240 = "EI240"


# --- KLASA BAZOWA ---

@dataclass
class BuildingElement:
    """
    Klasa bazowa dla wszystkich elementów modelu parametrycznego hali.
    
    Odpowiedzialności:
    - Przechowuje pozycję, obrót, skalę w przestrzeni 3D
    - Przechowuje metadane (typ, kategoria, priorytet, wymagania ppoż)
    - Serializuje się do Component3D (format API)
    - Umożliwia identyfikację relacji Parent-Child w grafie zależności
    """

    # --- Identyfikacja ---
    element_type: str                                    # Typ elementu (np. "column", "foundation", "sandwich_panel")
    element_category: ElementCategory = ElementCategory.OTHER
    priority: ElementPriority = ElementPriority.SUBORDINATE

    # --- Geometria ---
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    scale: Tuple[float, float, float] = (1.0, 1.0, 1.0)

    # --- Relacje (Node Graph) ---
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    parent_node_id: Optional[str] = None   # ID węzła siatki (GridNode) z którego dziedziczy pozycję
    block_id: Optional[str] = None         # ID bloku (dla wielobryłowości)

    # --- Bezpieczeństwo pożarowe ---
    fire_rating_required: FireRating = FireRating.NONE

    # --- Metadane dodatkowe ---
    meta: Dict[str, str] = field(default_factory=dict)

    def to_component3d(self) -> Component3D:
        """
        Konwertuje element do formatu Component3D wysyłanego do frontendu.
        
        Frontend (Scene3D.jsx) oczekuje:
        - type: str → mapowany na kategorię widoczności i materiał
        - position: [x, y, z]
        - rotation: [rx, ry, rz]
        - scale: [sx, sy, sz]
        - meta: Optional[Dict[str, str]] → dodatkowe info (fire_rating, room_type itp.)
        """
        # Budujemy meta z fire_rating i ewentualnych dodatkowych pól
        output_meta = dict(self.meta)
        if self.fire_rating_required != FireRating.NONE:
            output_meta["fire_rating"] = self.fire_rating_required.value
        if self.block_id:
            output_meta["block_id"] = self.block_id
        output_meta["category"] = self.element_category.value
        output_meta["priority"] = str(self.priority.value)

        return Component3D(
            type=self.element_type,
            position=list(self.position),
            rotation=list(self.rotation),
            scale=list(self.scale),
            meta=output_meta if output_meta else None,
        )

    def get_bounding_box(self) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """
        Zwraca uproszczony AABB (Axis-Aligned Bounding Box) — min i max punkt.
        Używane przez ClashDetector do wykrywania kolizji.
        Uwaga: nie uwzględnia obrotu (uproszczenie wystarczające dla prostokątnych elementów hal).
        """
        px, py, pz = self.position
        sx, sy, sz = self.scale
        half_sx, half_sy, half_sz = sx / 2, sy / 2, sz / 2

        min_pt = (px - half_sx, py - half_sy, pz - half_sz)
        max_pt = (px + half_sx, py + half_sy, pz + half_sz)
        return min_pt, max_pt

    def overlaps(self, other: "BuildingElement") -> bool:
        """Sprawdza czy bounding boxy dwóch elementów się przecinają."""
        min_a, max_a = self.get_bounding_box()
        min_b, max_b = other.get_bounding_box()

        return (
            min_a[0] < max_b[0] and max_a[0] > min_b[0] and
            min_a[1] < max_b[1] and max_a[1] > min_b[1] and
            min_a[2] < max_b[2] and max_a[2] > min_b[2]
        )
