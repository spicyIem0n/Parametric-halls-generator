"""
ColumnLoadCalculator — zbiera obciążenia charakterystyczne działające na słup
(N pionowe, H poziome z wiatru na ścianę, M zginające u podstawy słupa),
per kategoria słupa (external_main, external_corner, internal_main,
external_intermediate_cladding) i per moduł.

Wykorzystywane przez core/foundation_sizing_calculator.py do doboru gabarytów stóp.

UWAGA: obliczenia mają charakter orientacyjny/przedwymiarowy — patrz założenia
zwracane razem z wynikiem (ASSUMPTIONS_NOTE w foundation_sizing_calculator.py).
Uproszczenia:
- powierzchnie wpływu (tributary) liczone formułowo (rozstaw ram × rozstaw osi),
  nie węzeł po węźle,
- słupy pośrednie ściany (external_intermediate_cladding) — szczytowe i wzdłużne —
  potraktowane jednolicie, z rozstawem wg DEFAULTS.gable_column_spacing,
- wiatr na ścianę: jeden reprezentatywny współczynnik cpe na kategorię (bez
  rozróżnienia strony nawietrznej/zawietrznej per słup),
- warunki podparcia słupa: main frame (internal_main, external_main, external_corner)
  — słup wspornikowy utwierdzony w fundamencie (typowe dla ram halowych; stąd cała
  reakcja pozioma i moment trafiają do stopy). Słupy pośrednie ściany
  (external_intermediate_cladding) to elementy pomocnicze ryglówki — przegubowe
  u dołu I u góry (mocowane do rygla/płatwi), więc moment nie przenosi się na
  fundament (M=0), a siła pozioma dzieli się po połowie między podstawę a górne
  podparcie (H_podstawy = 0,5×H_całkowite),
- N pionowe liczone dla kombinacji stałe + max(śnieg równomierny, użytkowe)
  — dominująca kombinacja dla nośności gruntu; lokalne worki śnieżne (jeśli
  występują w zebraniu obciążeń dachu) nie są rozkładane na pojedyncze słupy,
- SYSTEM KONSTRUKCYJNY (założenie, nie fizyczna konieczność): każda nawa ma
  własny, przegubowo podparty dźwigar; słup wewnętrzny (internal_main) to
  wyłącznie podpórka dla końców dwóch sąsiednich dźwigarów — nie dotyka żadnej
  ściany zewnętrznej i nie jest połączony momentowo z dźwigarem, więc H=M=0
  (wiatr poprzeczny idzie łańcuchem: płyta → ryglówka → słup zewnętrzny tej
  ściany → fundament, z pominięciem słupów wewnętrznych). To bardzo typowe,
  ekonomiczne rozwiązanie dla hal wielonawowych, ale NIE jedyne możliwe: przy
  ciągłej ramie sztywnej (węzły momentowe też przy słupach wewnętrznych) albo
  gdy stężenia wiatrowe podłużne (bracing_config) przechodzą akurat przez
  przęsło ze słupem wewnętrznym, realne M na tym słupie byłoby niezerowe —
  bracing_config nie jest obecnie powiązany z tymi obliczeniami.
"""
from models import HallParameters
from core.defaults import DEFAULTS
from core.roof_load_calculator import compute_block_roof_loads, compute_wind_qp, grid_for_block
from core.wall_panel_catalog import get_wall_panel_weight

CONCRETE_DENSITY_KN_M3 = 25.0  # żelbet — ciężar objętościowy do ciężaru własnego słupa

COLUMN_CATEGORIES = ["internal_main", "external_main", "external_corner", "external_intermediate_cladding"]

# Uproszczone, reprezentatywne współczynniki cpe ściany (wartość bezwzględna) per kategoria słupa
CPE_WALL = {
    "internal_main": 0.0,                    # brak ściany zewnętrznej
    "external_main": 0.8,                    # parcie nawietrzne — ściana boczna
    "external_corner": 1.0,                  # ssanie w strefie narożnej (konserwatywnie)
    "external_intermediate_cladding": 0.8,   # jak external_main (uproszczenie — szczyt + wzdłużne razem)
}

# Słupy pomocnicze ryglówki — przegubowe u dołu i u góry (mocowane do rygla/płatwi),
# w odróżnieniu od głównych słupów ramy (wspornikowych, utwierdzonych w fundamencie)
PINNED_BASE_CATEGORIES = {"external_intermediate_cladding"}


def _present_categories(params: HallParameters, block) -> set:
    """Zwraca zbiór kategorii słupów, które FAKTYCZNIE występują w geometrii tego
    modułu — wyprowadzone z tej samej klasyfikacji węzłów GridSystem3D co
    generators/foundation_factory.py (a nie z formuł, które istnienia nie sprawdzają).

    Bez tego np. dla number_of_aisles=1 (hala jednonawowa — brak słupów wewnętrznych)
    kategoria 'internal_main' byłaby liczona formułowo mimo braku takiego słupa
    w rzeczywistym modelu 3D (fikcyjne obciążenie/stopa)."""
    grid = grid_for_block(params, block)
    present = set()
    for frame_idx in range(grid.num_frames):
        for axis_idx in range(len(grid.axes_x)):
            node = grid.get_node(frame_idx, axis_idx)
            is_corner = node.is_external and (frame_idx == 0 or frame_idx == grid.num_frames - 1)
            if is_corner:
                present.add("external_corner")
            elif node.is_external:
                present.add("external_main")
            else:
                present.add("internal_main")
    # Słupy szczytowe (ryglówka) generowane są zawsze, niezależnie od siatki głównej
    present.add("external_intermediate_cladding")
    return present


def _column_cross_section(block, category: str):
    method = getattr(block, "column_method", "default")
    if method == "manual":
        sec = (getattr(block, "manual_column_sections", None) or {}).get(category)
        if sec and len(sec) >= 2:
            return sec[0], sec[1]
    default_sec = DEFAULTS.column_sections.get(category, [0.4, 0.4])
    return default_sec[0], default_sec[1]


def _tributary(block, category: str):
    """Zwraca (powierzchnia_dachu_m2, szerokosc_sciany_m) dla danej kategorii słupa."""
    number_of_aisles = max(1, int(getattr(block, "number_of_aisles", 1) or 1))
    aisle_width = block.width / number_of_aisles
    bay_spacing = block.bay_spacing

    if category == "internal_main":
        return aisle_width * bay_spacing, 0.0
    if category == "external_main":
        return (aisle_width / 2) * bay_spacing, bay_spacing
    if category == "external_corner":
        return (aisle_width / 2) * (bay_spacing / 2), bay_spacing / 2 + DEFAULTS.gable_column_spacing / 2
    # external_intermediate_cladding — słup ściany, bez udziału w dachu
    return 0.0, DEFAULTS.gable_column_spacing


def _compute_categories_for_block(params: HallParameters, block) -> dict:
    roof = compute_block_roof_loads(params, block)["summary"]
    n_variable_kn_m2 = max(roof["sniegu_rownomiernego_kn_m2"], roof["uzytkowe_kn_m2"])
    n_roof_kn_m2 = roof["stale_kn_m2"] + n_variable_kn_m2

    wall_height = block.clear_height
    foundation_depth = getattr(block, "foundation_depth", 1.0) or 1.0
    panel_weight_kg_m2 = get_wall_panel_weight(getattr(block, "cladding_panel_id", "SP2B_E_PIR_100"))
    wind_qp_wall = compute_wind_qp(params.wind_zone, params.terrain_category, wall_height)
    present = _present_categories(params, block)

    categories = {}
    for cat in COLUMN_CATEGORIES:
        if cat not in present:
            continue
        a_roof, wall_width = _tributary(block, cat)
        bx, bz = _column_cross_section(block, cat)
        col_weight_kn = bx * bz * wall_height * CONCRETE_DENSITY_KN_M3
        n_roof_kn = n_roof_kn_m2 * a_roof

        if cat != "internal_main" and wall_width > 0:
            wall_area = wall_width * wall_height
            wall_weight_kn = wall_area * panel_weight_kg_m2 * 9.81 / 1000.0
            cpe = CPE_WALL[cat]
            h_total_kn = wind_qp_wall * cpe * wall_area
            if cat in PINNED_BASE_CATEGORIES:
                # Słup przegubowy u dołu i u góry: moment nie przenosi się na stopę,
                # a siła pozioma dzieli się między podstawę i górne podparcie (rygiel/płatew)
                h_kn = 0.5 * h_total_kn
                m_knm = 0.0
            else:
                # Słup wspornikowy, utwierdzony w fundamencie — cała reakcja pozioma
                # i moment (przy ramieniu do połowy wysokości ściany) trafiają do stopy
                h_kn = h_total_kn
                arm_m = wall_height / 2 + foundation_depth
                m_knm = h_kn * arm_m
        else:
            wall_area = 0.0
            wall_weight_kn = 0.0
            h_kn = 0.0
            m_knm = 0.0

        n_total_kn = n_roof_kn + col_weight_kn + wall_weight_kn

        categories[cat] = {
            "n_kn": round(n_total_kn, 2),
            "h_kn": round(h_kn, 2),
            "m_knm": round(m_knm, 2),
            "breakdown": {
                "dach_kn": round(n_roof_kn, 2),
                "slup_kn": round(col_weight_kn, 2),
                "sciana_kn": round(wall_weight_kn, 2),
            },
            "a_roof_m2": round(a_roof, 2),
            "wall_area_m2": round(wall_area, 2),
        }
    return categories


def compute_column_loads(params: HallParameters) -> dict:
    if params.hall_type == "complex" and params.blocks:
        blocks = []
        for b in params.blocks:
            blocks.append({"block_id": b.block_id, "categories": _compute_categories_for_block(params, b)})
        return {"blocks": blocks}
    return {"blocks": [{"block_id": "Hala", "categories": _compute_categories_for_block(params, params)}]}
