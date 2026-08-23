"""
GridSystem3D — centralny kontroler siatki osi (Root Node w grafie zależności).

Oblicza i cachuje WSZYSTKIE pozycje węzłów konstrukcyjnych hali:
- Osie poprzeczne (X) i podłużne (Z)
- Pozycje słupów szczytowych
- Podział przęseł na sloty (dla doków/bram)
- Płaszczyzny poziomów odniesienia (Z-Levels)
- Wysokości dachu w dowolnym punkcie X
- Głębokości posadowienia z uwzględnieniem doków

Eliminuje duplikację obecną w 5/7 fabryk.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import HallParameters
from core.defaults import DEFAULTS


# --- DATACLASS DLA WĘZŁA SIATKI ---

@dataclass
class GridNode:
    """
    Pojedynczy węzeł konstrukcyjny siatki — punkt przecięcia osi X i Z.
    Reprezentuje pozycję słupa/fundamentu wraz z obliczonymi parametrami.
    """
    x: float                        # Współrzędna X (poprzek hali)
    z: float                        # Współrzędna Z (wzdłuż hali)
    y_foundation: float             # Rzędna spodu fundamentu (ujemna)
    y_roof: float                   # Rzędna wierzchu słupa / oparcia dźwigara
    depth: float                    # Głębokość posadowienia [m]
    is_external: bool               # Czy to oś skrajna (ściana zewnętrzna)
    side: Optional[str]             # "left" | "right" | None (dla wewnętrznych)
    has_dock_neighbor: bool          # Czy w sąsiednich przęsłach jest dok (wpływa na głębokość)
    frame_index: int                # Indeks ramy (osi Z)
    axis_index: int                 # Indeks osi X


# --- GŁÓWNA KLASA SIATKI ---

class GridSystem3D:
    """
    Centralny kontroler siatki 3D hali.
    
    Tworzy pełną topologię węzłów na podstawie HallParameters i udostępnia
    metody do odpytywania pozycji, głębokości, wysokości — eliminując potrzebę
    powtarzania obliczeń w poszczególnych fabrykach.
    """

    def __init__(self, params: HallParameters):
        self.params = params

        # --- Kluczowe wymiary (cachowane) ---
        self.num_bays: int = max(1, round(params.length / params.bay_spacing))
        self.length: float = self.num_bays * params.bay_spacing  # Zatrzaśnięta długość
        self.width: float = params.width
        self.half_width: float = params.width / 2
        self.half_length: float = self.length / 2
        self.col_width: float = DEFAULTS.col_width
        self.num_frames: int = self.num_bays + 1

        # --- Podział na sloty (dla doków/bram) ---
        self.slots_per_bay: int = max(1, int(params.bay_spacing // DEFAULTS.slot_target_width))
        self.slot_width: float = params.bay_spacing / self.slots_per_bay

        # --- Obliczenie osi ---
        self.axes_x: List[float] = self._compute_axes_x()
        self.axes_z: List[float] = self._compute_axes_z()
        self.gable_xs: List[float] = self._compute_gable_xs()

        # --- Offset lica zewnętrznego (obudowa) ---
        self.external_face_offset_x: float = self.half_width + (self.col_width / 2) + params.cladding_thickness

        # --- Poziomy odniesienia (Z-Levels) ---
        self.z_levels: Dict[str, float] = self._compute_z_levels()

        # --- Cache węzłów ---
        self._nodes: Dict[Tuple[int, int], GridNode] = {}
        self._build_nodes()

    # ===========================================================
    # PRYWATNE METODY OBLICZENIOWE
    # ===========================================================

    def _compute_axes_x(self) -> List[float]:
        """
        Oblicza pozycje osi poprzecznych (X) — od lewej do prawej.
        Uwzględnia nawy pośrednie.
        """
        xs = [-self.half_width]
        if self.params.number_of_aisles > 1:
            aisle_width = self.width / self.params.number_of_aisles
            for j in range(1, self.params.number_of_aisles):
                xs.append(-self.half_width + j * aisle_width)
        xs.append(self.half_width)
        return xs

    def _compute_axes_z(self) -> List[float]:
        """Oblicza pozycje osi podłużnych (Z) — od przodu do tyłu."""
        return [i * self.params.bay_spacing - self.half_length for i in range(self.num_frames)]

    def _compute_gable_xs(self) -> List[float]:
        """
        Oblicza pozycje X slupow szczytowych (wiatrowych).
        Przy wiecej niz 1 nawie: kazda nawa dzielona na rowne czesci,
        tak aby zadna czesc nie przekraczala ~6m.
        Przy 1 nawie: rozstaw co ~6m.
        Pomija osie slupow wewnetrznych ramy (bo tam stoja juz slupy glowne).
        """
        gable_xs = []
        spacing = DEFAULTS.gable_column_spacing

        # Wyznacz granice naw (osie slupow glownych w poprzek)
        aisle_boundaries = list(self.axes_x)  # [-half_width, ..., half_width]

        # Dla kazdej nawy (odcinek miedzy kolejnymi osiami glownymi)
        for seg_idx in range(len(aisle_boundaries) - 1):
            x_start = aisle_boundaries[seg_idx]
            x_end = aisle_boundaries[seg_idx + 1]
            seg_width = x_end - x_start

            # Ile rownych podziałow potrzeba, zeby kazdy odcinek <= spacing
            num_divisions = max(1, math.ceil(seg_width / spacing))

            # Wstawiamy slupy posrednie (bez granic - te to slupy glowne)
            for k in range(1, num_divisions):
                x_pos = x_start + k * (seg_width / num_divisions)
                gable_xs.append(round(x_pos, 6))

        return sorted(gable_xs)

    def _compute_z_levels(self) -> Dict[str, float]:
        """Oblicza kluczowe płaszczyzny wysokościowe."""
        angle_rad = math.radians(self.params.roof_angle) if self.params.roof_drainage_type == "gravity" else 0
        z_eave = self.params.clear_height + self.params.truss_depth
        z_ridge = z_eave + self.half_width * math.tan(angle_rad) if self.params.roof_drainage_type == "gravity" else z_eave

        return {
            "Z_FFL": 0.0,
            "Z_ClearHeight": self.params.clear_height,
            "Z_Eave": z_eave,
            "Z_Ridge": z_ridge,
        }

    def _has_dock_at(self, frame_idx: int, side: str) -> bool:
        """Sprawdza czy przy danej ramie po danej stronie jest dok (w sąsiednich przęsłach)."""
        docks_config = self.params.docks_config or {}
        # Sprawdzamy przęsło za ramą (i) i przed ramą (i-1)
        for bay_offset in [0, -1]:
            bay_idx = frame_idx + bay_offset
            if bay_idx < 0 or bay_idx >= self.num_bays:
                continue
            for k in range(self.slots_per_bay):
                if docks_config.get(f"{side}-{bay_idx}-{k}", "none") == "dock":
                    return True
        return False

    def _build_nodes(self):
        """Buduje cache wszystkich węzłów siatki (frame × axis)."""
        for frame_idx in range(self.num_frames):
            z_pos = self.axes_z[frame_idx]
            for axis_idx, x_pos in enumerate(self.axes_x):
                is_left = (x_pos == -self.half_width)
                is_right = (x_pos == self.half_width)
                is_external = is_left or is_right
                side = "left" if is_left else ("right" if is_right else None)

                # Głębokość posadowienia
                has_dock = False
                if side:
                    has_dock = self._has_dock_at(frame_idx, side)
                depth = self.params.dock_foundation_depth if has_dock else self.params.foundation_depth

                # Wysokość dachu w tym punkcie
                y_roof = self.get_roof_height_at(x_pos)

                self._nodes[(frame_idx, axis_idx)] = GridNode(
                    x=x_pos,
                    z=z_pos,
                    y_foundation=-depth,
                    y_roof=y_roof,
                    depth=depth,
                    is_external=is_external,
                    side=side,
                    has_dock_neighbor=has_dock,
                    frame_index=frame_idx,
                    axis_index=axis_idx,
                )

    # ===========================================================
    # PUBLICZNE METODY API
    # ===========================================================

    def get_roof_height_at(self, x: float) -> float:
        """
        Oblicza wysokość wierzchu dachu (góra pasa dźwigara) dla danej pozycji X.
        
        Dla dachu dwuspadowego: clear_height + truss_depth + (half_width - |x|) * tan(angle)
        Dla dachu płaskiego (vacuum): clear_height + truss_depth
        """
        if self.params.roof_drainage_type == "gravity":
            angle_rad = math.radians(self.params.roof_angle)
            return self.params.clear_height + self.params.truss_depth + (self.half_width - abs(x)) * math.tan(angle_rad)
        else:
            return self.params.clear_height + self.params.truss_depth

    def get_foundation_depth_at(self, frame_idx: int, side: Optional[str]) -> float:
        """
        Zwraca głębokość posadowienia dla danej ramy i strony.
        Uwzględnia sąsiedztwo doków (głębsze fundamenty).
        """
        if side and self._has_dock_at(frame_idx, side):
            return self.params.dock_foundation_depth
        return self.params.foundation_depth

    def get_node(self, frame_idx: int, axis_idx: int) -> GridNode:
        """Zwraca węzeł siatki dla danej ramy i osi."""
        return self._nodes[(frame_idx, axis_idx)]

    def get_slot_center_z(self, bay_idx: int, slot_idx: int) -> float:
        """
        Oblicza współrzędną Z środka slotu w danym przęśle.
        Bay_idx: indeks przęsła (0 do num_bays-1)
        Slot_idx: indeks slotu w przęśle (0 do slots_per_bay-1)
        """
        bay_z_start = bay_idx * self.params.bay_spacing - self.half_length
        return bay_z_start + (slot_idx * self.slot_width) + (self.slot_width / 2)

    def get_parapet_height(self) -> float:
        """
        Oblicza wysokość attyki (najwyższy punkt obudowy ścian).
        Odpowiada max_roof_h + parapet_extension.
        """
        if self.params.roof_drainage_type == "gravity":
            angle_rad = math.radians(self.params.roof_angle)
            max_roof_h = self.params.clear_height + self.params.truss_depth + self.half_width * math.tan(angle_rad)
        else:
            slope_factor = self.params.roof_slope_percent / 100.0
            max_drain_dist = (
                self.width / self.params.drainage_zones_x / 2
                + self.length / self.params.drainage_zones_z / 2
            )
            max_roof_h = self.params.clear_height + self.params.truss_depth + (max_drain_dist * slope_factor)
        return max_roof_h + DEFAULTS.parapet_extension

    def get_intermediate_z(self, bay_idx: int) -> float:
        """
        Oblicza współrzędną Z słupa pośredniego wzdłużnego (środek przęsła).
        """
        return (bay_idx * self.params.bay_spacing) + (self.params.bay_spacing / 2) - self.half_length

    def has_dock_in_bay(self, bay_idx: int, side: str) -> bool:
        """
        Sprawdza czy w danym przęśle po danej stronie jest jakikolwiek dok.
        Używane przez factory do określenia głębokości dla słupów pośrednich i stóp.
        """
        docks_config = self.params.docks_config or {}
        for k in range(self.slots_per_bay):
            if docks_config.get(f"{side}-{bay_idx}-{k}", "none") == "dock":
                return True
        return False

    def get_dock_type_at_slot(self, side: str, bay_idx: int, slot_idx: int) -> str:
        """Zwraca typ doku/bramy w danym slocie ('none', 'dock', 'gate')."""
        docks_config = self.params.docks_config or {}
        return docks_config.get(f"{side}-{bay_idx}-{slot_idx}", "none")

    def get_cladding_x(self, side: str) -> float:
        """
        Zwraca współrzędną X środka płyty warstwowej (lico + grubość/2).
        """
        t = self.params.cladding_thickness
        ext_face = self.half_width + (self.col_width / 2)
        if side == "left":
            return -(ext_face + t / 2)
        else:
            return ext_face + t / 2

    def get_ext_face_x(self, side: str) -> float:
        """
        Zwraca współrzędną X zewnętrznego lica słupa (oś + col_width/2).
        Używane przez DockFactory do pozycji fartuchów.
        """
        ext = self.half_width + self.col_width / 2 + self.params.cladding_thickness / 2
        if side == "left":
            return -ext
        else:
            return ext
