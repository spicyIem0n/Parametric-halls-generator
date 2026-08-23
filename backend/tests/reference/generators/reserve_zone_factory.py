"""
ReserveZoneFactory — generuje strefę rezerwy pod biura w dachu.

Strefa rezerwy to obszar dachu przygotowany pod przyszłe wydzielenie pożarowe:
- Dźwigary w strefie mają osobny wymóg fire_rating (odrębny od globalnego)
- Na granicach strefy płatwie są zdublowane z przerwą (gap) na przyszłą ŚOP
- Wizualny marker strefy (półprzezroczysty prostokąt na dachu)
"""

from models import Component3D, HallParameters, OfficeReserveZone
from core.grid_system import GridSystem3D
from core.defaults import DEFAULTS


class ReserveZoneFactory:
    @staticmethod
    def generate(grid: GridSystem3D, params: HallParameters) -> list[Component3D]:
        elements = []

        if not params.office_reserve_zones:
            return elements

        for zone_config in params.office_reserve_zones:
            elements.extend(ReserveZoneFactory._build_zone(grid, params, zone_config))

        return elements

    @staticmethod
    def _build_zone(grid: GridSystem3D, params: HallParameters, config: OfficeReserveZone) -> list[Component3D]:
        """Generuje elementy strefy rezerwy pod biura."""
        elements = []

        start_bay = config.start_bay_index
        end_bay = config.end_bay_index

        # Walidacja zakresów
        if start_bay < 0 or end_bay >= grid.num_bays or start_bay > end_bay:
            return elements

        gap = config.purlin_doubling_gap
        half_gap = gap / 2

        # Pozycje Z granic strefy (osie ram)
        z_start = grid.axes_z[start_bay]       # Rama początkowa (granica "wejścia" do strefy)
        z_end = grid.axes_z[end_bay + 1]       # Rama końcowa (granica "wyjścia" ze strefy)

        # Poziom dachu
        roof_y = grid.z_levels["Z_Eave"]

        # Zakres X (pełna szerokość lub ograniczona osiami)
        x_start = grid.axes_x[config.start_axis_index] if config.start_axis_index < len(grid.axes_x) else -grid.half_width
        x_end = grid.axes_x[config.end_axis_index] if config.end_axis_index < len(grid.axes_x) else grid.half_width
        zone_width = abs(x_end - x_start)
        zone_cx = (x_start + x_end) / 2

        zone_meta = {
            "element_type": "reserve_zone",
            "zone_id": config.zone_id,
            "truss_fire_rating": config.truss_fire_rating,
        }

        # --- 1. ZDUBLOWANE PŁATWIE NA GRANICACH (z gap pod przyszłą ŚOP) ---
        purlin_t = DEFAULTS.purlin_chord_thickness

        for boundary_z in [z_start, z_end]:
            # Para płatwi odsunięta o half_gap od osi granicy
            for offset in [-half_gap, half_gap]:
                purlin_z = boundary_z + offset

                elements.append(Component3D(
                    type="reserve_purlin_doubled",
                    position=[zone_cx, roof_y, purlin_z],
                    rotation=[0, 0, 0],
                    scale=[zone_width, purlin_t, purlin_t],
                    meta={
                        **zone_meta,
                        "element_type": "doubled_purlin_boundary",
                        "description": f"Zdublowana platew z gap {gap}m na granicy strefy rezerwy",
                    }
                ))

        # --- 2. MARKER DŹWIGARÓW W STREFIE (osobny fire_rating) ---
        # Oznaczamy dźwigary w strefie — generujemy markery na ramach wewnątrz strefy
        for frame_idx in range(start_bay, end_bay + 2):  # +2 bo ramy obejmują przęsła
            if frame_idx >= grid.num_frames:
                break
            frame_z = grid.axes_z[frame_idx]

            # Cienki marker wzdłuż dźwigara (na jego wierzchu)
            elements.append(Component3D(
                type="reserve_truss_marker",
                position=[zone_cx, roof_y + 0.05, frame_z],
                rotation=[0, 0, 0],
                scale=[zone_width, 0.08, 0.15],
                meta={
                    **zone_meta,
                    "fire_rating": config.truss_fire_rating,
                    "element_type": "reserve_truss_with_fire_rating",
                }
            ))

        # --- 3. WIZUALNY MARKER STREFY (półprzezroczysty prostokąt na dachu) ---
        zone_length = abs(z_end - z_start)
        zone_cz = (z_start + z_end) / 2

        elements.append(Component3D(
            type="reserve_zone_marker",
            position=[zone_cx, roof_y + 0.12, zone_cz],
            rotation=[0, 0, 0],
            scale=[zone_width, 0.02, zone_length],
            meta={
                **zone_meta,
                "element_type": "reserve_zone_visual_marker",
                "description": "Strefa rezerwy pod biura - przygotowana pod wydzielenie pozarowe",
            }
        ))

        return elements
