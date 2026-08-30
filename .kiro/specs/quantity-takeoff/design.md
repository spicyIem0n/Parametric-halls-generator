# Projekt techniczny — Moduł przedmiaru ilościowego

## Przegląd

Moduł liczy przedmiar na backendzie na podstawie tej samej listy `Component3D`, którą generuje `HallGenerator`. Nowy endpoint `POST /quantity-takeoff` przyjmuje `HallParameters`, generuje komponenty (tak jak `/generate-hall`) i agreguje je w pozycje przedmiarowe. Osobny endpoint `POST /quantity-takeoff/export` zwraca plik `.xlsx`. Frontend dodaje widok tabeli (osobny panel/zakładka) wypełniany po kliknięciu „Buduj Model 3D" oraz przycisk eksportu.

Liczenie odbywa się w backendzie (jedno źródło prawdy o geometrii), nie w JS — dzięki temu Excel i tabela w UI korzystają z tych samych liczb.

## Architektura

```
Controls „Buduj Model 3D" ──► App.handleGenerate()
        │                         ├─► POST /generate-hall  → components (3D)
        │                         └─► POST /quantity-takeoff → pozycje przedmiaru
        ▼
QuantityTakeoffView (nowy panel/zakladka)
        │  wyswietla tabele: Lp, Opis, Jm, Ilosc, Cena, Wartosc, Uwagi
        └─► przycisk „Eksportuj do Excel" ─► POST /quantity-takeoff/export ─► plik .xlsx
```

Backend:
```
main.py
  POST /quantity-takeoff        → TakeoffCalculator.compute(params) → {"items": [...]}
  POST /quantity-takeoff/export → openpyxl → StreamingResponse (.xlsx)

core/takeoff_calculator.py (nowy)
  compute(params) -> list[TakeoffItem]
    1. HallGenerator(params).generate_all_components()
    2. agregacja komponentow wg mapy TYPE_RULES
    3. pozycje wskaznikowe (stal dachu 12 kg/m2, ryglowka 400 kg/kpl)
    4. rozbicie kazdej pozycji na material + montaz
```

## Komponenty i interfejsy

### Backend: `core/takeoff_calculator.py` (nowy plik)

Model wyniku (zwykły dict lub Pydantic):
```
TakeoffItem = {
  "lp": int,
  "opis": str,          # np. "Słup prefabrykowany — materiał"
  "jednostka": str,     # "m³" | "szt" | "kg" | "m²" | "mb" | "kpl"
  "ilosc": float,       # zaokrąglona do 2-3 miejsc
  "cena_jedn": None,    # niewypełniane
  "wartosc": None,      # niewypełniane
  "uwagi": str          # np. "wskaźnik 12 kg/m²" lub ""
}
```

Główna funkcja:
```python
def compute(params: HallParameters) -> list[dict]:
    comps = HallGenerator(params).generate_all_components()
    agg = _aggregate(comps)           # slownik surowych ilosci wg grupy
    hall_area = _hall_area(params)    # suma szer*dl po modulach (complex) lub szer*dl (simple)
    return _build_items(agg, hall_area, params)
```

Zasady liczenia ilości surowej z `scale` (scale = rzeczywiste wymiary w metrach; długość pręta = największa/osiowa składowa; grubość = najmniejsza):
- objętość elementu = sx*sy*sz (m³)
- powierzchnia płyty = iloczyn dwóch większych składowych (pomijając grubość) (m²)
- długość pręta = max(sx, sy, sz) (mb)
- sztuki = liczba komponentów danego typu

Mapa grup (typ komponentu → grupa przedmiaru → sposób liczenia):
- Słupy: `column`, `column_gable` → grupa „columns": licz sztuki + objętość (m³)
- Stopy: `foundation` → „foundations": objętość (m³) [materiał] i objętość (m³) [montaż]
- Dach stalowy: NIE z komponentów — pozycja wskaźnikowa: `12 * hall_area` kg (dźwigary+płatwie+stężenia dachowe reprezentowane wskaźnikiem). Komponenty `truss_chord/truss_web/purlin/purlin_strut/bracing_roof` są pomijane w liczeniu materiałowym (zastąpione wskaźnikiem), by nie dublować.
- Ryglówka: liczba otworów = liczba `dock_door` + `gate_door`; pozycja „Ryglówka bram/doków" w kpl (ilość = liczba otworów), uwaga „400 kg/kpl".
- Obudowa ścienna: `sandwich_panel` → „cladding_wall": suma m² (dwie większe składowe).
- Pokrycie dachu: `roof_panel` → „roof_cover": suma m² (poziomy rzut = sx*sz).
- Posadzka: `floor_slab` → „floor": m² (sx*sz). Podbudowa: `floor_base_*` (prefiks) → „subbase": m³.
- Podwaliny: `plinth` → „plinth": m³ [materiał], mb [montaż] (mb = suma największych poziomych składowych).
- Bramy: `dock_door` → „dock_doors" szt; `gate_door` → „gate_doors" szt.
- Doki fartuchy: `dock_shelter` → „dock_shelters": kpl = liczba/3 (3 elementy na dok) zaokrąglona, lub liczba doków z docks_config.
- Świetliki: `skylight` → szt; klapy: `smoke_vent` (element_type smoke_vent/strip_smoke_vent) → szt; pasma: `light_strip` → m².
- Ściany PPOŻ: `fire_wall`, `fire_strip_roof` → m².
- Stężenia ścienne: `bracing` → mb.
- Pomieszczenia techniczne: `tech_room_wall`, `tech_room_slab` → m²; `tech_room_door` szt.
- Biura zewn.: `office_wall`, `office_slab`, `office_roof`, `office_fire_wall` → m²; `office_column` szt; `office_stairs` szt.
- Antresole: `mezzanine_slab`, `mezzanine_fire_wall` → m²; `mezzanine_column` szt; `mezzanine_balustrade` mb; `mezzanine_stairs` szt.
- Pomijane (markery): `reserve_zone_marker`, `reserve_truss_marker`, `drainage_inlet` (lub szt jeśli chcemy — decyzja: liczyć szt jako „Wpust dachowy").

Rozbicie materiał/montaż per grupa:
- Słupy: materiał m³ (objętość), montaż szt (liczba).
- Stopy: materiał m³, montaż m³.
- Dach stalowy: materiał kg, montaż kg (obie = 12*hall_area).
- Ryglówka: materiał kpl, montaż kpl (= liczba otworów).
- Płyty/pokrycia/posadzka/ściany/biura: materiał = ilość, montaż = ilość (ta sama jednostka).
- Podwaliny: materiał m³, montaż mb.

### Backend: `main.py` — dwa endpointy

```python
@app.post("/quantity-takeoff")
def quantity_takeoff(params: HallParameters):
    return {"items": TakeoffCalculator.compute(params)}

@app.post("/quantity-takeoff/export")
def quantity_takeoff_export(params: HallParameters):
    items = TakeoffCalculator.compute(params)
    wb = _build_xlsx(items, params)   # openpyxl
    return StreamingResponse(bytes, media_type=..., headers={Content-Disposition})
```

Excel: openpyxl. Nagłówki kolumn identyczne jak w UI. Kolumny Cena/Wartość puste. Nazwa pliku `przedmiar_hala_{width}x{length}.xlsx`.

### Frontend

- `api.js`: dodać `getQuantityTakeoff(params)` (POST /quantity-takeoff) i `exportTakeoff(params)` (POST /quantity-takeoff/export, pobranie blob → download).
- `App.jsx`: nowy stan `takeoff`. W `handleGenerate` po generacji modelu wywołać `getQuantityTakeoff(apiParams)` i zapisać wynik. Dodać przełącznik widoku (3D / Przedmiar) lub panel.
- Nowy komponent `QuantityTakeoffView.jsx`: renderuje tabelę z kolumnami L.p., Opis pozycji, Jednostka miary, Ilość, Cena jednostkowa, Wartość, Uwagi. Przycisk „Eksportuj do Excel".
- Widok przedmiaru jako zakładka/przełącznik obok sceny 3D (żeby nie zasłaniać modelu). Prosty toggle w App.

## Modele danych

Bez zmian w istniejących modelach. Nowy kontrakt wyjściowy `{"items": [TakeoffItem...]}`. `TakeoffItem` jak wyżej.

## Zależności

Dodać `openpyxl` do `backend/requirements.txt`.

## Obsługa błędów

- Pusty model / brak komponentów: zwróć pustą listę items; UI pokazuje stan pusty.
- Brak openpyxl: endpoint eksportu zwraca 500 z czytelnym komunikatem (po instalacji zależności działa).
- Complex bez bloków: hall_area = 0 → pozycje wskaźnikowe = 0.

## Strategia testów

Testy API (PowerShell/REST):
1. Hala simple 30×60: posadzka m² = 1800; stal dachu kg = 12*1800 = 21600 (materiał i montaż).
2. Hala z 2 dokami + 1 bramą: ryglówka kpl = 3; dock_doors szt = 2; gate_doors szt = 1.
3. Słupy: pozycja materiał m³ > 0 i montaż szt = liczba słupów (column + column_gable).
4. Complex 2 moduły: hall_area = suma, stal dachu = 12*(a1+a2).
5. Każda pozycja występuje w parze materiał+montaż.
6. Eksport: POST /quantity-takeoff/export zwraca poprawny plik xlsx (status 200, niepusty content, poprawny content-type).
7. Parsowanie: backend .py (ast), frontend .jsx (esbuild); endpointy odpowiadają.

## Uzasadnienie decyzji projektowych

- **Liczenie w backendzie:** jedno źródło prawdy (te same komponenty co model 3D), spójność tabeli i Excela, brak duplikacji logiki w JS.
- **Stal dachu wskaźnikowo, komponenty pomijane:** liczenie tonażu z bounding-boxów byłoby niedokładne (scale to gabaryt, nie profil). Wskaźnik 12 kg/m² jest świadomym uproszczeniem na etapie oferty; komponenty kratownic pomijamy by nie dublować pozycji.
- **Ryglówka jako kpl 400 kg:** uproszczenie ofertowe — komplet na otwór; liczba otworów z docks_config (dock_door+gate_door).
- **openpyxl w backendzie:** ładne formatowanie, jeden układ dla UI i pliku, prostsze utrzymanie niż generowanie po stronie JS.
- **Osobny widok, nie modal nad sceną:** przedmiar bywa długi; wygodniej w dedykowanym panelu/zakładce.
