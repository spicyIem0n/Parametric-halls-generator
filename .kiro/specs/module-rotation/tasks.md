# Plan implementacji — Obrót modułów hali

- [x] 1. Przywrócenie prawdziwego obrotu w `_transform_components`
  - Zmodyfikować `backend/generators/hall_generator.py`: w metodzie `_transform_components` przeliczać pozycję przez macierz rotacji wokół Y, dodawać kąt do `rotation.y`, ale POZOSTAWIĆ wektor `scale` BEZ ZMIAN (usunąć zamianę `sx, sz = sz, sx`)
  - Zachować warunek szybkiego wyjścia dla `rotation_y == 0 and offset == [0,0,0]` (brak regresji)
  - _Wymagania: 1.2, 1.3, 2.1, 2.5_

- [x] 2. Usunięcie zamiany wymiarów w `_block_to_params`
  - W `backend/generators/hall_generator.py`: usunąć blok `if block.frame_orientation == 90: w, l = l, w`, tak aby moduł był generowany z oryginalnymi wymiarami użytkownika (width, length)
  - Zaktualizować komentarze wyjaśniające, że obrót realizuje `_transform_components`
  - _Wymagania: 1.1, 5.1_

- [x] 3. Podłączenie kąta obrotu w pętli `_generate_complex`
  - W `backend/generators/hall_generator.py`: w pętli po blokach ustawić `rotation_y = float(block.frame_orientation)` gdy blok jest obrócony i przekazać do `_transform_components` wraz z offsetem `(position_x, 0, position_z)`
  - Obsłużyć fallback do `position_offset` dla starszych projektów bez `position_x/position_z`
  - _Wymagania: 1.1, 1.2, 1.3, 5.3_

- [x] 4. Weryfikacja obrysów w `_process_connections`
  - W `backend/generators/hall_generator.py`: potwierdzić, że `block_bounds` liczy obrys po obrocie (zamiana w/l przy orient=90) — zgodnie z projektem logika pozostaje, ale zweryfikować spójność ze zmienionym mechanizmem obrotu
  - Upewnić się, że wykrywanie styków, usuwanie ścian i przycinanie attyk działa na obrysach globalnych
  - _Wymagania: 4.1, 4.2, 4.3_

- [x] 5. Weryfikacja spójności rzutu 2D w `ModuleLayoutEditor.jsx`
  - Potwierdzić, że `getEffectiveDims` opisuje obrys po obrocie (length×width przy orient=90)
  - Zweryfikować kierunek linii ram: orient=0 → linie wzdłuż X (poziome na rzucie), orient=90 → linie wzdłuż Z (pionowe na rzucie)
  - _Wymagania: 3.1, 3.3, 3.4_

- [x] 6. Test obrotu ram i braku deformacji (API)
  - Zrestartować serwer z czyszczeniem `__pycache__`
  - Wygenerować dwa moduły 24×48 (orient 0 i 90) i potwierdzić: moduł 0 ma rozpiętość osi słupów wzdłuż X i wiele osi wzdłuż Z; moduł 90 odwrotnie (ramy prostopadłe)
  - Potwierdzić, że panele obudowy obróconego modułu mają ten sam rozkład wartości scale co moduł nieobrócony (brak spłaszczenia)
  - _Wymagania: 1.4, 2.1, 6.1_

- [x] 7. Test kompletności geometrii i regresji (API)
  - Potwierdzić, że obrócony moduł ma niezerowe i porównywalne liczby elementów każdej kategorii (słupy, sandwich_panel, purlin, roof_panel) względem modułu nieobróconego
  - Potwierdzić, że moduł orient=0 generuje wynik identyczny z zachowaniem sprzed zmiany
  - Potwierdzić, że starszy JSON bez pełnych pól modułu generuje się bez błędu
  - _Wymagania: 2.4, 5.2, 5.3, 6.2_

- [x] 8. Test styków między modułami obróconymi (API)
  - Wygenerować dwa stykające się moduły (jeden obrócony) z połączeniem dylatacyjnym i potwierdzić usunięcie ścian na styku
  - Przy różnicy wysokości potwierdzić zachowanie ściany attykowej wyższego modułu
  - _Wymagania: 4.1, 4.2, 4.3_

- [x] 9. Weryfikacja końcowa parsowania i działania
  - Sprawdzić parsowanie wszystkich plików `.py` (ast.parse) i `.jsx` (esbuild transform)
  - Potwierdzić, że serwer odpowiada na `/generate-hall` i `/validate-hall`
  - Potwierdzić w przeglądarce (informacja dla użytkownika) że obrócony moduł wyświetla pełną, poprawną geometrię z prostopadłymi ramami
  - _Wymagania: 6.3_
