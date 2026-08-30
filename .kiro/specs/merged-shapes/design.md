# Projekt techniczny — Scalanie modułów w kształty złożone (L/T/U)

## Przegląd

Funkcja rozszerza istniejący post-processing połączeń modułów (`HallGenerator._process_connections`) o obsługę prawdziwego scalenia dla typu połączenia `none`. Obecnie `none` usuwa tylko ściany (sandwich_panel, plinth, girt) na linii styku. Rozszerzenie dodaje usuwanie zdublowanego rzędu słupów (`column`, `column_gable`) i fundamentów (`foundation`) na wspólnej krawędzi, tak aby powstała jedna spójna bryła o kształcie L/T/U/krzyż zamiast dwóch sklejonych hal.

Zmiana jest skoncentrowana w jednej metodzie backendu. Generatory pozostają nietknięte. Frontend zyskuje jedynie czytelniejszy opis opcji scalenia.

## Architektura

```
HallGenerator._generate_complex()
    │  generuje moduły (bez zmian)
    ▼
_process_connections(components)
    │  1. oblicz block_bounds (obrysy po obrocie) — istnieje
    │  2. dla kazdego polaczenia wyznacz strefe styku — istnieje
    │  3a. usuwanie/przycinanie SCIAN — istnieje
    │  3b. NOWE: dla typu "none" usun zdublowane SLUPY i FUNDAMENTY
    │       na linii styku (rzad jednego z modulow)
    ▼
lista Component3D → frontend
```

## Zasada usuwania zdublowanego rzędu

Przy połączeniu `none` na linii styku obie hale mają własny rząd słupów (każda swoją ramę skrajną). Aby powstała jedna przestrzeń, usuwamy rząd **jednego** modułu — deterministycznie modułu o wyższym indeksie w połączeniu (`moduleB`), zostawiając rząd `moduleA`.

Identyfikacja słupów/stóp do usunięcia:
- Element należy do modułu B (`meta.block_id == bid_b`).
- Leży na linii styku: dla styku w osi X — `abs(pos_x - x_coord) < tol_col`; dla styku w osi Z — `abs(pos_z - z_coord) < tol_col`.
- Leży w obrębie wspólnego odcinka styku (overlap): druga współrzędna mieści się w `[rng_min, rng_max]`.

Tolerancja `tol_col` ~ 0.6 m (słup + luz). Overlap już liczony w istniejącym kodzie (z_min/z_max lub x_min/x_max strefy).

## Komponenty i interfejsy

### Backend: `_process_connections` — rozszerzenie

Do istniejącej struktury `remove_zones` dodać flagę typu połączenia (już jest `conn_type` w krotce). Po fazie filtrowania ścian dodać drugą fazę: filtrowanie słupów i fundamentów.

Pseudokod nowej fazy:
```python
# Zbierz strefy scalenia (tylko none) z informacja ktory modul traci rzad
merge_zones = []  # (axis, coord, rng_min, rng_max, bid_loser)
for zone in remove_zones:
    (axis, coord, rng_min, rng_max, ctype, h_a, h_b, bid_a, bid_b) = zone
    if ctype == "none":
        merge_zones.append((axis, coord, rng_min, rng_max, bid_b))  # B traci rzad

STRUCT_TYPES = {"column", "column_gable", "foundation"}
tol_col = 0.6
result = []
for c in filtered:                       # filtered = po usunieciu scian
    drop = False
    if c.type in STRUCT_TYPES:
        bid = c.meta.get("block_id", "") if c.meta else ""
        px, py, pz = c.position
        for (axis, coord, rng_min, rng_max, bid_loser) in merge_zones:
            if bid != bid_loser:
                continue
            if axis == "x":
                on_line = abs(px - coord) < tol_col
                in_overlap = (rng_min - 0.5) <= pz <= (rng_max + 0.5)
            else:
                on_line = abs(pz - coord) < tol_col
                in_overlap = (rng_min - 0.5) <= px <= (rng_max + 0.5)
            if on_line and in_overlap:
                drop = True
                break
    if not drop:
        result.append(c)
return result
```

Uwaga: faza słupów działa na wyniku fazy ścian (`filtered`), a nie na oryginalnej liście. Kolejność: najpierw ściany (istniejąca logika), potem słupy/fundamenty (nowa).

### Frontend: panel połączeń (Controls.jsx / ConnectionsPanel)

- Etykieta opcji „none" doprecyzowana: „Bez ściany (scal w jedną przestrzeń)".
- Opis efektu w panelu: przy wybranym „none" pokazać notę „Usuwa ściany i zdublowany rząd słupów na styku (kształt L/T/U)".
- Blokada „none" dla prostopadłych ram — bez zmian (już istnieje).

## Modele danych

Bez zmian. `module_connections` już zawiera `{moduleA, moduleB, type}`. Typ `none` już istnieje.

## Obsługa błędów i przypadki brzegowe

- Styk częściowy: overlap ogranicza usuwanie do wspólnego odcinka (druga współrzędna w zakresie rng_min..rng_max). Słupy poza overlapem pozostają.
- Brak przylegania: jeśli moduły nie stykają się (brak strefy w remove_zones), scalenie nie jest stosowane.
- Moduł B nie ma słupów dokładnie na linii (inny rozstaw): usuwane są tylko te, które faktycznie leżą na linii — jeśli żadne, rząd A i tak zostaje jako wspólny (akceptowalne).
- Tolerancja tol_col dobrana tak, by nie usuwać słupów wewnętrznych naw (te są dalej od linii styku niż 0.6 m).

## Strategia testów

Testy API (PowerShell/REST):
1. Dwa moduły stykające się bokiem (np. 30×60 + 20×40) z połączeniem `none`: liczba `column`+`column_gable` mniejsza niż przy `expansion_joint` (usunięty rząd B na styku).
2. Liczba `foundation` mniejsza przy `none` niż przy `expansion_joint` (usunięte stopy pod zdjętymi słupami).
3. Brak `sandwich_panel` na linii styku przy `none` (jak dotychczas).
4. Połączenie `expansion_joint`: liczba słupów bez zmian względem stanu sprzed funkcji (brak regresji).
5. Kształt L: trzy moduły, dwa styki `none` — model spójny, słupy tylko pojedyncze na obu liniach styku.
6. Parsowanie: backend .py (ast), frontend .jsx (esbuild); endpointy odpowiadają.

## Uzasadnienie decyzji projektowych

- **Usuwanie rzędu modułu B (wyższy indeks):** deterministyczne, przewidywalne; użytkownik może zmienić kolejność modułów jeśli chce zachować konkretny rząd. Prostsze niż liczenie „który rząd bardziej pasuje".
- **Druga faza po ścianach, nie łączenie:** zachowuje istniejącą, przetestowaną logikę ścian bez ryzyka regresji; słupy to osobny, additywny krok.
- **Tylko column/column_gable/foundation:** dźwigary i płatwie modułu B pozostają — opierają się na wspólnym rzędzie słupów A (który stoi w tym samym miejscu co usunięty rząd B, bo moduły przylegają). To akceptowalne uproszczenie w tej iteracji.
- **Bez rynny koszowej i łączenia połaci:** świadomie poza zakresem (zgodnie z ustaleniami), do osobnej iteracji.
