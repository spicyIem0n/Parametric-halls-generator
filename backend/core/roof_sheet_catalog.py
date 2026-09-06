"""
RoofSheetCatalog — ciężary blach trapezowych dachowych [kg/m²].

Dane odzwierciedlają katalog ROOF_SHEET_CATALOG z frontendu
(frontend/src/App.jsx). Utrzymywane osobno, bo backend nie ma dostępu
do plików frontendu — przy dodaniu nowej blachy w App.jsx należy
dopisać jej ciężar również tutaj.
"""

ROOF_SHEET_WEIGHTS_KG_M2 = {
    "T55_07": 7.6,
    "T85_08": 9.2,
    "T100_088": 10.8,
    "T130_10": 13.4,
    "T150_10": 14.8,
    "T160_125": 17.2,
}

DEFAULT_ROOF_SHEET_WEIGHT_KG_M2 = 9.2  # fallback = T85_08


def get_roof_sheet_weight(roof_sheet_id: str) -> float:
    return ROOF_SHEET_WEIGHTS_KG_M2.get(roof_sheet_id, DEFAULT_ROOF_SHEET_WEIGHT_KG_M2)


# ---------------------------------------------------------------------------
# Geometria profilu — potrzebna do obliczenia tarczowego działania poszycia
# (stressed-skin diaphragm action, PN-EN 1993-1-3 rozdz. 10 + ECCS nr 88).
#
# h  — wysokość profilu [mm]
# d  — rozstaw (podziałka) fałd [mm]
# t  — grubość netto blachy bez powłok [mm]
# l  — szerokość górnej półki fałdy [mm]
#
# UWAGA: podziałki i szerokości półek to wartości typowe dla rodziny profili.
# Przed użyciem w projekcie należy je potwierdzić z kartą techniczną producenta.
# ---------------------------------------------------------------------------
ROOF_SHEET_GEOMETRY = {
    #            h     d     t     l
    "T55_07":   (55,  250, 0.70,  60),
    "T85_08":   (85,  280, 0.80,  65),
    "T100_088": (100, 275, 0.88,  70),
    "T130_10":  (130, 310, 1.00,  75),
    "T150_10":  (150, 290, 1.00,  75),
    "T160_125": (160, 250, 1.25,  70),
}

DEFAULT_ROOF_SHEET_GEOMETRY = ROOF_SHEET_GEOMETRY["T85_08"]


def get_roof_sheet_geometry(roof_sheet_id: str):
    """Zwraca (h, d, t, l) w mm dla podanego profilu blachy trapezowej."""
    return ROOF_SHEET_GEOMETRY.get(roof_sheet_id, DEFAULT_ROOF_SHEET_GEOMETRY)
