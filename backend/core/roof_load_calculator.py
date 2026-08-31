"""
RoofLoadCalculator — klasyczne zebranie obciążeń dachu (wartości charakterystyczne),
liczone per moduł (hale typu Complex) lub dla całej hali (typ Simple).

Zakres:
- obciążenia stałe: warstwa po warstwie (blacha, izolacja termiczna, izolacja
  przeciwwodna, konstrukcja stalowa dachu, sufit podwieszony/instalacje)
- śnieg: obciążenie równomierne (PN-EN 1991-1-3 + zał. krajowy) + lokalne worki
  śnieżne przy różnicach wysokości sąsiednich modułów oraz przy attykach ścian PPOŻ
- wiatr: uproszczone ssanie charakterystyczne na dachu (bez pełnego strefowania cpe
  wg tabel normowych — jedna wartość reprezentatywna dla strefy krawędziowej i środkowej)
- obciążenie użytkowe dachu (kategoria wg PN-EN 1991-1-1)

UWAGA: Wartości strefowe (sk, vb0), współczynniki cpe oraz uproszczenia workow
śnieżnych są ORIENTACYJNE — punkt wyjścia do dalszych obliczeń, nie zastępują
pełnej analizy wg aktualnego załącznika krajowego normy wykonanej przez
uprawnionego konstruktora.
"""
import math

from models import HallParameters, BlockDefinition
from core.defaults import DEFAULTS
from core.grid_system import GridSystem3D
from core.insulation_catalog import load_thermal_insulation_catalog, load_waterproofing_catalog
from core.roof_sheet_catalog import get_roof_sheet_weight
from core.takeoff_calculator import STEEL_ROOF_KG_PER_M2

G_ACC = 9.81  # m/s2 — przelicznik kg/m2 -> kN/m2

ASSUMPTIONS_NOTE = (
    "Zebranie obciążeń ma charakter orientacyjny (etap koncepcyjny/przedwymiarowanie). "
    "Wartości strefowe śniegu (sk) i wiatru (vb0), współczynniki cpe dachu oraz uproszczony "
    "sposób liczenia worków śnieżnych wymagają weryfikacji z aktualnym załącznikiem krajowym "
    "normy PN-EN 1991-1-3 / PN-EN 1991-1-4 oraz pełnej analizy przez uprawnionego konstruktora "
    "przed wymiarowaniem elementów konstrukcji."
)

# --- Śnieg: wartości strefowe sk [kN/m²] wg PN-EN 1991-1-3 zał. krajowy (wartości orientacyjne) ---
SNOW_ZONE_SK = {1: 0.70, 2: 0.90, 3: 1.20, 4: 1.60, 5: 2.00}
SNOW_EXPOSURE_CE = {"normalna": 1.0, "wietrzna": 0.8, "oslonieta": 1.2}
SNOW_DENSITY_KN_M3 = 2.0  # przyjęta wartość do obliczeń worków śnieżnych (PN-EN 1991-1-3)

# --- Wiatr: prędkość bazowa vb0 [m/s] wg stref (wartości orientacyjne) ---
WIND_ZONE_VB0 = {1: 22.0, 2: 26.0, 3: 30.0}
AIR_DENSITY_KG_M3 = 1.25
TERRAIN_CATEGORY_PARAMS = {
    "0": {"z0": 0.003, "zmin": 1.0},
    "I": {"z0": 0.01, "zmin": 1.0},
    "II": {"z0": 0.05, "zmin": 2.0},
    "III": {"z0": 0.3, "zmin": 5.0},
    "IV": {"z0": 1.0, "zmin": 10.0},
}
# Uproszczone, reprezentatywne współczynniki cpe ssania na dachu (bez pełnego strefowania wg normy)
CPE_ROOF_EDGE = -1.6     # strefa krawędziowa/narożna
CPE_ROOF_CENTER = -0.7   # strefa środkowa połaci

ROOF_USE_CATEGORY_QK = {"H": 0.4}  # kN/m² — kategoria H (dach niedostępny poza konserwacją)
DEFAULT_ROOF_USE_QK = 0.4


def _item(kategoria, opis, wartosc, jednostka="kN/m²", uwagi=""):
    return {
        "kategoria": kategoria,
        "opis": opis,
        "wartosc": round(float(wartosc), 3),
        "jednostka": jednostka,
        "uwagi": uwagi,
    }


def _mu1(angle_deg: float) -> float:
    """Współczynnik kształtu dachu (obciążenie równomierne, bez wiatru) wg PN-EN 1991-1-3 tabl. 5.2."""
    if angle_deg <= 30:
        return 0.8
    if angle_deg < 60:
        return 0.8 * (60 - angle_deg) / 30
    return 0.0


def _snow_sk(zone: int, altitude_m: float) -> float:
    base = SNOW_ZONE_SK.get(zone, SNOW_ZONE_SK[2])
    if zone in (1, 2) and altitude_m > 300:
        return base * (1 + (altitude_m / 800) ** 2)
    return base


def _wind_qp(zone: int, terrain_category: str, height_m: float) -> float:
    """Szczytowe ciśnienie prędkości qp(h) [kN/m²] wg PN-EN 1991-1-4 (co=1, kI=1 — teren płaski)."""
    vb0 = WIND_ZONE_VB0.get(zone, WIND_ZONE_VB0[1])
    tp = TERRAIN_CATEGORY_PARAMS.get(terrain_category, TERRAIN_CATEGORY_PARAMS["II"])
    z0, zmin = tp["z0"], tp["zmin"]
    z0_ii = TERRAIN_CATEGORY_PARAMS["II"]["z0"]
    kr = 0.19 * (z0 / z0_ii) ** 0.07
    z_eff = max(height_m, zmin)
    cr = kr * math.log(z_eff / z0)
    vm = cr * vb0
    iv = 1.0 / math.log(z_eff / z0)
    return (1 + 7 * iv) * 0.5 * AIR_DENSITY_KG_M3 * vm ** 2 / 1000.0


def compute_wind_qp(zone: int, terrain_category: str, height_m: float) -> float:
    """Publiczny wrapper na _wind_qp — używany też przez column_load_calculator (wiatr na ściany)."""
    return _wind_qp(zone, terrain_category, height_m)


def _grid_for(params: HallParameters, block) -> GridSystem3D:
    """Buduje GridSystem3D dla danego modułu (block=params dla hali Simple)."""
    if block is params:
        return GridSystem3D(params)
    block_dict = params.model_dump()
    block_dict.update({
        "hall_type": "simple",
        "width": block.width, "length": block.length,
        "clear_height": block.clear_height, "bay_spacing": block.bay_spacing,
        "roof_angle": block.roof_angle, "roof_drainage_type": block.roof_drainage_type,
        "number_of_aisles": block.number_of_aisles,
        "truss_depth": block.truss_depth, "roof_slope_percent": block.roof_slope_percent,
        "drainage_zones_x": block.drainage_zones_x, "drainage_zones_z": block.drainage_zones_z,
        "docks_config": {}, "blocks": [], "fire_walls": [],
        "technical_rooms": [], "external_offices": [], "internal_offices": [], "office_reserve_zones": [],
    })
    return GridSystem3D(HallParameters(**block_dict))


def grid_for_block(params: HallParameters, block) -> GridSystem3D:
    """Publiczny wrapper na _grid_for — używany też przez column_load_calculator."""
    return _grid_for(params, block)


def compute_block_roof_loads(params: HallParameters, block) -> dict:
    """Publiczny wrapper na _compute_block — używany też przez column_load_calculator
    (potrzebuje sumy obciążeń dachu [kN/m²] do obliczenia N na słup)."""
    return _compute_block(params, block)


def _compute_block(params: HallParameters, block) -> dict:
    block_id = getattr(block, "block_id", None) or "Hala"
    grid = _grid_for(params, block)
    ridge_height = grid.get_parapet_height()  # najwyższy punkt dachu (z attyką obudowy)

    items = []

    # --- OBCIĄŻENIA STAŁE ---
    sheet_kg = get_roof_sheet_weight(block.roof_sheet_id)
    items.append(_item("stałe", "Blacha trapezowa dachowa", sheet_kg * G_ACC / 1000))

    if getattr(block, "roof_thermal_insulation_enabled", False) and block.roof_thermal_insulation_id:
        catalog = {c["ID"]: c for c in load_thermal_insulation_catalog()}
        mat = catalog.get(block.roof_thermal_insulation_id)
        if mat:
            kg_m2 = (mat["Grubość [cm]"] / 100.0) * mat["Ciężar właściwy [kg/m3]"]
            items.append(_item(
                "stałe", f"Izolacja termiczna — {mat['Materiał']} {mat['Grubość [cm]']} cm",
                kg_m2 * G_ACC / 1000))

    if getattr(block, "roof_waterproofing_enabled", False) and block.roof_waterproofing_id:
        catalog = {c["ID"]: c for c in load_waterproofing_catalog()}
        mat = catalog.get(block.roof_waterproofing_id)
        if mat:
            kg_m2 = (mat["Grubość [mm]"] / 1000.0) * mat["Ciężar właściwy [kg/m3]"]
            items.append(_item(
                "stałe", f"Izolacja przeciwwodna — {mat['Materiał']}",
                kg_m2 * G_ACC / 1000))

    items.append(_item(
        "stałe", "Konstrukcja stalowa dachu (dźwigary, płatwie, stężenia)",
        STEEL_ROOF_KG_PER_M2 * G_ACC / 1000, uwagi="wskaźnik 12 kg/m² (jak w przedmiarze)"))

    suspended = getattr(block, "roof_suspended_load", 0.15)
    items.append(_item("stałe", "Sufit podwieszony / instalacje", suspended))

    suma_stale = sum(i["wartosc"] for i in items if i["kategoria"] == "stałe")

    # --- ŚNIEG (obciążenie równomierne) ---
    sk = _snow_sk(params.snow_zone, params.terrain_altitude_m)
    ce = SNOW_EXPOSURE_CE.get(params.snow_exposure, 1.0)
    ct = params.snow_thermal_coefficient
    mu = _mu1(block.roof_angle)
    s_uniform = mu * ce * ct * sk
    items.append(_item(
        "śnieg", f"Śnieg — obciążenie równomierne (μ1={mu:.2f})", s_uniform,
        uwagi=f"sk={sk:.2f} kN/m², Ce={ce}, Ct={ct}"))

    # --- WIATR (uproszczony, ssanie na dachu) ---
    qp = _wind_qp(params.wind_zone, params.terrain_category, ridge_height)
    w_edge = qp * abs(CPE_ROOF_EDGE)
    w_center = qp * abs(CPE_ROOF_CENTER)
    items.append(_item(
        "wiatr", "Wiatr — ssanie, strefa krawędziowa/narożna", w_edge,
        uwagi=f"qp(h={ridge_height:.1f} m)={qp:.2f} kN/m², cpe={CPE_ROOF_EDGE} (wartość orientacyjna)"))
    items.append(_item(
        "wiatr", "Wiatr — ssanie, strefa środkowa połaci", w_center,
        uwagi=f"qp(h={ridge_height:.1f} m)={qp:.2f} kN/m², cpe={CPE_ROOF_CENTER} (wartość orientacyjna)"))

    # --- OBCIĄŻENIE UŻYTKOWE ---
    use_cat = getattr(block, "roof_use_category", "H")
    qk = ROOF_USE_CATEGORY_QK.get(use_cat, DEFAULT_ROOF_USE_QK)
    items.append(_item("użytkowe", f"Obciążenie użytkowe dachu (kategoria {use_cat})", qk))

    return {
        "block_id": block_id,
        "items": items,
        "summary": {
            "stale_kn_m2": round(suma_stale, 3),
            "sniegu_rownomiernego_kn_m2": round(s_uniform, 3),
            "wiatr_krawedziowy_kn_m2": round(w_edge, 3),
            "wiatr_srodkowy_kn_m2": round(w_center, 3),
            "uzytkowe_kn_m2": round(qk, 3),
            "wysokosc_odniesienia_m": round(ridge_height, 2),
        },
    }


def _add_parapet_drift(params: HallParameters, block_result: dict, opis: str = "Worek śnieżny — attyka ściany PPOŻ"):
    h = DEFAULTS.parapet_extension
    sk = _snow_sk(params.snow_zone, params.terrain_altitude_m)
    ce = SNOW_EXPOSURE_CE.get(params.snow_exposure, 1.0)
    ct = params.snow_thermal_coefficient
    s = min(2.0 * ce * ct * sk, max(0.8 * ce * ct * sk, SNOW_DENSITY_KN_M3 * h))
    ls = min(15.0, max(5.0, 2 * h))
    block_result["items"].append(_item(
        "śnieg", opis, s, uwagi=f"h attyki={h:.2f} m, zasięg ls≈{ls:.1f} m od ściany"))


def _fire_wall_top_type(fw) -> str:
    if isinstance(fw, dict):
        return fw.get("top_type", "")
    return getattr(fw, "top_type", "")


def _touching_pairs(blocks: list[BlockDefinition]):
    """Zwraca pary modułów stykających się krawędziami dachu wraz z ich wymiarami
    prostopadłymi do styku (b1, b2) — potrzebnymi do współczynnika worka śnieżnego."""
    bounds = {}
    for b in blocks:
        w, l = b.width, b.length
        if b.frame_orientation == 90:
            w, l = l, w
        bounds[b.block_id] = {
            "x_min": b.position_x - w / 2, "x_max": b.position_x + w / 2,
            "z_min": b.position_z - l / 2, "z_max": b.position_z + l / 2,
            "w": w, "l": l,
        }
    tolerance = 0.5
    pairs = []
    for i in range(len(blocks)):
        for j in range(i + 1, len(blocks)):
            a, b = blocks[i], blocks[j]
            ba, bb = bounds[a.block_id], bounds[b.block_id]
            if abs(ba["x_max"] - bb["x_min"]) < tolerance or abs(ba["x_min"] - bb["x_max"]) < tolerance:
                overlap = min(ba["z_max"], bb["z_max"]) - max(ba["z_min"], bb["z_min"])
                if overlap > tolerance:
                    pairs.append((a, b, ba["w"], bb["w"]))
                    continue
            if abs(ba["z_max"] - bb["z_min"]) < tolerance or abs(ba["z_min"] - bb["z_max"]) < tolerance:
                overlap = min(ba["x_max"], bb["x_max"]) - max(ba["x_min"], bb["x_min"])
                if overlap > tolerance:
                    pairs.append((a, b, ba["l"], bb["l"]))
    return pairs


class RoofLoadCalculator:
    @staticmethod
    def compute(params: HallParameters) -> dict:
        if params.hall_type == "complex" and params.blocks:
            blocks = params.blocks
            result_blocks = [_compute_block(params, b) for b in blocks]
            by_id = {r["block_id"]: r for r in result_blocks}

            # Worki śnieżne na stykach modułów o różnej wysokości dachu
            for a, b, dim_a, dim_b in _touching_pairs(blocks):
                dh = abs(a.clear_height - b.clear_height)
                if dh < 0.05:
                    continue
                lower, higher = (a, b) if a.clear_height < b.clear_height else (b, a)
                sk = _snow_sk(params.snow_zone, params.terrain_altitude_m)
                ce = SNOW_EXPOSURE_CE.get(params.snow_exposure, 1.0)
                ct = params.snow_thermal_coefficient
                mu_w = min(4.0, max(0.8, (dim_a + dim_b) / (2 * dh)))
                ls = min(15.0, max(5.0, 2 * dh))
                s_drift = mu_w * ce * ct * sk
                by_id[lower.block_id]["items"].append(_item(
                    "śnieg", f"Worek śnieżny — uskok dachu przy module {higher.block_id} (Δh={dh:.2f} m)",
                    s_drift, uwagi=f"μw={mu_w:.2f}, zasięg ls≈{ls:.1f} m od krawędzi uskoku"))

            # Worki śnieżne przy attykach ścian PPOŻ (per moduł)
            for b in blocks:
                for fw in (b.fire_walls or []):
                    if _fire_wall_top_type(fw) == "parapet_above_roof":
                        _add_parapet_drift(params, by_id[b.block_id])

            return {"blocks": result_blocks, "assumptions": ASSUMPTIONS_NOTE}

        # Hala Simple — traktowana jako jeden moduł
        result = _compute_block(params, params)
        result["block_id"] = "Hala"
        for fw in (params.fire_walls or []):
            if _fire_wall_top_type(fw) == "parapet_above_roof":
                _add_parapet_drift(params, result)
        return {"blocks": [result], "assumptions": ASSUMPTIONS_NOTE}
