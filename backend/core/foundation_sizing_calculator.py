"""
FoundationSizingCalculator — automatyczny dobór gabarytów (a×b×h) stóp
fundamentowych na podstawie obciążeń charakterystycznych słupa (N, H, M)
i dopuszczalnego obciążenia gruntu (qdop).

Metoda klasyczna (wartości charakterystyczne, bez współczynników częściowych),
z uwzględnieniem mimośrodu metodą powierzchni efektywnej (Meyerhof):
1. A_wymagane = N / qdop
2. e = M / N; wymiar w kierunku momentu a ≥ max(√A_wymagane, 6·e) (warunek
   rdzenia przekroju e ≤ a/6, bez odrywania podstawy stopy)
3. b = A_wymagane / (a − 2e) — nośność sprawdzana na powierzchni EFEKTYWNEJ
   (a−2e)×b, nie na całym a×b (klasyczny błąd: liczenie b z pełnego a przy
   wydłużonym a daje absurdalnie wąską stopę, wyglądającą jak ława)
4. Korekta foremności: jeśli a/b przekracza MAX_ASPECT_RATIO (2:1), oba wymiary
   są przeliczane WSPÓLNIE (przy zachowanej proporcji), by stopa pozostała
   zwarta — kosztem częściowego odstępstwa od warunku e≤a/6 (sygnalizowanego
   ostrzeżeniem), zamiast dalszego wydłużania stopy
5. Zaokrąglenie a, b w górę do modułu 0,1 m
6. Grubość: h ≈ max(a,b)/5, zaokrąglona w górę do 0,1 m, min. MIN_THICKNESS

UWAGA: dobór ma charakter orientacyjny/przedwymiarowy — patrz ASSUMPTIONS_NOTE.
Nie zastępuje pełnego sprawdzenia nośności/osiadania gruntu (PN-EN 1997) ani
sprawdzenia konstrukcyjnego (przebicie, zbrojenie) wykonanego przez uprawnionego
konstruktora.
"""
import math

from models import HallParameters
from core.column_load_calculator import compute_column_loads, COLUMN_CATEGORIES

ASSUMPTIONS_NOTE = (
    "Dobór gabarytów stóp fundamentowych ma charakter orientacyjny (przedwymiarowanie). "
    "Obciążenia N/H/M są uproszczone (powierzchnie wpływu liczone formułowo, jeden "
    "reprezentatywny współczynnik cpe ściany na kategorię słupa, bez pełnej analizy "
    "kombinacji obciążeń wg PN-EN 1990/1997). Przyjęty system konstrukcyjny: każda nawa ma "
    "własny, przegubowo podparty dźwigar — słupy zewnętrzne i narożne (dotykające ściany) są "
    "wspornikowe, utwierdzone w fundamencie, więc cały moment od wiatru trafia do stopy. "
    "Słupy wewnętrzne to wyłącznie podpórki dla dźwigarów (nie dotykają żadnej ściany), więc "
    "nie przenoszą wiatru wcale (H=M=0) — to typowe dla hal wielonawowych, ale przy ciągłej "
    "ramie sztywnej lub stężeniach wiatrowych przechodzących przez to przęsło realne M byłoby "
    "niezerowe. Słupy pośrednie ściany (ryglówka) potraktowano jako przegubowe u dołu i u góry "
    "(mocowane do rygla/płatwi) — moment na fundament nie jest przenoszony (M=0), a siła "
    "pozioma dzieli się po połowie z górnym podparciem. Nośność sprawdzana na powierzchni "
    "efektywnej (metoda Meyerhofa), a proporcje boków ograniczone do 2:1, by uniknąć "
    "nierealistycznie wąskich kształtów — gdy to ogranicza spełnienie warunku e≤a/6, "
    "sygnalizuje to ostrzeżenie przy danej pozycji. Wartość qdop musi pochodzić z dokumentacji "
    "geotechnicznej działki. Wynik nie obejmuje sprawdzenia nośności/osiadania gruntu, oporu "
    "na poślizg ani zbrojenia — wymaga weryfikacji przez uprawnionego konstruktora przed "
    "wykonaniem."
)

CATEGORY_LABELS = {
    "internal_main": "Słup wewnętrzny",
    "external_main": "Słup zewnętrzny (ściana boczna)",
    "external_corner": "Słup narożny",
    "external_intermediate_cladding": "Słup pośredni ściany (szczyt/wzdłużny)",
}

ROUND_STEP = 0.1
MIN_DIM = 1.0
MAX_DIM = 6.0
MIN_THICKNESS = 0.4
MAX_ASPECT_RATIO = 2.0  # maks. stosunek dłuższego do krótszego boku — dalej stopa przestaje być "foremna"


def _round_up(value: float, step: float = ROUND_STEP) -> float:
    return math.ceil(value / step - 1e-9) * step


def _size_footing(n_kn: float, h_kn: float, m_knm: float, qdop_kpa: float):
    qdop = qdop_kpa if qdop_kpa and qdop_kpa > 0 else 1.0
    n = max(n_kn, 1e-6)
    e = (m_knm / n_kn) if n_kn > 1e-6 else 0.0
    req_area = n / qdop  # wymagana powierzchnia przy czysto osiowym obciążeniu

    # 1) Punkt wyjścia: kwadrat z warunku nośności osiowej, wydłużony w razie
    #    potrzeby do warunku rdzenia przekroju (brak odrywania podstawy stopy)
    a = max(math.sqrt(req_area), 6 * e, MIN_DIM)
    # 2) Nośność sprawdzana na powierzchni EFEKTYWNEJ (a-2e)×b (metoda Meyerhofa) —
    #    nie na całym a×b, bo to właśnie dawało absurdalnie wąskie stopy przy dużym e
    a_eff = max(a - 2 * e, 0.05)
    b = max(req_area / a_eff, MIN_DIM)

    warnings = []

    # 3) Korekta foremności — jeśli wyszło zbyt wydłużone (jak ława), szukamy
    #    zwartszego kształtu o stałej proporcji a=R·b, wciąż spełniającego
    #    nośność na powierzchni efektywnej: (R·b - 2e)·b = req_area
    if a / b > MAX_ASPECT_RATIO:
        R = MAX_ASPECT_RATIO
        disc = (2 * e) ** 2 + 4 * R * req_area
        b = max((2 * e + math.sqrt(disc)) / (2 * R), MIN_DIM)
        a = R * b

    if n_kn > 1e-6 and e > a / 6 + 1e-6:
        warnings.append(
            "Przy zachowaniu zwartych proporcji stopy mimośród (M/N) przekracza klasyczny warunek "
            "rdzenia przekroju e≤a/6 — możliwe częściowe odrywanie podstawy stopy pod obciążeniem "
            "wiatrem. Wymaga weryfikacji naprężeń brzegowych lub innego rozwiązania (słup przegubowy "
            "kotwiony punktowo, ława/płyta wspólna, zastrzały usztywniające ścianę).")

    a = _round_up(a)
    b = _round_up(b)
    h = max(MIN_THICKNESS, _round_up(max(a, b) / 5))

    if a > MAX_DIM or b > MAX_DIM:
        warnings.append(f"Wymiar przekracza {MAX_DIM:.0f} m — zbyt duże obciążenie / zbyt niska nośność gruntu; "
                         f"rozważyć ławę wspólną, płytę fundamentową lub posadowienie pośrednie.")

    return round(a, 2), round(b, 2), round(h, 2), warnings


class FoundationSizingCalculator:
    @staticmethod
    def compute(params: HallParameters) -> dict:
        column_loads = compute_column_loads(params)
        qdop = params.qdop_kpa

        result_blocks = []
        for blk in column_loads["blocks"]:
            categories_out = []
            for cat in COLUMN_CATEGORIES:
                if cat not in blk["categories"]:
                    continue  # kategoria nie występuje w tym module (np. brak słupów wewnętrznych przy 1 nawie)
                load = blk["categories"][cat]
                a, b, h, warnings = _size_footing(load["n_kn"], load["h_kn"], load["m_knm"], qdop)
                categories_out.append({
                    "category": cat,
                    "label": CATEGORY_LABELS[cat],
                    "n_kn": load["n_kn"],
                    "h_kn": load["h_kn"],
                    "m_knm": load["m_knm"],
                    "breakdown": load["breakdown"],
                    "required_area_m2": round(load["n_kn"] / qdop, 2) if qdop else None,
                    "size": {"a_m": a, "b_m": b, "h_m": h},
                    "warnings": warnings,
                })
            result_blocks.append({"block_id": blk["block_id"], "categories": categories_out})

        return {"blocks": result_blocks, "qdop_kpa": qdop, "assumptions": ASSUMPTIONS_NOTE}
