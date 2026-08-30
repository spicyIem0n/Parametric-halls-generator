# Plan implementacji — Scalanie modułów w kształty złożone (L/T/U)

- [ ] 1. Rozszerzyć `_process_connections` o usuwanie zdublowanych słupów i fundamentów
  - W `backend/generators/hall_generator.py`, w metodzie `_process_connections`, po istniejącej fazie usuwania/przycinania ścian dodać drugą fazę
  - Zebrać `merge_zones` z `remove_zones` tam gdzie `conn_type == "none"` (axis, coord, rng_min, rng_max, bid_b jako moduł tracący rząd)
  - Filtrować komponenty typu `column`, `column_gable`, `foundation` należące do modułu B, leżące na linii styku (tol ~0.6 m) i w obrębie wspólnego odcinka (overlap)
  - Faza słupów działa na wyniku fazy ścian (na liście `filtered`)
  - _Wymagania: 1.1, 1.2, 1.3, 2.1, 2.2, 3.1, 3.2_

- [ ] 2. Zapewnić poprawność przypadków brzegowych i brak regresji
  - Upewnić się, że dla typów połączeń innych niż `none` słupy/fundamenty NIE są usuwane (expansion_joint, internal_wall, fire_wall bez zmian)
  - Overlap ogranicza usuwanie do wspólnego odcinka styku (styk częściowy)
  - Brak przylegania → brak strefy → brak scalenia
  - Tryb Simple i starsze projekty bez zmian
  - _Wymagania: 2.3, 3.3, 5.1, 5.2, 5.3, 5.4_

- [ ] 3. Zaktualizować opis opcji scalenia w interfejsie
  - W `frontend/src/components/Controls.jsx` (ConnectionsPanel): doprecyzować etykietę opcji „none" na „Bez ściany (scal w jedną przestrzeń)"
  - Dodać notę o efekcie: „Usuwa ściany i zdublowany rząd słupów na styku (kształt L/T/U)"
  - Zachować blokadę „none" dla prostopadłych ram (bez zmian)
  - _Wymagania: 4.1, 4.3_

- [ ] 4. Testy scalania i weryfikacja
  - Test API: dwa moduły stykające się `none` → mniej `column`+`column_gable` niż przy `expansion_joint`
  - Test: mniej `foundation` przy `none` niż `expansion_joint`
  - Test: brak `sandwich_panel` na linii styku przy `none`
  - Test regresji: `expansion_joint` bez zmian liczby słupów
  - Test kształtu L: trzy moduły, dwa styki `none` — pojedyncze słupy na liniach styku
  - Parsowanie backend .py (ast) i frontend .jsx (esbuild); endpointy odpowiadają
  - _Wymagania: 6.1, 6.2, 6.3_
