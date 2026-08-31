"""
WallPanelCatalog — ciężary płyt warstwowych ściennych [kg/m²].

Dane odzwierciedlają katalog RUUKKI_CATALOG z frontendu (frontend/src/App.jsx).
Wartości ciężaru są ORIENTACYJNE (na podstawie typowych kart technicznych rdzeni
PIR/wełna mineralna) — do zweryfikowania z kartą techniczną konkretnego produktu
przed wymiarowaniem konstrukcji. Utrzymywane osobno, bo backend nie ma dostępu
do plików frontendu — przy dodaniu nowego panelu w App.jsx należy dopisać jego
ciężar również tutaj.
"""

WALL_PANEL_WEIGHTS_KG_M2 = {
    "SP2B_E_PIR_100": 10.5,
    "SP2B_E_PIR_150": 12.5,
    "SP2E_X_PIR_120": 11.3,
    "SP2E_X_PIR_160": 13.0,
    "nSPB_WE_100": 18.0,
    "nSPB_WE_150": 23.0,
}

DEFAULT_WALL_PANEL_WEIGHT_KG_M2 = 10.5  # fallback = SP2B_E_PIR_100


def get_wall_panel_weight(panel_id: str) -> float:
    return WALL_PANEL_WEIGHTS_KG_M2.get(panel_id, DEFAULT_WALL_PANEL_WEIGHT_KG_M2)
