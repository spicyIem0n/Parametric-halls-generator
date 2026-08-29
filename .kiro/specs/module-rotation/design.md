# Projekt techniczny — Obrót modułów hali

## Przegląd

Rozwiązanie wprowadza transformację "lokalny układ modułu → globalny układ sceny". Każdy moduł jest generowany przez istniejące fabryki w swoim lokalnym układzie (środek w 0,0, ramy wzdłuż lokalnej osi X) — bez żadnych zmian w generatorach. Następnie `HallGenerator` stosuje do wszystkich komponentów modułu jednolitą transformację: rotację wokół osi Y o kąt `frame_orientation` oraz translację do `(position_x, position_z)`.

Kluczowa zasada wynikająca z analizy renderera: Three.js renderuje każdy komponent jako jednostkowy `boxGeometry([1,1,1])` z zastosowaniem `scale`, potem `rotation`, potem `position`. Dlatego poprawny obrót elementu polega na:
- przeliczeniu jego **pozycji** przez macierz rotacji wokół Y,
- dodaniu kąta do jego **rotation.y**,
- pozostawieniu **scale bez zmian**.

Ten trzeci punkt jest sednem naprawy — poprzednia wersja zamieniała scale.x ↔ scale.z, co spłaszczało panele i płatwie. Przy poprawnym podejściu bryła obraca się jako całość i zachowuje wymiary własne.

## Architektura

```
Controls.jsx (frame_orientation per blok)
        │  params.blocks[i].frame_orientation ∈ {0, 90}
        ▼
API  /generate-hall
        ▼
HallGenerator._generate_complex()
        │  dla każdego bloku:
        │   1. _block_to_params(block)  → HallParameters z ORYGINALNYMI width/length
        │   2. fabryki generują komponenty w układzie LOKALNYM (środek 0,0)
        │   3. _transform_components(offset=(px,0,pz), rotation_y=frame_orientation)
        │        - obrót pozycji wokół Y
        │        - rotation.y += kąt
        │        - scale BEZ ZMIAN
        ▼
_process_connections()  (operuje na obrysach po obrocie)
        ▼
lista Component3D → frontend → Scene3D (mesh position/rotation/scale)
```

## Komponenty i interfejsy

### Backend

#### 1. `_block_to_params(block)` — usunięcie zamiany wymiarów

Obecnie funkcja zamienia `w, l = l, w` przy `frame_orientation == 90`. Ta zamiana zostaje **usunięta**. Moduł jest generowany z oryginalnymi wymiarami użytkownika (width = rozpiętość ram lokalnie wzdłuż X, length = powtarzalność wzdłuż Z). Obrót przejmuje w całości `_transform_components`.

#### 2. `_transform_components(components, offset, rotation_y, block_id)` — poprawiona transformacja

Sygnatura bez zmian. Zmiana logiki wewnętrznej:

```python
# Rotacja pozycji wokół osi Y:
cos_a = cos(radians(rotation_y))
sin_a = sin(radians(rotation_y))
new_x = px * cos_a - pz * sin_a + offset_x
new_z = px * sin_a + pz * cos_a + offset_z
new_y = py + offset_y

# KLUCZOWE: rotacja elementu to ZŁOŻENIE MACIERZY, nie dodanie kątów Eulera.
# Element ma własną rotację Eulera (rx, ry, rz) — np. krzyżulec ma nachylenie
# w rx lub rz. Naiwne "ry += kąt" daje błędny wynik, bo rotacje 3D nie są
# przemienne. Trzeba policzyć R_final = R_y(kąt) · R_element i rozłożyć
# wynik z powrotem na kąty Eulera XYZ (kolejność zgodna z Three.js).
R_module = rotation_matrix_y(radians(rotation_y))
R_elem = euler_xyz_to_matrix(rx, ry, rz)
R_final = R_module @ R_elem
new_rx, new_ry, new_rz = matrix_to_euler_xyz(R_final)
# SCALE bez zmian.
```

Wymaga to dodania trzech funkcji pomocniczych do modułu (poza klasą `HallGenerator`):
- `rotation_matrix_y(a)` — macierz 3x3 rotacji wokół osi Y.
- `euler_xyz_to_matrix(rx, ry, rz)` — składa macierz z kątów Eulera w konwencji spójnej z Three.js (dla Euler 'XYZ' macierz = Rx · Ry · Rz).
- `matrix_to_euler_xyz(R)` — rozkłada macierz na `(rx, ry, rz)` w konwencji XYZ.

Warunek szybkiego wyjścia (brak transformacji) pozostaje dla `rotation_y == 0 and offset == [0,0,0]`, gwarantując brak regresji dla modułów nieobróconych (Wymaganie 5.2).

#### 3. `_module_bounds(block)` — helper obrysu w układzie globalnym

Nowa funkcja pomocnicza (lub inline) obliczająca prostokątny obrys modułu po obrocie, używana przez `_process_connections` i zwracana też do walidacji. Dla kątów 0/90 obrys to prostokąt o wymiarach:
- orientation 0: width (X) × length (Z)
- orientation 90: length (X) × width (Z)

Środek zawsze w (position_x, position_z). Zapis ogólny (dla przyszłych kątów) używa obróconego AABB, ale w tej iteracji wystarczy rozróżnienie 0/90.

#### 4. `_process_connections()` — bez zmian koncepcyjnych

Funkcja już teraz liczy `block_bounds` z zamianą w/l przy orient=90 — ta logika pozostaje poprawna, bo opisuje **obrys po obrocie** (co się zgadza z nowym podejściem). Wykrywanie styków, usuwanie ścian i przycinanie attyk operują na tych obrysach i nie wymagają zmian.

### Frontend

#### 5. `Scene3D.jsx` — bez zmian

Renderer już poprawnie stosuje `position/rotation/scale`. Ponieważ backend nie zamienia scale i przekazuje rotation.y w radianach, obrócone elementy wyświetlą się prawidłowo. Zero zmian.

#### 6. `ModuleLayoutEditor.jsx` — `getEffectiveDims` pozostaje

Funkcja `getEffectiveDims` (zamiana w↔l przy orient=90) opisuje obrys po obrocie na rzucie 2D — zgodna z nowym modelem. Rysowanie prostokąta, znaczników ram i wykrywanie styków pozostają bez zmian merytorycznych. Weryfikujemy jedynie spójność kierunku linii ram (orient=0 linie wzdłuż X = poziome; orient=90 linie wzdłuż Z = pionowe).

## Modele danych

`BlockDefinition.frame_orientation: int` — już istnieje (0 lub 90). Typ pozostaje `int`, dopuszczając w przyszłości inne wartości kątowe. Brak zmian w modelu.

`Component3D` — kontrakt bez zmian: `position[3]`, `rotation[3]` (radiany), `scale[3]`, `meta`.

## Obsługa błędów

- Kąt spoza {0, 90} w tej iteracji: backend przyjmie dowolny int i obróci poprawnie (mechanizm ogólny); UI ogranicza wybór do 0/90, więc inne wartości mogą pojawić się tylko z ręcznie edytowanego pliku projektu — akceptowane, bez błędu.
- Moduł bez `position_x/position_z` (starszy projekt): fallback do `position_offset` zachowany.
- Prostopadłe ramy + połączenie „none": walidacja w UI blokuje wybór (Wymaganie 4.4) — bez zmian.

## Strategia testów

Testy API (PowerShell/REST) po wdrożeniu:

1. **Test obrotu ram (Wymaganie 1, 6.1):** dwa moduły 24×48, orient 0 i 90. Zebrać unikalne pozycje X i Z słupów każdego modułu. Oczekiwane: moduł 0 ma rozpiętość (mała liczba osi) wzdłuż X i wiele osi wzdłuż Z; moduł 90 odwrotnie.
2. **Test kompletności geometrii (Wymaganie 2.4, 6.2):** obrócony moduł ma niezerowe i porównywalne liczby: słupy, sandwich_panel, purlin, roof_panel względem modułu nieobróconego.
3. **Test braku deformacji (Wymaganie 2.1, 2.5):** sprawdzić, że panele obudowy obróconego modułu mają ten sam rozkład wartości scale co moduł nieobrócony (te same wymiary własne, tylko inna rotacja.y).
4. **Test regresji orient=0 (Wymaganie 5.2):** moduł orient=0 generuje identyczny wynik jak przed zmianą.
5. **Test styków (Wymaganie 4):** dwa moduły stykające się, jeden obrócony, dylatacja — ściany na styku usunięte, attyka zachowana przy różnicy wysokości.
6. **Test kompatybilności (Wymaganie 5.3):** starszy JSON bez nowych pól generuje się bez błędu.
7. **Test parsowania (Wymaganie 6.3):** wszystkie pliki .py (ast.parse) i .jsx (esbuild transform) parsują się; serwer odpowiada na /generate-hall i /validate-hall.

## Uzasadnienie decyzji projektowych

- **Dlaczego obrót przez rotację elementów, nie zamianę wymiarów:** zamiana width↔length nie zmienia fizycznego kierunku ram w przestrzeni (ramy nadal wzdłuż X), więc nie spełnia Wymagania 1. Prawdziwy obrót wokół Y jest jedyną drogą do prostopadłych ram.
- **Dlaczego nie zamieniamy scale:** renderer skaluje jednostkowy box PRZED rotacją; ustawienie rotation.y obraca już przeskalowaną bryłę jako całość. Zamiana scale.x↔scale.z powodowała spłaszczenie — to była przyczyna „rozsypania" geometrii.
- **Dlaczego transformacja w HallGenerator, nie w generatorach:** spełnia Wymaganie 5.1 (zero zmian w 15 fabrykach) i centralizuje logikę obrotu w jednym miejscu, ułatwiając przyszłe rozszerzenie o dowolne kąty.
- **Alternatywa odrzucona — grupowanie w Three.js `<group>`:** przeniosłoby obrót na frontend, ale skomplikowałoby logikę styków/attyk (która działa na współrzędnych globalnych w backendzie) i wykrywanie kolizji. Transformacja w backendzie utrzymuje jedno źródło prawdy o pozycjach globalnych.
- **Dlaczego złożenie macierzy zamiast dodania kątów Eulera:** pierwsza wersja dodawała kąt obrotu do składowej ry. Działa to dla elementów obróconych wyłącznie wokół Y (pasy, słupy, panele), ale krzyżulce i słupki kratownic mają nachylenie zapisane w rx (płatwie, płaszczyzna ZY) lub rz (dźwigary główne, płaszczyzna XY). Dodanie 90° tylko do ry łamie te elementy, bo rotacje 3D nie są przemienne. Poprawne jest złożenie pełnych macierzy R_y(kąt)·R_element i rozłożenie na kąty Eulera XYZ zgodne z konwencją Three.js.
