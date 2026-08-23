"""
ClashDetector — system detekcji kolizji geometrycznych.

Sprawdza czy otwory (doki, bramy) nie kolidują ze słupami głównymi
i innymi elementami o wyższym priorytecie. Raportuje:
- Hard Clash: otwarcie koliduje z elementem Priority 1 (słup główny) → BŁĄD
- Soft Clash: otwarcie koliduje z elementem Priority 2 (stężenie) → OSTRZEŻENIE

Na tym etapie implementujemy detekcję i raportowanie (nie auto-fix).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from models import HallParameters
from core.grid_system import GridSystem3D
from core.defaults import DEFAULTS


@dataclass
class Clash:
    """Pojedyncza wykryta kolizja."""
    clash_type: str          # "hard" | "soft"
    severity: str            # "error" | "warning"
    message: str             # Opis czytelny dla użytkownika
    element_a_type: str      # Typ kolidującego elementu A (np. "column")
    element_b_type: str      # Typ kolidującego elementu B (np. "dock")
    position: List[float]    # Pozycja kolizji [x, y, z]
    bay_index: int = -1      # Indeks przęsła
    side: str = ""           # Strona ("left" / "right")


@dataclass
class ValidationResult:
    """Wynik walidacji modelu."""
    is_valid: bool
    clashes: List[Clash]
    warnings_count: int
    errors_count: int

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "warnings_count": self.warnings_count,
            "errors_count": self.errors_count,
            "clashes": [
                {
                    "clash_type": c.clash_type,
                    "severity": c.severity,
                    "message": c.message,
                    "element_a": c.element_a_type,
                    "element_b": c.element_b_type,
                    "position": c.position,
                    "bay_index": c.bay_index,
                    "side": c.side,
                }
                for c in self.clashes
            ],
        }


class ClashDetector:
    """
    Detektor kolizji geometrycznych dla modelu hali.
    
    Logika oparta na siatce:
    - Sprawdza czy doki/bramy nie są ustawione dokładnie na osi ramy głównej
      (co oznaczałoby kolizję ze słupem)
    - Sprawdza czy wymiary otworów nie przekraczają dostępnej przestrzeni w slocie
    """

    def __init__(self, grid: GridSystem3D, params: HallParameters):
        self.grid = grid
        self.params = params

    def validate(self) -> ValidationResult:
        """Przeprowadza pełną walidację modelu i zwraca wynik."""
        clashes = []

        # 1. Sprawdź kolizje doków/bram ze słupami głównymi
        clashes.extend(self._check_dock_column_clashes())

        # 2. Sprawdź czy wymiary otworów mieszczą się w slocie
        clashes.extend(self._check_opening_size_clashes())

        # 3. Sprawdź czy ściany ppoż nie kolidują z dokami
        clashes.extend(self._check_fire_wall_dock_clashes())

        errors = [c for c in clashes if c.severity == "error"]
        warnings = [c for c in clashes if c.severity == "warning"]

        return ValidationResult(
            is_valid=len(errors) == 0,
            clashes=clashes,
            warnings_count=len(warnings),
            errors_count=len(errors),
        )

    def _check_dock_column_clashes(self) -> List[Clash]:
        """
        Sprawdza czy dok/brama nie jest umieszczona bezpośrednio na osi ramy głównej.
        
        Slot na granicy przęsła (slot_idx = 0 lub last) jest bezpośrednio przyległy 
        do osi ramy, gdzie stoi słup. Nie jest to hard clash sam w sobie
        (bo slot jest między ramami), ale sprawdzamy logikę topologiczną.
        
        Hard clash: nie może istnieć — w obecnej architekturze doki są w slotach
        MIĘDZY ramami, więc nie mogą kolidować bezpośrednio ze słupami.
        Ta metoda weryfikuje spójność konfiguracji.
        """
        clashes = []
        docks_config = self.params.docks_config or {}

        for side in ["left", "right"]:
            x_pos = -self.grid.half_width if side == "left" else self.grid.half_width

            for bay_idx in range(self.grid.num_bays):
                for slot_idx in range(self.grid.slots_per_bay):
                    dock_type = self.grid.get_dock_type_at_slot(side, bay_idx, slot_idx)
                    if dock_type == "none":
                        continue

                    z_center = self.grid.get_slot_center_z(bay_idx, slot_idx)

                    # Sprawdź czy otwór nie jest zbyt blisko osi ramy (słupa)
                    door_w = DEFAULTS.dock_door_width if dock_type == "dock" else DEFAULTS.gate_door_width
                    half_door = door_w / 2

                    # Krawędzie otworu w Z
                    door_z_min = z_center - half_door
                    door_z_max = z_center + half_door

                    # Osie ram sąsiednich (granice przęsła)
                    frame_z_before = self.grid.axes_z[bay_idx]
                    frame_z_after = self.grid.axes_z[bay_idx + 1]

                    # Minimalna odległość od osi słupa (col_width/2 + margines)
                    min_clearance = self.grid.col_width / 2 + 0.05

                    if door_z_min < frame_z_before + min_clearance:
                        clashes.append(Clash(
                            clash_type="hard",
                            severity="error",
                            message=f"Otwór ({dock_type}) w przęśle {bay_idx+1}, slot {slot_idx+1}, strona {side} — zbyt blisko słupa na osi {bay_idx+1}",
                            element_a_type="column",
                            element_b_type=dock_type,
                            position=[x_pos, 0, z_center],
                            bay_index=bay_idx,
                            side=side,
                        ))

                    if door_z_max > frame_z_after - min_clearance:
                        clashes.append(Clash(
                            clash_type="hard",
                            severity="error",
                            message=f"Otwór ({dock_type}) w przęśle {bay_idx+1}, slot {slot_idx+1}, strona {side} — zbyt blisko słupa na osi {bay_idx+2}",
                            element_a_type="column",
                            element_b_type=dock_type,
                            position=[x_pos, 0, z_center],
                            bay_index=bay_idx,
                            side=side,
                        ))

        return clashes

    def _check_opening_size_clashes(self) -> List[Clash]:
        """Sprawdza czy wymiary otworu mieszczą się w slocie."""
        clashes = []
        docks_config = self.params.docks_config or {}

        for side in ["left", "right"]:
            x_pos = -self.grid.half_width if side == "left" else self.grid.half_width

            for bay_idx in range(self.grid.num_bays):
                for slot_idx in range(self.grid.slots_per_bay):
                    dock_type = self.grid.get_dock_type_at_slot(side, bay_idx, slot_idx)
                    if dock_type == "none":
                        continue

                    door_w = DEFAULTS.dock_door_width if dock_type == "dock" else DEFAULTS.gate_door_width
                    z_center = self.grid.get_slot_center_z(bay_idx, slot_idx)

                    # Otwór nie może być szerszy niż slot
                    if door_w > self.grid.slot_width:
                        clashes.append(Clash(
                            clash_type="hard",
                            severity="error",
                            message=f"Otwór ({dock_type}, szer. {door_w}m) jest szerszy niż slot ({self.grid.slot_width:.1f}m) w przęśle {bay_idx+1}",
                            element_a_type="slot_boundary",
                            element_b_type=dock_type,
                            position=[x_pos, 0, z_center],
                            bay_index=bay_idx,
                            side=side,
                        ))

        return clashes

    def _check_fire_wall_dock_clashes(self) -> List[Clash]:
        """Sprawdza czy ściana pożarowa nie przecina przęsła z dokiem."""
        clashes = []

        if not self.params.fire_walls:
            return clashes

        for fw in self.params.fire_walls:
            axis_idx = fw.axis_index
            if axis_idx < 0 or axis_idx >= self.grid.num_frames:
                continue

            z_pos = self.grid.axes_z[axis_idx]

            # Sprawdź przęsła po obu stronach ŚOP
            for bay_offset in [-1, 0]:
                check_bay = axis_idx + bay_offset
                if check_bay < 0 or check_bay >= self.grid.num_bays:
                    continue

                for side in ["left", "right"]:
                    for slot_idx in range(self.grid.slots_per_bay):
                        dock_type = self.grid.get_dock_type_at_slot(side, check_bay, slot_idx)
                        if dock_type == "none":
                            continue

                        z_center = self.grid.get_slot_center_z(check_bay, slot_idx)
                        door_w = DEFAULTS.dock_door_width if dock_type == "dock" else DEFAULTS.gate_door_width

                        # Czy otwór jest blisko ściany pożarowej (< 1m)?
                        if abs(z_center - z_pos) < door_w / 2 + 1.0:
                            clashes.append(Clash(
                                clash_type="soft",
                                severity="warning",
                                message=f"Otwór ({dock_type}) blisko ściany PPOŻ na osi {axis_idx+1} — wymagana weryfikacja szczelności",
                                element_a_type="fire_wall",
                                element_b_type=dock_type,
                                position=[-self.grid.half_width if side == "left" else self.grid.half_width, 0, z_center],
                                bay_index=check_bay,
                                side=side,
                            ))

        return clashes
