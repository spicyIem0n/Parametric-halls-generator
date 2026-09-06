"""
Tarczowe działanie poszycia dachu z blachy trapezowej (stressed-skin diaphragm).

Podstawa: PN-EN 1993-1-3 rozdz. 10 (Stressed skin design) oraz
ECCS Publication No. 88 "European Recommendations for the Application of
Metal Sheeting acting as a Diaphragm" (1995), rozdz. 5 — tablice 5.5-5.9.

Model liczy:
  1. podatność postaciową tarczy c [mm/kN] jako sumę składników
     c = c1.1 + c1.2 + c2.1 + c2.2 + c2.3
  2. sztywność postaciową S = 1/c [kN/mm]
  3. zastępczą powierzchnię przekroju przekątnej A_eq [m2], którą można wstawić
     do modelu MES zamiast tarczy (para krzyżulców tension-only na panel)
  4. nośność tarczy V_Rd jako minimum trzech postaci zniszczenia
     (zamki, łączniki blacha/płatew, zmiażdżenie profilu na końcu)

ZASTRZEŻENIA — konieczne przed użyciem w projekcie:
  * Warunkiem stosowania jest zamocowanie blachy do płatwi ORAZ do elementów
    obrzeża na WSZYSTKICH CZTERECH krawędziach panelu, z łącznikami w zakładach.
  * Łączniki muszą być wymiarowane na ścinanie tarczy, nie tylko na ssanie.
  * Brak dużych otworów (świetliki, klapy dymowe) w obrębie panelu.
  * PN-EN 1993-1-3 wymaga zapisu w dokumentacji, że poszycia nie wolno
    zdemontować ani przewiercić bez ponownej analizy stateczności.
  * Stała profilu K jest tu interpolowana przybliżeniem — patrz _sheeting_K().
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import hypot
from typing import Dict, List

E_STEEL = 205.0        # kN/mm2
NU = 0.3
FYB = 320.0            # N/mm2 — podstawowa granica plastyczności blachy S320GD

# Poślizg łączników [mm/kN] — ECCS nr 88, tabl. 5.1/5.2 (wkręty samowiercące)
SLIP_SHEET_PURLIN = 0.15     # sp — wkręt 6,3 mm z podkładką stalową
SLIP_SEAM = 0.25             # ss — wkręt zamka 4,8 mm
SLIP_SHEAR_CONNECTOR = 0.15  # ssc

# Nośności obliczeniowe łączników [kN] — wartości typowe, do potwierdzenia
F_P = 6.0 * 1.0              # blacha/płatew: 6,0 kN na 1 mm grubości blachy
F_S = 2.5 * 1.0              # zamek: 2,5 kN na 1 mm grubości blachy

# ECCS nr 88, tabl. 5.4 — wpływ płatwi pośrednich
_ALPHA = {2: (1.00, 1.00, 1.00), 3: (1.00, 1.00, 1.00), 4: (0.85, 0.75, 0.90),
          5: (0.70, 0.67, 0.80), 6: (0.60, 0.55, 0.71), 7: (0.60, 0.50, 0.64),
          8: (0.60, 0.44, 0.58), 9: (0.60, 0.40, 0.53), 10: (0.60, 0.36, 0.49)}


def _alphas(n_p: int):
    if n_p <= 2:
        return _ALPHA[2]
    return _ALPHA[min(n_p, 10)]


def _sheeting_K(h: float, d: float) -> float:
    """Stała profilu K1 (łączniki w każdej fałdzie) — ECCS nr 88 tabl. 5.6.

    Tablica jest funkcją h/d, l/d i kąta środnika. Tu stosuję liniowe
    przybliżenie przez punkty z przykładów obliczeniowych ECCS:
      h/d = 0,24 -> K1 = 0,130   (TRP22)
      h/d = 0,47 -> K1 = 0,209   (TRP110)
    Odchyłka od tablicy sięga ok. +/-20%, dlatego wartość powinna być
    nadpisywana odczytem z tablicy albo z karty producenta.
    """
    r = h / d
    return max(0.08, 0.0477 + 0.343 * r)


@dataclass
class SheetProfile:
    h: float        # wysokość profilu [mm]
    d: float        # podziałka fałd [mm]
    t: float        # grubość netto [mm]
    l: float = 0.0  # szerokość półki [mm]
    sheet_width: float = 0.0      # szerokość krycia arkusza [mm]; 0 = wyznacz z podziałki
    sheet_length: float = 12000.0  # długość arkusza [mm]

    def __post_init__(self):
        if not self.sheet_width:
            # typowa szerokość krycia: 3 fałdy dla profili wysokich, 4 dla niskich
            self.sheet_width = (3.0 if self.h >= 100 else 4.0) * self.d


@dataclass
class DiaphragmPanel:
    """Panel tarczy. a — wymiar prostopadle do fałd, b — wzdłuż fałd [m]."""
    a: float
    b: float
    profile: SheetProfile
    purlin_spacing: float                # rozstaw płatwi [m]
    fasten_every_corrugation: bool = True
    K_override: float | None = None

    # wyniki
    c_components: Dict[str, float] = field(default_factory=dict)

    def shear_flexibility(self) -> float:
        """Podatność postaciowa c [mm/kN]."""
        pr = self.profile
        a, b = self.a * 1000.0, self.b * 1000.0      # -> mm
        d, h, t = pr.d, pr.h, pr.t

        n_p = max(2, int(round(self.b / self.purlin_spacing)) + 1)   # liczba płatwi w panelu
        a1, a2, a3 = _alphas(n_p)
        n_b = max(1, int(round(self.b * 1000.0 / pr.sheet_length)))  # liczba arkuszy na głębokości
        a4 = 1.0 + 0.3 * n_b if n_b > 1 else 1.0
        K = self.K_override if self.K_override is not None else _sheeting_K(h, d)
        if not self.fasten_every_corrugation:
            K *= 8.0        # K2 >> K1 (rząd wielkości wg tabl. 5.7)

        # c1.1 — dystorsja profilu
        c11 = a * d ** 2.5 * K * a1 * a4 / (E_STEEL * t ** 2.5 * b ** 2)
        # c1.2 — odkształcenie postaciowe blachy
        c12 = 2.0 * a * a2 * (1.0 + NU) * (1.0 + 2.0 * h / d) / (E_STEEL * t * b)
        # c2.1 — poślizg łączników blacha/płatew
        p = d if self.fasten_every_corrugation else 2.0 * d
        c21 = 2.0 * a * SLIP_SHEET_PURLIN * p * a3 / b ** 2
        # c2.2 — poślizg zamków
        n_sh = max(1, int(round(a / pr.sheet_width)))          # liczba arkuszy w szerokości panelu
        n_s = max(1, int(round(b / 500.0)))                    # zamki co ok. 500 mm
        n_f = max(2, int(round(pr.sheet_width / p)))
        beta1 = (n_f - 1) / n_f
        c22 = (2.0 * SLIP_SEAM * SLIP_SHEET_PURLIN * (n_sh - 1) /
               (2.0 * n_s * SLIP_SHEET_PURLIN + beta1 * n_p * SLIP_SEAM)) if n_sh > 1 else 0.0
        # c2.3 — poślizg łączników blacha/element obrzeża
        n_sc = max(1, int(round(a / p)))
        c23 = 2.0 * SLIP_SHEAR_CONNECTOR / n_sc

        self.c_components = {"c1.1": c11, "c1.2": c12, "c2.1": c21,
                             "c2.2": c22, "c2.3": c23}
        return c11 + c12 + c21 + c22 + c23

    def shear_flexibility_conservative(self) -> float:
        """Zachowawcza podatność: większa z dwóch orientacji panelu.

        Sztywność tarczy jest kierunkowa — badania MES pokazują, że w kierunku
        poprzecznym do fałd panel może być kilkukrotnie podatniejszy niż wzdłuż.
        W dachu hali stan naprężenia jest czystym ścinaniem (obie orientacje
        pracują), dlatego przyjmuję niekorzystniejszą z nich.
        """
        c1 = self.shear_flexibility()
        comp1 = dict(self.c_components)
        swapped = DiaphragmPanel(a=self.b, b=self.a, profile=self.profile,
                                 purlin_spacing=self.purlin_spacing,
                                 fasten_every_corrugation=self.fasten_every_corrugation,
                                 K_override=self.K_override)
        c2 = swapped.shear_flexibility()
        if c1 >= c2:
            self.c_components = comp1
            return c1
        self.c_components = swapped.c_components
        return c2

    def shear_stiffness_kn_per_m(self) -> float:
        """S = 1/c, przeliczone na kN/m przemieszczenia."""
        return 1000.0 / self.shear_flexibility_conservative()

    def shear_resistance_kn(self) -> Dict[str, float]:
        """V_Rd — minimum z postaci zniszczenia (ECCS nr 88 rozdz. 6)."""
        pr = self.profile
        b = self.b * 1000.0
        n_p = max(2, int(round(self.b / self.purlin_spacing)) + 1)
        a1, _, _ = _alphas(n_p)
        n_s = max(1, int(round(b / 500.0)))
        p = pr.d if self.fasten_every_corrugation else 2.0 * pr.d
        n_f = max(2, int(round(pr.sheet_width / p)))
        beta1 = (n_f - 1) / n_f
        n_b = max(1, int(round(b / pr.sheet_length)))
        a4 = 1.0 + 0.3 * n_b if n_b > 1 else 1.0
        k_end = 0.9 if self.fasten_every_corrugation else 0.3

        v_seam = n_s * F_S + n_p * F_P / (a1 * beta1)
        v_fast = 0.6 * b * F_P / (p * a4)
        # ECCS nr 88 / ESDEP 9.5: V = k * t^1.5 * b * fy / sqrt(d)  [fy w kN/mm2]
        v_end = k_end * pr.t ** 1.5 * b * (FYB / 1000.0) / pr.d ** 0.5
        out = {"zamki": v_seam, "lacznik_blacha_platew": v_fast, "zmiazdzenie_profilu": v_end}
        out["V_Rd"] = min(out.values())
        return out

    def equivalent_diagonal_area_m2(self, load_dir_len: float | None = None) -> float:
        """Zastępcza powierzchnia przekątnej [m2] dla pary krzyżulców tension-only.

        Dla panelu o wymiarze L wzdłuż kierunku siły poprzecznej i H prostopadle:
            A_eq = S * Ld^3 / (E * L^2),   Ld = sqrt(L^2 + H^2)
        Wyprowadzenie: przemieszczenie od krzyżulca Δ = V*Ld^3/(E*A*L^2).
        """
        L = load_dir_len if load_dir_len is not None else self.a
        H = self.b if load_dir_len is None else (self.a if abs(load_dir_len - self.b) < 1e-9 else self.b)
        S = self.shear_stiffness_kn_per_m()                       # kN/m
        Ld = hypot(L, H)
        E_kn_m2 = E_STEEL * 1e6                                   # kN/mm2 -> kN/m2
        return S * Ld ** 3 / (E_kn_m2 * L ** 2)


def panel_from_params(a: float, b: float, roof_sheet_id: str, purlin_spacing: float,
                      fasten_every_corrugation: bool = True) -> DiaphragmPanel:
    from core.roof_sheet_catalog import get_roof_sheet_geometry
    h, d, t, l = get_roof_sheet_geometry(roof_sheet_id)
    return DiaphragmPanel(a=a, b=b, profile=SheetProfile(h=h, d=d, t=t, l=l),
                          purlin_spacing=purlin_spacing,
                          fasten_every_corrugation=fasten_every_corrugation)
