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
