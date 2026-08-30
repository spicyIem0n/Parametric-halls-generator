"""
TakeoffCalculator — modul przedmiaru ilosciowego.
Liczy pozycje przedmiaru na podstawie wygenerowanych komponentow modelu 3D.
Kazda pozycja rozbita na material + montaz (pozycje blizniacze).
"""

from models import HallParameters
from generators.hall_generator import HallGenerator

# Wskazniki
STEEL_ROOF_KG_PER_M2 = 12.0      # kg/m2 powierzchni hali (dzwigary+platwie+stezenia dachu)
RYGLOWKA_KG_PER_SET = 400.0      # kg/komplet na 1 otwor (info pomocnicza)

# Typy pomijane w agregacji
_SKIP_TYPES = {
    "truss_chord", "truss_web", "purlin", "purlin_strut", "bracing_roof",
    "girt", "trimmer", "cladding_rail",
    "reserve_zone_marker", "reserve_truss_marker", "reserve_purlin_doubled",
}


def _vol(s):
    return s[0] * s[1] * s[2]

def _area_plate(s):
    # powierzchnia = iloczyn dwoch wiekszych skladowych (pomijamy najmniejsza=grubosc)
    ss = sorted(s)
    return ss[1] * ss[2]

def _len_bar(s):
    return max(s)


class TakeoffCalculator:
    @staticmethod
    def compute(params: HallParameters) -> list[dict]:
        comps = HallGenerator(params).generate_all_components()
        agg = TakeoffCalculator._aggregate(comps)
        hall_area = TakeoffCalculator._hall_area(params)
        return TakeoffCalculator._build_items(agg, hall_area)

    @staticmethod
    def _hall_area(params: HallParameters) -> float:
        if params.hall_type == "complex" and params.blocks:
            return sum(b.width * b.length for b in params.blocks)
        return params.width * params.length

    @staticmethod
    def _aggregate(comps) -> dict:
        # Zwraca slownik z surowymi wartosciami dla kazdej grupy
        a = {
            "col_count": 0, "col_vol": 0.0,
            "found_vol": 0.0,
            "roof_cover_m2": 0.0,
            "cladding_m2": 0.0,
            "floor_m2": 0.0,
            "subbase_m3": 0.0,
            "plinth_m3": 0.0, "plinth_mb": 0.0,
            "dock_doors": 0, "gate_doors": 0, "dock_shelters": 0,
            "skylights": 0, "smoke_vents": 0, "light_strip_m2": 0.0,
            "firewall_m2": 0.0,
            "bracing_mb": 0.0,
            "techroom_m2": 0.0, "techroom_doors": 0,
            "office_m2": 0.0, "office_cols": 0, "office_stairs": 0,
            "mezz_m2": 0.0, "mezz_cols": 0, "mezz_balustrade_mb": 0.0, "mezz_stairs": 0,
            "drainage_inlets": 0,
        }
        for c in comps:
            t = c.type
            s = c.scale
            if t in _SKIP_TYPES:
                continue
            if t in ("column", "column_gable"):
                a["col_count"] += 1
                a["col_vol"] += _vol(s)
            elif t == "foundation":
                a["found_vol"] += _vol(s)
            elif t == "roof_panel":
                a["roof_cover_m2"] += s[0] * s[2]
            elif t == "sandwich_panel":
                a["cladding_m2"] += _area_plate(s)
            elif t == "floor_slab":
                a["floor_m2"] += s[0] * s[2]
            elif t.startswith("floor_base_"):
                a["subbase_m3"] += _vol(s)
            elif t == "plinth":
                a["plinth_m3"] += _vol(s)
                a["plinth_mb"] += max(s[0], s[2])
            elif t == "dock_door":
                a["dock_doors"] += 1
            elif t == "gate_door":
                a["gate_doors"] += 1
            elif t == "dock_shelter":
                a["dock_shelters"] += 1
            elif t == "skylight":
                a["skylights"] += 1
            elif t == "smoke_vent":
                a["smoke_vents"] += 1
            elif t == "light_strip":
                a["light_strip_m2"] += _area_plate(s)
            elif t in ("fire_wall", "fire_strip_roof"):
                a["firewall_m2"] += _area_plate(s)
            elif t == "bracing":
                a["bracing_mb"] += _len_bar(s)
            elif t in ("tech_room_wall", "tech_room_slab"):
                a["techroom_m2"] += _area_plate(s)
            elif t == "tech_room_door":
                a["techroom_doors"] += 1
            elif t in ("office_wall", "office_slab", "office_roof", "office_fire_wall"):
                a["office_m2"] += _area_plate(s)
            elif t == "office_column":
                a["office_cols"] += 1
            elif t == "office_stairs":
                a["office_stairs"] += 1
            elif t in ("mezzanine_slab", "mezzanine_fire_wall"):
                a["mezz_m2"] += _area_plate(s)
            elif t == "mezzanine_column":
                a["mezz_cols"] += 1
            elif t == "mezzanine_balustrade":
                a["mezz_balustrade_mb"] += _len_bar(s)
            elif t == "mezzanine_stairs":
                a["mezz_stairs"] += 1
            elif t == "drainage_inlet":
                a["drainage_inlets"] += 1
        return a

    @staticmethod
    def _build_items(a, hall_area) -> list[dict]:
        items = []
        lp = [0]  # licznik w liscie by domkniecie moglo modyfikowac

        def add(opis, jm, ilosc, uwagi=""):
            if ilosc is None:
                return
            # pomijamy pozycje zerowe
            if isinstance(ilosc, (int, float)) and abs(ilosc) < 1e-9:
                return
            lp[0] += 1
            items.append({
                "lp": lp[0],
                "opis": opis,
                "jednostka": jm,
                "ilosc": round(float(ilosc), 3),
                "cena_jedn": None,
                "wartosc": None,
                "uwagi": uwagi,
            })

        def add_pair(nazwa, jm_mat, il_mat, jm_mont, il_mont, uwagi=""):
            # dodaje pozycje blizniacze material + montaz (pomija gdy obie zerowe)
            has_mat = il_mat is not None and abs(il_mat) > 1e-9
            has_mont = il_mont is not None and abs(il_mont) > 1e-9
            if not has_mat and not has_mont:
                return
            add(nazwa + " — materiał", jm_mat, il_mat, uwagi)
            add(nazwa + " — montaż", jm_mont, il_mont, uwagi)

        # Slupy prefabrykowane: material m3, montaz szt
        add_pair("Słup prefabrykowany", "m³", a["col_vol"], "szt", a["col_count"])
        # Stopy fundamentowe: material m3, montaz m3
        add_pair("Stopa fundamentowa", "m³", a["found_vol"], "m³", a["found_vol"])
        # Konstrukcja stalowa dachu: wskaznik 12 kg/m2
        steel = STEEL_ROOF_KG_PER_M2 * hall_area
        add_pair("Konstrukcja stalowa dachu", "kg", steel, "kg", steel,
                 uwagi="wskaźnik 12 kg/m²")
        # Ryglowka bram/dokow: komplety = liczba otworow
        openings = a["dock_doors"] + a["gate_doors"]
        add_pair("Ryglówka bram/doków", "kpl", openings, "kpl", openings,
                 uwagi="400 kg/kpl")
        # Plyta warstwowa scienna
        add_pair("Płyta warstwowa", "m²", a["cladding_m2"], "m²", a["cladding_m2"])
        # Pokrycie dachu
        add_pair("Pokrycie dachu", "m²", a["roof_cover_m2"], "m²", a["roof_cover_m2"])
        # Posadzka
        add_pair("Posadzka przemysłowa", "m²", a["floor_m2"], "m²", a["floor_m2"])
        # Podbudowa
        add_pair("Podbudowa", "m³", a["subbase_m3"], "m³", a["subbase_m3"])
        # Podwaliny
        add_pair("Podwalina", "m³", a["plinth_m3"], "mb", a["plinth_mb"])
        # Bramy dokowe
        add_pair("Brama dokowa", "szt", a["dock_doors"], "szt", a["dock_doors"])
        # Bramy kurierskie
        add_pair("Brama kurierska", "szt", a["gate_doors"], "szt", a["gate_doors"])
        # Doki fartuchy (3 elem na dok)
        docks = round(a["dock_shelters"] / 3) if a["dock_shelters"] else 0
        add_pair("Dok (fartuch uszczelniający)", "kpl", docks, "kpl", docks)
        # Swietliki
        add_pair("Świetlik", "szt", a["skylights"], "szt", a["skylights"])
        # Klapy dymowe
        add_pair("Klapa dymowa", "szt", a["smoke_vents"], "szt", a["smoke_vents"])
        # Pasma swietlne
        add_pair("Pasmo świetlne", "m²", a["light_strip_m2"], "m²", a["light_strip_m2"])
        # Sciany PPOZ
        add_pair("Ściana PPOŻ", "m²", a["firewall_m2"], "m²", a["firewall_m2"])
        # Stezenia
        add_pair("Stężenia ścienne", "mb", a["bracing_mb"], "mb", a["bracing_mb"])
        # Wpusty dachowe
        add_pair("Wpust dachowy", "szt", a["drainage_inlets"], "szt", a["drainage_inlets"])
        # Pomieszczenia techniczne
        add_pair("Pomieszczenie techniczne", "m²", a["techroom_m2"], "m²", a["techroom_m2"])
        add_pair("Drzwi techniczne EI", "szt", a["techroom_doors"], "szt", a["techroom_doors"])
        # Biura zewnetrzne
        add_pair("Biuro zewnętrzne", "m²", a["office_m2"], "m²", a["office_m2"])
        add_pair("Słup biurowy", "m³", None, "szt", a["office_cols"])
        add_pair("Schody biurowe", "szt", a["office_stairs"], "szt", a["office_stairs"])
        # Antresole
        add_pair("Antresola", "m²", a["mezz_m2"], "m²", a["mezz_m2"])
        add_pair("Słup antresoli", "szt", a["mezz_cols"], "szt", a["mezz_cols"])
        add_pair("Balustrada antresoli", "mb", a["mezz_balustrade_mb"], "mb", a["mezz_balustrade_mb"])
        add_pair("Schody antresoli", "szt", a["mezz_stairs"], "szt", a["mezz_stairs"])

        return items
