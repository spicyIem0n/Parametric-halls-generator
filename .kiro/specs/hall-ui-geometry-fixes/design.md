# Hall UI & Geometry Fixes — Bugfix Design

## Overview

Zgłoszenie obejmuje siedem punktów, które sprowadzają się do trzech warstw defektu:

1. **Warstwa serializacji (przyczyna główna)** — `handleChange` w `Controls.jsx` konwertuje przez `parseFloat` każdą wartość poza checkboxem. Wybór dowolnej wartości tekstowej w `<select>` (`roof_drainage_type='gravity'`, `column_method='manual'`, `foundation_method='manual'`, w przyszłości `cladding_orientation='vertical'`) zapisuje `NaN`, `JSON.stringify` zamienia go na `null`, Pydantic odrzuca żądanie kodem 422, `api.js` zwraca `{ components: [] }` i scena 3D zostaje wyczyszczona. Naprawa: rozpoznanie typu pola (`e.target.type`) i konwersja numeryczna wyłącznie dla `range`/`number`, z zachowaniem poprzedniej wartości przy `NaN`.

2. **Warstwa geometrii dachu grawitacyjnego (defekty ukryte za punktem 1)** — po odblokowaniu selecta ujawnią się dwa błędy backendu: odbite rotacje połaci w `RoofFactory` (litera V zamiast ∧) oraz `GridSystem3D.get_parapet_height()` zwracające dla `gravity` wysokość kalenicy + 0.20 m, przez co `CladdingFactory` zamyka bryłę prostopadłościenną attyką ~2.8 m ponad okapem. Naprawa: korekta znaku rotacji, rozbicie jednej metody wysokościowej na trzy o rozłącznych znaczeniach (`get_eave_height`, `get_max_roof_height`, `get_wall_top_height`) oraz zakończenie ścian wzdłużnych na okapie ze schodkowym zamknięciem szczytów do linii połaci.

3. **Warstwa mechanizmu ręcznego i UI** — martwe kategorie `external_dock`/`internal_dock`, brak `external_corner`, mutowanie tablic stanu w miejscu, brak pól numerycznych obok suwaków, zbyt wąskie zakresy, prymitywny selektor doków, nieużywane `cladding_orientation`, nazwy sekcji.

Strategia: naprawa idzie od przyczyny do skutku (najpierw `handleChange`, potem geometria, potem kategorie i UI), a każda zmiana backendu jest projektowana tak, aby wynik dla `roof_drainage_type='vacuum'`, `column_method='default'`, `foundation_method='default'` i `cladding_orientation='horizontal'` pozostał **bit w bit identyczny**. To jest osią sprawdzania zachowania (preservation checking).

## Glossary

- **Bug_Condition (C)**: warunek uruchamiający defekt — wejście (parametry hali + interakcja UI), dla którego system produkuje wynik niezgodny z Expected Behavior. Rozbity na siedem rozłącznych podwarunków C1–C7 (patrz Bug Details).
- **Property (P)**: pożądane zachowanie dla wejść spełniających C — wartość tekstowa dociera do backendu jako `str`, poszycie dachu leży na górnym pasie dźwigara, ściana kończy się na okapie, kategoria słupa odpowiada jego położeniu w siatce, stan React aktualizuje się niemutowalnie.
- **Preservation**: zachowanie niezmienione — cała ścieżka `vacuum` + `default` + `horizontal`, ŚOP, stężenia, doki, biura, antresole, rezerwy, kontrakt `Component3D`.
- **`handleChange`**: wspólny handler zmian pól w `frontend/src/components/Controls.jsx`, podłączony do suwaków, checkboxów i selectów sekcji 1–5.
- **`RoofFactory`**: `backend/generators/roof_factory.py` — dźwigary, płatwie i poszycie; ETAP 3 generuje dwie połacie dla `gravity`.
- **`GridSystem3D`**: `backend/core/grid_system.py` — jedyne źródło pozycji osi, slotów i rzędnych (wymóg 3.7).
- **`get_parapet_height()`**: obecna metoda `GridSystem3D` zwracająca „najwyższy punkt obudowy”; używana przez `CladdingFactory`, `SecondaryStructureFactory` i `FireWallFactory` w trzech różnych znaczeniach — źródło defektu 1.3.
- **Okap (eave)**: `clear_height + truss_depth` — rzędna oparcia dźwigara na słupie skrajnym.
- **Kalenica (ridge)**: dla `gravity` `okap + half_width · tan(roof_angle)`.
- **Kategoria słupa/stopy**: klucz w `manual_column_sections` / `manual_sizes` i w `DEFAULTS`; po naprawie: `external_main`, `external_corner`, `external_intermediate_cladding`, `internal_main`.
- **Slot**: podział przęsła na pola o szerokości ≈4 m (`GridSystem3D.slots_per_bay`), jednostka adresowania doków (`"left-3-1"`).
- **Płyta modularna**: pionowa płyta warstwowa o szerokości `modularWidth` z `RUUKKI_CATALOG` (1100 mm dla wszystkich pozycji katalogu).
- **Rygiel montażowy (`cladding_rail`)**: poziomy profil stalowy stanowiący podkonstrukcję mocowania płyt pionowych.

## Bug Details

### Bug Condition

Defekt manifestuje się w siedmiu rozłącznych sytuacjach. Wspólny mianownik C1 (konwersja numeryczna pól tekstowych) maskuje C2 i C3 — dopóki `roof_drainage_type='gravity'` nie dociera do backendu, błędy geometrii dachu dwuspadowego są nieobserwowalne z UI.

**Formal Specification:**

```
FUNCTION isBugCondition(input)
  INPUT: input = (uiEvent, params, interaction)
  OUTPUT: boolean

  // C1 — konwersja numeryczna pola tekstowego (przyczyna główna, punkty [3] i [7])
  C1 := uiEvent.handler = handleChange
        AND uiEvent.target.type IN ['select-one', 'text']
        AND NOT isNumeric(uiEvent.target.value)

  // C2 — odbite połacie dachu grawitacyjnego
  C2 := params.roof_drainage_type = 'gravity'
        AND EXISTS panel IN roofPanels(params):
              sign(slope(panel)) <> sign(slope(trussTopChord(params, panel.side)))

  // C3 — attyka zabudowująca dach dwuspadowy
  C3 := params.roof_drainage_type = 'gravity'
        AND wallTopHeight(params) > eaveHeight(params) + tolerance

  // C4 — martwe kategorie gabarytów ręcznych
  C4 := (params.column_method = 'manual' OR params.foundation_method = 'manual')
        AND EXISTS category IN keys(params.manual_sizes) ∪ keys(params.manual_column_sections):
              category NOT IN categoriesReadByFactories()

  // C5 — brak rozpoznania słupów narożnych i pośrednich pod obudowę
  C5 := EXISTS node IN grid.nodes:
              isCorner(node) AND categoryOf(node) <> 'external_corner'

  // C6 — mutowalna aktualizacja stanu ręcznych gabarytów
  C6 := interaction = editManualSize
        AND stateUpdate mutates params.manual_sizes[category]
            OR stateUpdate mutates params.manual_column_sections[category]

  // C7 — brak kontrolek: pole numeryczne, zakresy, selektor doków, orientacja obudowy
  C7 := interaction IN ['typeExactDimension', 'setWidthAbove60', 'setLengthAbove120',
                        'setAislesAbove4', 'pickOpeningTypeFromList', 'shiftRangeSelect',
                        'setVerticalCladding']
        AND NOT uiSupports(interaction)

  RETURN C1 OR C2 OR C3 OR C4 OR C5 OR C6 OR C7
END FUNCTION
```

### Examples

- **C1** — użytkownik wybiera „Grawitacyjne (Dwuspadowy)”: stan otrzymuje `roof_drainage_type: NaN`, ciało żądania zawiera `"roof_drainage_type": null`, backend odpowiada `422 Input should be a valid string`, `api.js` loguje błąd i zwraca `{ components: [] }`, scena pustoszeje. Oczekiwane: `"roof_drainage_type": "gravity"`, model 3441 komponentów dla 30×60 m.
- **C1** — analogicznie „Ręczne przekroje [X, Z]” → `column_method: NaN` → 422 → model znika. Oczekiwane: `"manual"` i przekroje wpisane w formularzu (0.7/0.8/0.9 zamiast 0.4/0.3).
- **C2** — 30 m, kąt 10°: górny pas dźwigara ma kalenicę 11.44 m i okap 8.80 m; poszycie ma okap 11.58 m i kalenicę 8.88 m (litera V). Panele przecinają kratownicę. Oczekiwane: poszycie z kalenicą ≈11.44 m i okapem ≈8.80 m, oparte na górnym pasie.
- **C3** — 30 m, kąt 10°, `truss_depth=0.8`: `get_parapet_height()` = 8.80 + 2.64 + 0.20 = 11.64 m, `CladdingFactory` stawia ściany wzdłużne o tej wysokości na całej długości hali. Oczekiwane: ściany wzdłużne do 8.80 m, szczyty zamknięte schodkowo do linii połaci.
- **C4** — formularz pokazuje `external dock` i `internal dock`; wpisanie 5.0 × 5.0 nie zmienia ani jednego komponentu w odpowiedzi backendu.
- **C5** — hala 1-nawowa 30×60: 4 węzły narożne (przecięcie osi skrajnej X z osią skrajną Z) otrzymują `external_main` zamiast `external_corner`.
- **C6** — wpisanie 0.75 w polu `external_main[0]`: `newParams.manual_column_sections['external_main'][0] = 0.75` mutuje tablicę współdzieloną z poprzednim stanem; React nie widzi zmiany referencji obiektu zagnieżdżonego, a `prev` jest już zanieczyszczony.
- **C7 (przypadek brzegowy)** — użytkownik chce hali 150 × 300 m z 8 nawami: suwaki zatrzymują się na 60/120/4, brak pola do wpisania wartości.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**

- Ścieżka `roof_drainage_type='vacuum'`: koperty ze spadkami, `drainage_inlet`, słupki dystansowe, `roof_slope_percent`, `drainage_zones_x/z` — identyczna lista komponentów (3.1).
- Ścieżka `column_method='default'` i `foundation_method='default'`: przekroje 0.4×0.4 i 0.3×0.3, stopy 2.0×2.0, 1.5×1.5, 1.2×1.2 — identyczne wartości po wprowadzeniu nowych kategorii (3.2).
- Suwaki pól liczbowych: przesunięcie aktualizuje parametr, model przelicza się po „Buduj Model 3D” (3.3).
- Kliknięcie pojedynczego slotu bez Shift zmienia wyłącznie ten slot; „Max Doki L/R” i „Czyść L/R” działają na całą stronę hali (3.4).
- `cladding_orientation='horizontal'`: obudowa generowana jak dotychczas, w tym wycięcia otworów i zamknięcia szczytów (3.5).
- `dock_foundation_depth` stosowane dla słupów i stóp w przęsłach z dokiem (3.6).
- `GridSystem3D` jako jedyne źródło osi, slotów i rzędnych; zatrzask długości hali do wielokrotności rozstawu ram (3.7).
- Kontrakt `Component3D` (`type`, `position`, `rotation`, `scale`, `meta`); mapowanie typów na materiały, kategorie widoczności i podświetlenie PPOŻ w `Scene3D` (3.8).
- Sekcje 6–10 panelu (PPOŻ, pomieszczenia techniczne, biura zewnętrzne, antresole, rezerwa) — bez zmian (3.9).
- `hall_type='complex'`: bloki z transformacją offsetu i rotacji (3.10).
- `/validate-hall`: format listy kolizji i sposób ich prezentacji w panelu (3.11).

**Scope:**

Wszystkie wejścia, które nie spełniają C1–C7, muszą pozostać nietknięte. W szczególności:

- żądania z `roof_drainage_type='vacuum'` — cała geometria dachu, attyki, rygli i ŚOP,
- żądania z metodami `default` — geometria słupów i fundamentów,
- żądania z `cladding_orientation='horizontal'` — geometria obudowy,
- pola liczbowe obsługiwane przez `handleChange` (suwaki `range`, pola `number`) — konwersja do `float` bez zmian,
- checkboxy (`has_cladding`, `has_sprinklers`) — `checked` bez zmian,
- handlery inline sekcji 6–10 (ŚOP, biura, antresole, rezerwy) — bez zmian, mają własną obsługę typów.

Rzeczywiste poprawne zachowanie dla wejść spełniających C jest zdefiniowane w sekcji Correctness Properties (Property 1).

## Hypothesized Root Cause

1. **Jedna reguła konwersji dla wszystkich typów pól** (`handleChange`) — `parseFloat` zastosowany do `select-one`:
   - handler rozgałęzia się tylko na `type === 'checkbox'`, wszystko inne traktuje jako liczbę,
   - `parseFloat('gravity')` = `NaN`, `JSON.stringify({ x: NaN })` = `{"x":null}` — cicha utrata informacji bez błędu w konsoli,
   - `api.js` zamienia 422 na `{ components: [] }`, więc objaw („model znika”) jest maksymalnie oddalony od przyczyny.

2. **Odbity znak rotacji połaci** (`RoofFactory` ETAP 3) — panel jest boksem rozciągniętym po lokalnej osi X i obracanym wokół Z. Dla lewej połaci (x od −W do 0) rzędna musi rosnąć wraz z x, czyli nachylenie musi być dodatnie (`+angle_rad`); kod używa `-angle_rad` dla lewej i `+angle_rad` dla prawej. Środki paneli i rzędna `roof_y` są policzone poprawnie, dlatego defekt jest czystym odbiciem wokół poziomej osi przechodzącej przez środek połaci.

3. **Przeciążone znaczenie `get_parapet_height()`** — jedna metoda obsługuje trzy różne pytania: „gdzie kończy się obudowa ściany wzdłużnej?” (`CladdingFactory`, `SecondaryStructureFactory`) i „jak wysoko musi wyjść ŚOP?” (`FireWallFactory`). Dla dachu płaskiego (`vacuum`) odpowiedź jest jedna, dla dwuspadowego — trzy różne. Dach dwuspadowy nie ma attyki: ściana wzdłużna kończy się na okapie, a ściana szczytowa idzie po linii połaci.

4. **Kategorie gabarytów jako luźne stringi** — `manual_sizes` i `manual_column_sections` to `Dict[str, List[float]]` bez walidacji kluczy. Klucze `external_dock`/`internal_dock` przetrwały w modelu i UI po refaktoryzacji, w której wpływ doków przeniesiono na głębokość posadowienia (`dock_foundation_depth`), a nie na gabaryt stopy. Nikt nie zauważył, bo formularz nie zgłasza nieodczytanych kluczy.

5. **Brak klasyfikacji topologicznej węzła** — `GridNode` wie, czy jest zewnętrzny (`is_external`), ale nie wie, czy jest narożny. Kategoria jest wybierana w każdej fabryce osobno (`sec_ext_main if node.is_external else sec_int_main`), więc logika kategoryzacji jest zduplikowana i niepełna.

6. **Płaskie kopiowanie stanu przy zagnieżdżonych strukturach** — `{ ...params }` kopiuje referencję do słownika kategorii i do tablic wartości; przypisanie `[type][i] = ...` modyfikuje obiekt, który jest jednocześnie poprzednim stanem.

## Correctness Properties

Property 1: Bug Condition — Poprawne przekazanie typów pól i geometria zgodna z konstrukcją

_For any_ wejście spełniające warunek błędu (`isBugCondition` zwraca `true`), naprawiony system SHALL:
(a) przekazać wartość pola nieliczbowego do backendu jako łańcuch znaków identyczny z wartością wybraną w kontrolce, bez konwersji numerycznej, i otrzymać odpowiedź 200 z niepustą listą komponentów;
(b) dla `roof_drainage_type='gravity'` wygenerować poszycie dachowe o nachyleniu zgodnym ze znakiem nachylenia górnego pasa dźwigara po tej samej stronie hali, z kalenicą w osi hali i okapami na rzędnej `clear_height + truss_depth`;
(c) zakończyć obudowę ścian wzdłużnych na rzędnej okapu i zamknąć ściany szczytowe do linii połaci;
(d) przypisać każdemu węzłowi siatki kategorię wynikającą z jego położenia (`external_corner` dla przecięcia skrajnej osi X ze skrajną osią Z, `external_main` dla pozostałych węzłów osi skrajnych, `internal_main` dla węzłów wewnętrznych, `external_intermediate_cladding` dla słupów pod obudowę) i zastosować przekrój oraz stopę z tej kategorii;
(e) zaktualizować stan ręcznych gabarytów niemutowalnie — poprzedni obiekt stanu, jego słowniki i tablice pozostają nietknięte, a nowa wartość jest natychmiast widoczna w polu;
(f) udostępnić pola numeryczne obok suwaków geometrii głównej z zakresami do 180 m / 360 m / 12 naw, listę rodzaju otworu z zaznaczaniem zakresowym Shift oraz pionowy układ obudowy z płytami modularnymi i ryglami montażowymi.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11, 2.12**

Property 2: Preservation — Niezmienione zachowanie dla wejść poza warunkiem błędu

_For any_ wejście niespełniające warunku błędu (`isBugCondition` zwraca `false`), naprawiony system SHALL wyprodukować dokładnie ten sam wynik co system przed naprawą, zachowując: pełną geometrię dachu podciśnieniowego wraz z wpustami i słupkami dystansowymi, gabaryty domyślne słupów i stóp, geometrię obudowy poziomej z otworami i zamknięciami szczytów, wysokości i geometrię ŚOP dla obu typów dachu, głębokości posadowienia w strefach dokowych, kontrakt `Component3D`, działanie suwaków oraz przycisków wypełniania i czyszczenia doków, a także pełną funkcjonalność sekcji 6–10 i trybu `complex`.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11**

## Fix Implementation

### Changes Required

Zakładając, że analiza przyczyn jest poprawna, poprawka obejmuje 9 plików: 5 w backendzie i 4 w froncie (w tym 2 nowe komponenty).

---

#### 1. `frontend/src/components/Controls.jsx` — `handleChange` (przyczyna główna, wymogi 2.1, 2.4)

Regułą rozstrzygającą jest **typ kontrolki DOM**, nie nazwa pola — nowe selecty tekstowe (np. `cladding_orientation`) będą działać bez modyfikacji handlera.

```jsx
// Selecty, których wartości są liczbami (obecnie pusty — furtka na przyszłość)
const NUMERIC_SELECT_FIELDS = new Set([]);
// Pola całkowitoliczbowe
const INTEGER_FIELDS = new Set(['number_of_aisles', 'drainage_zones_x', 'drainage_zones_z']);

const handleChange = (e) => {
  const { name, value, type, checked } = e.target;

  setParams(prev => {
    if (type === 'checkbox') return { ...prev, [name]: checked };

    const isNumericField =
      type === 'range' || type === 'number' || NUMERIC_SELECT_FIELDS.has(name);

    if (!isNumericField) return { ...prev, [name]: value };   // select-one, text → string

    const parsed = parseFloat(value);
    if (!Number.isFinite(parsed)) return prev;                // pusty input nie psuje stanu
    return { ...prev, [name]: INTEGER_FIELDS.has(name) ? Math.round(parsed) : parsed };
  });
};
```

Zmiany szczegółowe:
1. Rozgałęzienie na trzy przypadki (`checkbox` / numeryczne / tekstowe) zamiast dwóch.
2. Straż `Number.isFinite` — puste pole `number` nie wprowadza `NaN` do stanu (zwraca `prev`).
3. `Math.round` dla pól całkowitoliczbowych — `number_of_aisles` trafia do Pydantic jako `int`.
4. Zamiana `setParams(prev => ...)` — bez odczytu `params` z domknięcia.

#### 2. `backend/generators/roof_factory.py` — rotacja połaci (wymóg 2.2)

W ETAP 3, gałąź `gravity`:

```python
# Lewa połać: x ∈ [-ext, 0], rzędna rośnie w stronę kalenicy → nachylenie dodatnie
# Prawa połać: x ∈ [0, +ext], rzędna maleje w stronę okapu → nachylenie ujemne
roof_y = (params.clear_height + params.truss_depth
          + (ext_roof_half_width / 2) * math.tan(angle_rad)
          + (params.roof_panel_thickness / 2) / math.cos(angle_rad))

elements.append(Component3D(type="roof_panel", position=[-panel_x, roof_y, 0],
                            rotation=[0, 0, angle_rad],
                            scale=[chord_len_ext, params.roof_panel_thickness, grid.length]))
elements.append(Component3D(type="roof_panel", position=[panel_x, roof_y, 0],
                            rotation=[0, 0, -angle_rad],
                            scale=[chord_len_ext, params.roof_panel_thickness, grid.length]))
```

Zmiany szczegółowe:
1. Zamiana znaków rotacji: lewa `+angle_rad`, prawa `-angle_rad`.
2. Offset grubości `(t/2) / cos(angle)` zamiast `t/2` — spód płyty leży dokładnie na linii górnego pasa (przy 10° różnica 0.8 mm, przy 35° już 16 mm).
3. Bez zmian: `position`, `scale`, `chord_len_ext`, liczba i typ komponentów, cała gałąź `vacuum`.

#### 3. `backend/core/grid_system.py` — rozdzielenie rzędnych wysokościowych (wymóg 2.3)

```python
def get_eave_height(self) -> float:
    """Rzędna okapu — oparcie dźwigara na słupie skrajnym."""
    return self.params.clear_height + self.params.truss_depth

def get_max_roof_height(self) -> float:
    """Najwyższy punkt połaci: kalenica (gravity) lub szczyt koperty (vacuum)."""
    if self.params.roof_drainage_type == "gravity":
        return self.get_eave_height() + self.half_width * math.tan(math.radians(self.params.roof_angle))
    slope_factor = self.params.roof_slope_percent / 100.0
    max_drain_dist = (self.width / self.params.drainage_zones_x / 2
                      + self.length / self.params.drainage_zones_z / 2)
    return self.get_eave_height() + max_drain_dist * slope_factor

def get_wall_top_height(self) -> float:
    """Górna krawędź obudowy ściany WZDŁUŻNEJ."""
    if self.params.roof_drainage_type == "gravity":
        return self.get_eave_height()                       # dach dwuspadowy nie ma attyki
    return self.get_max_roof_height() + DEFAULTS.parapet_extension

def get_gable_wall_top_at(self, x: float) -> float:
    """Górna krawędź obudowy ściany SZCZYTOWEJ w danym X (linia połaci)."""
    if self.params.roof_drainage_type == "gravity":
        return self.get_roof_height_at(min(max(x, -self.half_width), self.half_width))
    return self.get_wall_top_height()
```

Zmiany szczegółowe:
1. `get_parapet_height()` usunięta — jej trzy znaczenia rozdzielone na trzy metody; wszystkie 6 wywołań w 3 plikach (`cladding_factory` ×1, `secondary_structure_factory` ×3, `fire_wall_factory` ×2) zostaje zmigrowane w tej samej zmianie.
2. `get_max_roof_height()` odtwarza dla `vacuum` dokładnie starą formułę (`max_roof_h`), więc `get_wall_top_height()` dla `vacuum` = stary `get_parapet_height()` — geometria attyki niezmieniona (3.5).
3. `GridNode` zyskuje pole `is_corner: bool`, a klasa metodę kategoryzującą:

```python
def is_corner_node(self, frame_idx: int, axis_idx: int) -> bool:
    return (axis_idx in (0, len(self.axes_x) - 1)
            and frame_idx in (0, self.num_frames - 1))

def get_column_category(self, node: GridNode) -> str:
    if node.is_corner:
        return "external_corner"
    if node.is_external:
        return "external_main"
    return "internal_main"

CLADDING_COLUMN_CATEGORY = "external_intermediate_cladding"
```

#### 4. `backend/generators/fire_wall_factory.py` — migracja wywołań (preservation 3.1, 3.9)

```python
if config.top_type == "parapet_above_roof":
    wall_top_y = grid.get_max_roof_height() + DEFAULTS.parapet_extension + 0.10
else:
    wall_top_y = grid.get_max_roof_height()
```

Obie formuły dają liczby identyczne ze starymi dla `vacuum` **i** dla `gravity` (stary `get_parapet_height()` = `max_roof + 0.20`), więc ŚOP nadal wychodzi ponad kalenicę — wymóg 2.3 nie dotyczy ścian oddzielenia pożarowego.

#### 5. `backend/generators/cladding_factory.py` — zakończenie ścian i pionowy układ (wymogi 2.3, 2.12)

Rozbicie na cztery funkcje pomocnicze:

1. `_build_longitudinal_wall(grid, params, side, bay_idx, slot_idx)` — wysokość `grid.get_wall_top_height()` zamiast `parapet_h`; logika otworów bez zmian dla `horizontal`.
2. `_build_gable_wall(grid, params, z_pos)`:
   - `vacuum` → jeden panel pełnej szerokości i wysokości `get_wall_top_height()` (dokładnie jak dziś, 3.5),
   - `gravity` → podział szerokości zewnętrznej na segmenty o szerokości `params.cladding_module_width` (reszta domykana węższym segmentem), wysokość segmentu = `grid.get_gable_wall_top_at(x_edge_bliższa_kalenicy)`, czyli schodkowe zamknięcie do linii połaci z minimalnym nadmiarem schowanym pod płytą dachową (brak szczelin).
3. `_build_vertical_field(x, z_start, z_end, y_bottom, y_top, t, module_w, opening)` — dekompozycja pola ściany na pasma i podział modularny:
   - najpierw podział wzdłuż Z na pasma: `[z_start, z_hole_start]`, `[z_hole_start, z_hole_end]`, `[z_hole_end, z_end]` — żadna płyta nie przechodzi przez krawędź otworu,
   - każde pasmo dzielone na `n = max(1, round(width / module_w))` płyt o równej szerokości `width / n` (joint pokrywa się z krawędzią pasma i slotu),
   - płyty w pasmie otworu generowane jako część nad nadprożem (i pod otworem, gdy `hole_y_start > 0`),
   - typ komponentu `sandwich_panel_v` (już obsłużony w `Scene3D` na liście płaszczyzn).
4. `_build_cladding_rails(grid, params, side)` — poziome rygle montażowe dla `vertical`:
   - rzędne od `params.plinth_top_level + rail_spacing` co `DEFAULTS.cladding_rail_spacing` (1.8 m) do `get_wall_top_height()`, plus rygiel krawędziowy na górze ściany,
   - rygiel na poziomie bez otworów w przęśle → jeden element na całe przęsło; przęsło z otworem → elementy per slot, pomijające sloty, w których rzędna mieści się w wysokości otworu,
   - typ `cladding_rail`, przekrój `DEFAULTS.cladding_rail_section` (0.10 m),
   - dla ścian szczytowych rzędne przycięte do `get_gable_wall_top_at(x)`.

Rozgałęzienie orientacji na wejściu `generate()`:

```python
if not params.has_cladding:
    return []
if params.cladding_orientation == "vertical":
    return CladdingFactory._generate_vertical(grid, params)
return CladdingFactory._generate_horizontal(grid, params)   # ścieżka zachowana 1:1
```

> Uwaga: obecny kod nie sprawdza `params.has_cladding`. Dodanie tego warunku jest zmianą zachowania dla `has_cladding=False` — zostaje **poza zakresem** poprawki; warunek dodajemy tylko wtedy, gdy testy preservation potwierdzą, że `has_cladding=False` już dziś nie generuje obudowy w innym miejscu łańcucha. Domyślnie zachowujemy obecne wejście bez tego `if`.

#### 6. `backend/generators/secondary_structure_factory.py` — rygle vs. orientacja (wymogi 2.3, 2.12)

1. `_generate_wall_girts` i `_generate_trimmers`: `grid.get_parapet_height()` → `grid.get_wall_top_height()` (dla `gravity` rygle kończą się na okapie, dla `vacuum` bez zmian).
2. `_generate_gable_girts`: poziom rygla przycinany do linii połaci — rygiel dzielony na odcinki tam, gdzie `get_gable_wall_top_at(x)` spada poniżej rzędnej rygla (dla `vacuum` jeden odcinek pełnej szerokości, jak dziś).
3. Gdy `params.cladding_orientation == 'vertical'`, pomijamy generowanie `girt` (rygle poziome `cladding_rail` z `CladdingFactory` pełnią tę funkcję i mają własny rozstaw); wymiany (`trimmer`) wokół otworów generowane bez zmian.

#### 7. `backend/models.py` i `backend/core/defaults.py` — kategorie i parametry obudowy (wymogi 2.5, 2.6, 2.12)

`models.py`:

```python
manual_sizes: Dict[str, List[float]] = {
    "external_main": [2.5, 4.0, 0.45],
    "external_corner": [2.5, 4.0, 0.45],
    "external_intermediate_cladding": [1.5, 1.5, 0.40],
    "internal_main": [2.5, 2.5, 0.45],
}

manual_column_sections: Dict[str, List[float]] = {
    "external_main": [0.4, 0.4],
    "external_corner": [0.4, 0.4],
    "external_intermediate_cladding": [0.3, 0.3],
    "internal_main": [0.4, 0.4],
}

cladding_orientation: str = "horizontal"        # "horizontal" | "vertical"
cladding_module_width: float = 1.1              # szerokość modularna płyty [m]
```

`defaults.py`:

```python
foundation_sizes = {
    "external_main": [2.0, 2.0, 0.5],
    "external_corner": [2.0, 2.0, 0.5],                 # = external_main → geometria domyślna bez zmian
    "external_intermediate_cladding": [1.2, 1.2, 0.5],  # = dawne intermediate_cladding
    "internal_main": [1.5, 1.5, 0.5],
}
column_sections = {
    "external_main": [0.4, 0.4],
    "external_corner": [0.4, 0.4],
    "external_intermediate_cladding": [0.3, 0.3],
    "internal_main": [0.4, 0.4],
}
cladding_rail_spacing: float = 1.8
cladding_rail_section: float = 0.10
LEGACY_CATEGORY_ALIASES = {
    "intermediate_cladding": "external_intermediate_cladding",
    "external_corner": "external_main",      # fallback dla żądań bez nowej kategorii
}
```

Wartości domyślne `external_corner` są celowo równe `external_main`, a `external_intermediate_cladding` równe dawnemu `intermediate_cladding` — dzięki temu wynik dla `column_method='default'` / `foundation_method='default'` jest identyczny z obecnym (3.2), a nowe kategorie mają znaczenie tylko w trybie `manual`.

Wspólne resolvery (jedno miejsce, trzy fabryki):

```python
def resolve_column_section(params, category: str) -> List[float]:
    """manual → manual_column_sections[category] z fallbackiem na alias i DEFAULTS."""

def resolve_foundation_size(params, category: str) -> List[float]:
    """manual → manual_sizes[category] z fallbackiem na alias i DEFAULTS."""
```

Kolejność szukania: klucz nowy → alias legacy → `DEFAULTS`. Dzięki temu żądanie ze starym kluczem `intermediate_cladding` (np. z nieodświeżonej karty przeglądarki) nadal działa; usunięte `external_dock` / `internal_dock` są ignorowane, bo Pydantic przyjmuje dowolne klucze w `Dict[str, List[float]]` — kontrakt API pozostaje wstecznie zgodny.

#### 8. `backend/generators/column_factory.py` i `foundation_factory.py` — kategoryzacja z siatki (wymóg 2.6)

```python
# ColumnFactory — słupy ram głównych
for frame_idx in range(grid.num_frames):
    for axis_idx in range(len(grid.axes_x)):
        node = grid.get_node(frame_idx, axis_idx)
        section = resolve_column_section(params, grid.get_column_category(node))
        ...

# słupy szczytowe i pośrednie pod obudowę
section = resolve_column_section(params, GridSystem3D.CLADDING_COLUMN_CATEGORY)
```

`FoundationFactory` — analogicznie z `resolve_foundation_size`. `PlinthFactory` przechodzi na `resolve_foundation_size(params, "external_main")` (ten sam wynik, jeden mechanizm).

Zmiany szczegółowe:
1. Wybór kategorii przenosi się do `GridSystem3D` — jedno źródło prawdy (3.7), koniec duplikacji `is_external ? ... : ...`.
2. Słupy narożne dostają własny przekrój i stopę; przy wartościach domyślnych są identyczne z `external_main`, więc `default` nie zmienia geometrii.
3. Słupy szczytowe (wiatrowe) i pośrednie wzdłużne używają wspólnej kategorii `external_intermediate_cladding` — obie grupy przenoszą wyłącznie obciążenie od obudowy i wiatru, a wymóg 2.5 wymienia dokładnie cztery kategorie. Decyzja jest świadoma i zapisana tu, bo poprzednia nazwa (`intermediate_cladding`) tego nie komunikowała.

#### 9. `frontend/src/components/NumberSlider.jsx` (nowy) — suwak + input (wymóg 2.8)

```jsx
const NumberSlider = ({ name, label, value, min, max, step, integer = false, onCommit }) => {
  const [draft, setDraft] = useState(String(value));
  const [focused, setFocused] = useState(false);

  // Synchronizacja suwak → input (tylko gdy input nie jest edytowany)
  useEffect(() => { if (!focused) setDraft(String(value)); }, [value, focused]);

  const clamp = (n) => {
    const c = Math.min(max, Math.max(min, n));
    return integer ? Math.round(c) : c;
  };

  const onDraftChange = (text) => {
    setDraft(text);
    const n = parseFloat(text);
    if (Number.isFinite(n) && n >= min && n <= max) onCommit(name, integer ? Math.round(n) : n);
  };

  const onCommitDraft = () => {                 // blur / Enter
    const n = parseFloat(draft);
    const next = Number.isFinite(n) ? clamp(n) : value;
    setDraft(String(next));
    if (next !== value) onCommit(name, next);
  };
  ...
};
```

Zasady:
1. Dwukierunkowa synchronizacja: suwak jest kontrolowany wartością z `params`; input trzyma `draft` (string), aby dało się wpisywać wartości pośrednie („1” w drodze do „150”).
2. Wpisywanie propaguje stan tylko dla wartości w zakresie — bez agresywnego clampowania w trakcie pisania.
3. Clamp i normalizacja na `blur` oraz `Enter`; niepoprawna treść wraca do ostatniej dobrej wartości.
4. `integer` dla `number_of_aisles`.
5. `onCommit(name, value)` woła to samo `setParams(prev => ...)` co `handleChange` — jedna ścieżka aktualizacji stanu.

#### 10. `frontend/src/components/DockGridSelector.jsx` (wydzielony z `Controls.jsx`) — typ otworu i zakres Shift (wymóg 2.10)

```jsx
const OPENING_TYPES = [
  { value: 'none', label: 'Brak (ściana pełna)' },
  { value: 'dock', label: 'Dok przeładunkowy' },
  { value: 'gate', label: 'Brama kurierska' },
];

const [openingType, setOpeningType] = useState('dock');
const [lastClickedIndex, setLastClickedIndex] = useState(null);  // { side, index } | null
```

Zasady:
1. Płaski indeks slotu: `index = bayIdx * slotsPerBay + slotIdx`; adres klucza (`side-bay-slot`) odtwarzany z indeksu — zaznaczanie zakresowe przechodzi przez granice przęseł.
2. Klik bez Shift: zapis `openingType` w klikniętym slocie i `setLastClickedIndex({ side, index })`.
3. Klik z Shift przy `lastClickedIndex` po **tej samej** stronie: zapis `openingType` we wszystkich slotach od `min` do `max` indeksu, następnie aktualizacja `lastClickedIndex` na bieżący. Shift bez zapamiętanego indeksu lub po innej stronie działa jak klik pojedynczy.
4. `openingType === 'none'` usuwa klucze z `docks_config` (utrzymanie obecnej konwencji „brak klucza = brak otworu”).
5. Reset `lastClickedIndex` w `useEffect` na zmianę `numBays`/`slotsPerBay` — indeks z poprzedniej siatki nie może wyznaczać zakresu.
6. Aktualizacja niemutowalna: `setParams(prev => ({ ...prev, docks_config: { ...prev.docks_config, ...patch } }))`.
7. „Max Doki L/R” i „Czyść L/R” bez zmian (3.4). Świadoma zmiana zachowania: klik pojedynczy nie cykluje już `none → dock → gate`, lecz stosuje rodzaj z listy — dokładnie tego wymaga 2.10, a 3.4 wymaga jedynie, aby dotyczył pojedynczego slotu.

#### 11. `frontend/src/components/Controls.jsx` — sekcje, kategorie, zakresy (wymogi 2.5, 2.7, 2.9, 2.11, 2.12)

1. Sekcja 1: pięć pól przez `NumberSlider` z zakresami `width` 10–180, `length` 10–360, `clear_height` 4–18, `number_of_aisles` 1–12 (integer), `bay_spacing` 4–12 (2.8, 2.9).
2. Nazwy sekcji: „4. Obudowa Ruukki” → „ŚCIANY ZEWNĘTRZNE”, „5. Konstrukcja i Fundamenty” → „KONSTRUKCJA” (2.11). Numeracja pozostałych sekcji nietknięta — renumeracja nie jest wymagana i zwiększałaby ryzyko regresji w 3.9.
3. Sekcja „ŚCIANY ZEWNĘTRZNE”: nowy select `cladding_orientation` (`horizontal` / `vertical`) plus informacja o szerokości modularnej wybranej płyty (2.12).
4. Formularz ręcznych gabarytów renderowany ze stałej listy kategorii, nie z `Object.keys(params.…)`:

```jsx
const COLUMN_CATEGORIES = [
  { key: 'external_main', label: 'Słupy główne zewnętrzne' },
  { key: 'external_corner', label: 'Słupy zewnętrzne narożne' },
  { key: 'external_intermediate_cladding', label: 'Słupy zewn. pośrednie (obudowa)' },
  { key: 'internal_main', label: 'Słupy wewnętrzne' },
];
```

5. Niemutowalna edycja gabarytów — nowa tablica, nowy słownik, nowy obiekt stanu (2.7):

```jsx
const updateManualValue = (field, category, index, raw) => {
  const parsed = parseFloat(raw);
  setParams(prev => {
    const current = prev[field]?.[category] ?? [];
    const nextArr = current.map((v, i) => (i === index ? (Number.isFinite(parsed) ? parsed : v) : v));
    return { ...prev, [field]: { ...prev[field], [category]: nextArr } };
  });
};
```

Pole trzyma własny `draft` (jak w `NumberSlider`), aby wpisywanie „0.” nie kasowało znaku — wartość propagowana po sparsowaniu, `NaN` nie nadpisuje stanu.

#### 12. `frontend/src/App.jsx` i `frontend/src/components/Scene3D.jsx`

1. `App.jsx`: stan początkowy z nowymi kategoriami (te same cztery klucze co w `models.py`), `cladding_orientation: 'horizontal'`, `cladding_module_width: 1.1`.
2. `handlePanelChange` ustawia również `cladding_module_width: RUUKKI_CATALOG[panelId].modularWidth / 1000` — szerokość modularna płyty pionowej pochodzi z katalogu, bez duplikowania katalogu w backendzie.
3. `Scene3D.getCategory`: nowa reguła `if (type.includes('cladding_rail')) return 'structure';` **przed** regułą `sandwich_panel`. Bez tego rygle wpadają do kategorii `other`, dla której nie istnieje klucz w `visibilities`, i nie renderują się w ogóle.
4. `Scene3D` materiały: `cladding_rail` w kolorze rygla (`#64748b`); `sandwich_panel_v` już jest na liście płaszczyzn i już trafia do kategorii `cladding` (podciąg `sandwich_panel`) — bez zmian.

### Kolejność wdrożenia

1. `handleChange` (odblokowuje obserwowalność C2/C3) → 2. `GridSystem3D` (rzędne + kategorie) → 3. `RoofFactory` → 4. `FireWallFactory` + `SecondaryStructureFactory` (migracja wywołań) → 5. `CladdingFactory` (okap i szczyty) → 6. kategorie w `models.py`/`defaults.py` + fabryki słupów i stóp → 7. `NumberSlider` i zakresy → 8. `DockGridSelector` → 9. obudowa pionowa (backend + UI) → 10. nazwy sekcji.

### Ryzyka

- Zakresy 180 × 360 m z rozstawem 4 m dają ~90 ram i wielokrotnie więcej komponentów niż dziś (3441 dla 30×60). Renderowanie w `Scene3D` odbywa się per `mesh` bez instancjonowania — możliwy spadek płynności. Poza zakresem tej poprawki; wymóg 2.9 mówi wyłącznie o zakresach kontrolek.
- Pominięcie `girt` przy `cladding_orientation='vertical'` zmienia listę komponentów dla tej ścieżki. Jest to ścieżka dziś martwa (żadna fabryka nie czytała `cladding_orientation`), więc nie narusza żadnego wymogu 3.x.

## Testing Strategy

### Validation Approach

Dwa etapy: najpierw testy eksploracyjne uruchamiane na **niepoprawionym** kodzie, aby zobaczyć kontrprzykłady i potwierdzić lub odrzucić hipotezy przyczyn; potem testy sprawdzające naprawę (fix checking) i testy zachowania (preservation checking) porównujące wynik z zapisanym snapshotem sprzed naprawy.

Infrastruktura testowa nie istnieje w repozytorium i wymaga ustawienia:
- backend: `pytest` + `hypothesis` (dopisane do `backend/requirements.txt`), katalog `backend/tests/`,
- frontend: `vitest` + `@testing-library/react` + `jsdom` + `fast-check` (devDependencies), skrypt `npm run test -- --run` (tryb jednorazowy, bez watch).

Snapshoty preservation generujemy **przed** pierwszą zmianą backendu: dla zestawu parametrów referencyjnych (`vacuum`/`default`/`horizontal`, kilka rozmiarów, warianty z dokami i ŚOP) zapisujemy posortowaną listę komponentów jako JSON do `backend/tests/snapshots/`.

### Exploratory Bug Condition Checking

**Goal**: Wydobyć kontrprzykłady demonstrujące błąd na kodzie **przed** naprawą i potwierdzić lub odrzucić analizę przyczyn. Odrzucenie hipotezy oznacza powrót do sekcji Hypothesized Root Cause.

**Test Plan**: Backend testowany bezpośrednio przez `HallGenerator.generate_all_components()` (bez HTTP) oraz przez `TestClient` FastAPI dla ścieżki 422. Front testowany przez render `Controls` i symulację `change` na selektach z odczytem obiektu przekazanego do `setParams`.

**Test Cases**:
1. **Select tekstowy przez `handleChange`** — `fireEvent.change(select[name=roof_drainage_type], { target: { value: 'gravity' } })`, asercja `params.roof_drainage_type === 'gravity'` (na niepoprawionym kodzie da `NaN`).
2. **Kontrakt żądania** — `JSON.stringify(paramsAfterChange)` nie zawiera `"roof_drainage_type":null` (na niepoprawionym kodzie zawiera).
3. **422 z backendu** — `POST /generate-hall` z `roof_drainage_type: None` zwraca 422 i `Input should be a valid string` (potwierdzenie łańcucha przyczynowego).
4. **Nachylenie połaci vs. dźwigar** — dla `gravity`, 30×60, 10°: dla każdej połaci porównanie znaku `sin(rotation_z)` ze znakiem nachylenia górnego pasa po tej samej stronie; dodatkowo rzędne skrajne panelu (okap/kalenica) względem `get_roof_height_at(±half_width)` i `get_roof_height_at(0)` (na niepoprawionym kodzie znaki przeciwne, kalenica niżej od okapu).
5. **Wysokość obudowy ściany wzdłużnej** — dla `gravity` max `position.y + scale.y/2` po `sandwich_panel` ścian wzdłużnych ≤ okap + tolerancja (na niepoprawionym kodzie przekroczenie o `half_width·tan(angle) + 0.20`, czyli ~2.84 m dla 30 m/10°).
6. **Martwe kategorie** — generacja dla `foundation_method='manual'` z `manual_sizes['external_dock'] = [9, 9, 9]` daje listę komponentów identyczną jak dla `[2.7, 3.5, 0.45]` (na niepoprawionym kodzie: identyczną — potwierdzenie, że pole jest martwe).
7. **Kategoria narożna** — dla 30×60 istnieją 4 węzły narożne; test sprawdza, że ich stopy różnią się od stóp pozostałych węzłów osi skrajnych, gdy `manual_sizes['external_corner']` ma odmienne wartości (na niepoprawionym kodzie brak takiej kategorii).
8. **Mutacja stanu (przypadek brzegowy)** — edycja `manual_column_sections.external_main[0]`: asercja, że obiekt `prevParams` przechwycony przed edycją nie zmienił wartości (na niepoprawionym kodzie zmienił — dowód mutacji w miejscu).

**Expected Counterexamples**:
- `params.roof_drainage_type === NaN` po wyborze „Grawitacyjne”; ciało żądania z `null`; odpowiedź 422; pusta lista komponentów.
- Połać lewa z `rotation_z = -angle` przy dźwigarze o nachyleniu `+angle`; kalenica poszycia 8.88 m przy kalenicy dźwigara 11.44 m.
- Ściana wzdłużna o wysokości 11.64 m przy okapie 8.80 m.
- Możliwe przyczyny: jedna reguła konwersji dla wszystkich typów pól; odbity znak rotacji połaci; przeciążone znaczenie `get_parapet_height()`; brak klasyfikacji narożnika w `GridNode`; płaskie kopiowanie zagnieżdżonego stanu.

### Fix Checking

**Goal**: Dla wszystkich wejść spełniających warunek błędu naprawiony system produkuje zachowanie z Property 1.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := fixedSystem(input)
  ASSERT expectedBehavior(result)
END FOR
```

Konkretyzacja per podwarunek:

```
// C1
FOR ALL field WHERE field.type IN ['select-one', 'text'] DO
  ASSERT typeof handleChange(field, value).params[field.name] = 'string'
  ASSERT handleChange(field, value).params[field.name] = value
END FOR

// C2, C3
FOR ALL (width, angle, clear_height, truss_depth) WHERE drainage = 'gravity' DO
  panels := roofPanels(generate(params))
  ASSERT sign(slope(panels.left)) = +1 AND sign(slope(panels.right)) = -1
  ASSERT abs(ridgeY(panels) - grid.get_roof_height_at(0)) <= t/(2·cos) + eps
  ASSERT maxWallTopY(longitudinalPanels(generate(params))) <= grid.get_eave_height() + eps
  ASSERT minGableTopY covers roofline: FOR ALL x: gableTopY(x) >= grid.get_roof_height_at(x) - eps
END FOR

// C4, C5
FOR ALL node IN grid.nodes DO
  ASSERT categoryOf(node) = expectedCategory(node.axis_index, node.frame_index)
END FOR
FOR ALL category IN keys(manual_sizes) DO
  ASSERT category IN categoriesReadByFactories()
END FOR

// C6
FOR ALL (category, index, value) DO
  before := deepFreeze(params)
  after  := updateManualValue('manual_column_sections', category, index, value)
  ASSERT before unchanged AND after[category][index] = value
  ASSERT after[category] !== before[category]        // nowa referencja
END FOR

// C7
FOR ALL (min, max, typed) DO
  ASSERT commit(typed) = clamp(typed, min, max)
  ASSERT sliderValue = inputValue                    // dwukierunkowa synchronizacja
END FOR
FOR ALL (i, j) IN slotIndices × slotIndices DO
  ASSERT shiftClick(i, j) sets exactly slots [min(i,j) .. max(i,j)] to openingType
END FOR
```

### Preservation Checking

**Goal**: Dla wszystkich wejść niespełniających warunku błędu naprawiony system produkuje ten sam wynik co system pierwotny.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT originalSystem(input) = fixedSystem(input)
END FOR
```

**Testing Approach**: Testy własnościowe (property-based) są tu właściwym narzędziem, bo:
- generują wiele przypadków automatycznie w całej domenie parametrów (szerokość, długość, wysokość, kąt, rozstaw, strefy odwodnienia, konfiguracje doków),
- wychwytują przypadki brzegowe, których testy przykładowe nie obejmą (kąt 2° i 35°, rozstaw dokładnie 8.0 m przełączający słupy pośrednie, `bay_spacing` niedzielące długości, hala 1- i 4-nawowa),
- dają mocną gwarancję, że dla ścieżki `vacuum` / `default` / `horizontal` nie zmieniło się nic.

**Test Plan**: Snapshot listy komponentów zdjęty z **niepoprawionego** kodu dla zestawu parametrów referencyjnych; po naprawie ta sama lista (posortowana po `type, position, scale`) musi być identyczna z dokładnością do 1e-9. Uzupełniająco Hypothesis generuje losowe `HallParameters` z ograniczeniem `NOT isBugCondition` i porównuje wynik z wersją pierwotną wywołaną z zapisanego modułu referencyjnego (kopia sprzed naprawy w `backend/tests/reference/`).

**Test Cases**:
1. **Dach podciśnieniowy** — obserwacja na niepoprawionym kodzie liczby i pozycji `roof_panel`, `drainage_inlet`, `purlin_strut` dla `vacuum`; po naprawie identyczne (3.1).
2. **Gabaryty domyślne** — obserwacja przekrojów słupów i stóp dla `default`; po wprowadzeniu `external_corner` i `external_intermediate_cladding` identyczne (3.2).
3. **Obudowa pozioma** — obserwacja `sandwich_panel` dla `horizontal` + `vacuum` z dokami i bramami; po naprawie identyczne, w tym otwory i zamknięcia szczytów (3.5).
4. **Ściany oddzielenia pożarowego** — obserwacja `wall_top_y` dla obu `top_type` i obu typów dachu przed migracją `get_parapet_height()`; po migracji identyczne (3.9).
5. **Strefy dokowe** — obserwacja głębokości słupów i stóp w przęsłach z dokiem; po naprawie identyczne (3.6).
6. **Tryb complex** — obserwacja transformacji offsetu i rotacji dla dwóch bloków; po naprawie identyczne (3.10).
7. **Kontrakt odpowiedzi** — każdy komponent ma `type: str`, `position/rotation/scale` o długości 3, `meta` jako `dict[str, str] | None` (3.8).
8. **Suwaki i przyciski doków** — przesunięcie suwaka aktualizuje parametr; „Max Doki L/R” wypełnia całą stronę wartością `dock`, „Czyść L/R” usuwa klucze tej strony (3.3, 3.4).

### Unit Tests

- `handleChange`: trzy klasy pól (`checkbox`, `range`/`number`, `select-one`/`text`), puste pole `number`, pole całkowitoliczbowe `number_of_aisles`.
- `GridSystem3D`: `get_eave_height`, `get_max_roof_height`, `get_wall_top_height`, `get_gable_wall_top_at` dla `gravity` i `vacuum`; `is_corner_node` dla 1, 2 i 4 naw; `get_column_category` dla wszystkich klas węzłów.
- `RoofFactory`: znaki rotacji i rzędne skrajne połaci; brak zmian w gałęzi `vacuum`.
- `CladdingFactory`: wysokość ścian wzdłużnych, schodkowe zamknięcie szczytu, podział modularny pola z otworem i bez, rzędne rygli `cladding_rail`.
- Resolvery kategorii: klucz nowy, alias legacy, brak klucza (fallback na `DEFAULTS`), tryb `default` ignorujący `manual_*`.
- `NumberSlider`: wpisanie wartości w zakresie, poniżej `min`, powyżej `max`, tekstu niebędącego liczbą, wartości pośredniej podczas pisania; synchronizacja po zmianie z suwaka.
- `DockGridSelector`: klik pojedynczy dla każdego rodzaju otworu, Shift bez zapamiętanego indeksu, Shift w odwrotnym kierunku, Shift przez granicę przęseł, Shift po zmianie strony, reset po zmianie liczby przęseł.
- `updateManualValue`: niemutowalność (nowa tablica, nowy słownik, nowy obiekt), odrzucenie `NaN`.

### Property-Based Tests

- **Property 1 (fix)**: dla losowych `(width ∈ [10,180], length ∈ [10,360], clear_height, roof_angle ∈ [2,35], bay_spacing, aisles ∈ [1,12])` przy `gravity`: nachylenie każdej połaci ma znak zgodny z dźwigarem, kalenica poszycia zgadza się z `get_roof_height_at(0)`, żaden `sandwich_panel` ściany wzdłużnej nie wychodzi powyżej okapu, a suma wysokości zamknięcia szczytu pokrywa linię połaci bez szczelin.
- **Property 1 (kategorie)**: dla losowych siatek każdy węzeł ma kategorię wynikającą z jego indeksów; liczba węzłów `external_corner` = 4 dla `hall_type='simple'`.
- **Property 1 (obudowa pionowa)**: dla losowych `module_width ∈ [0.6, 1.5]` i losowych `docks_config` suma szerokości płyt `sandwich_panel_v` w każdym polu ściany równa się szerokości pola pomniejszonej o otwory, a szerokość każdej płyty ≤ `module_width` i > 0.
- **Property 1 (kontrolki)**: dla losowych `(min, max, typed)` `commit(typed) = clamp(typed, min, max)`; dla losowych par indeksów zaznaczanie Shift daje dokładnie zbiór `[min..max]`.
- **Property 2 (preservation)**: dla losowych `HallParameters` z `roof_drainage_type='vacuum'`, `column_method='default'`, `foundation_method='default'`, `cladding_orientation='horizontal'` — lista komponentów naprawionego generatora jest identyczna z listą generatora referencyjnego.
- **Property 2 (idempotencja stanu)**: dla losowych ciągów edycji ręcznych gabarytów każdy krok tworzy nowe referencje i nie modyfikuje żadnego wcześniejszego snapshotu stanu (deep-freeze).

### Integration Tests

- Pełna ścieżka `POST /generate-hall` z `roof_drainage_type='gravity'`, `column_method='manual'`, `foundation_method='manual'`: 200, niepusta lista, przekroje i stopy zgodne z wpisanymi wartościami, poszycie i obudowa spójne z dźwigarami.
- Pełna ścieżka z `cladding_orientation='vertical'`: obecność `sandwich_panel_v` i `cladding_rail`, brak `girt` na ścianach, otwory doków i bram zachowane, `Scene3D` renderuje oba typy (kategoria `structure`/`cladding`, nie `other`).
- Przełączanie `gravity` ↔ `vacuum` ↔ `gravity` w UI: model odbudowuje się za każdym razem, brak 422, `validation.clashes` w niezmienionym formacie.
- Hala 150 × 300 m, 8 naw, wartości wpisane z klawiatury: żądanie przechodzi, długość zatrzaśnięta do wielokrotności rozstawu ram, panel prezentuje ostrzeżenia walidacji.
- Konfiguracja doków: wybór „Brama kurierska”, klik slotu 2, Shift+klik slotu 9 → 8 bram w `docks_config`, po generacji odpowiadające otwory w obudowie i wymiany wokół nich.
- Tryb `complex` z dwoma blokami (`gravity` + `vacuum`, offset i rotacja 90°): geometria bez zmian względem stanu sprzed naprawy poza korektą dachu dwuspadowego bloku `gravity`.
