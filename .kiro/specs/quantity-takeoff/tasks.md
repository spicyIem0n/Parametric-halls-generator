# Plan implementacji — Moduł przedmiaru ilościowego

- [ ] 1. Utworzyć kalkulator przedmiaru w backendzie
  - Stworzyć `backend/core/takeoff_calculator.py` z klasą/funkcją `compute(params) -> list[dict]`
  - Zaimplementować agregację komponentów wg mapy grup (słupy, stopy, obudowa, pokrycie, posadzka, podbudowa, podwaliny, bramy, doki, świetliki, klapy, pasma, ściany PPOŻ, stężenia, pomieszczenia, biura, antresole)
  - Zaimplementować helpery: objętość (sx*sy*sz), powierzchnia płyty (dwie większe składowe), długość pręta (max składowa), zliczanie sztuk
  - Pominąć markery wizualne (reserve_zone_marker, reserve_truss_marker)
  - _Wymagania: 1.1, 1.4, 3.1-3.9_

- [ ] 2. Zaimplementować pozycje wskaźnikowe i rozbicie materiał/montaż
  - Stal dachu: 12 kg/m² × powierzchnia hali (kg, materiał i montaż)
  - Ryglówka: liczba otworów (dock_door + gate_door) jako kpl, uwaga „400 kg/kpl"
  - Słupy: materiał m³, montaż szt; stopy: materiał m³, montaż m³; podwaliny: materiał m³, montaż mb
  - Każda pozycja jako para bliźniacza materiał + montaż z numeracją L.p.
  - Obsłużyć tryb Complex (zbiorczo, hall_area = suma modułów)
  - _Wymagania: 1.3, 2.2, 2.3, 2.4, 3.3, 3.4_

- [ ] 3. Dodać endpointy API
  - `POST /quantity-takeoff` w `backend/main.py` zwracający {"items": [...]}
  - `POST /quantity-takeoff/export` zwracający plik .xlsx (StreamingResponse)
  - _Wymagania: 1.1, 5.1_

- [ ] 4. Dodać eksport Excel (openpyxl)
  - Dodać `openpyxl` do `backend/requirements.txt` i zainstalować
  - Zbudować arkusz z kolumnami: L.p., Opis pozycji, Jednostka miary, Ilość, Cena jednostkowa, Wartość, Uwagi
  - Kolumny Cena/Wartość puste; nazwa pliku przedmiar_hala_SZERxDL.xlsx
  - _Wymagania: 5.1, 5.2, 5.3, 5.4_

- [ ] 5. Dodać funkcje API po stronie frontendu
  - W `frontend/src/api.js`: `getQuantityTakeoff(params)` i `exportTakeoff(params)` (pobranie blob → download)
  - _Wymagania: 1.1, 5.1_

- [ ] 6. Utworzyć widok tabeli przedmiaru
  - Nowy komponent `frontend/src/components/QuantityTakeoffView.jsx` z tabelą (7 kolumn) i przyciskiem „Eksportuj do Excel"
  - Stan pusty gdy brak danych
  - _Wymagania: 2.1, 4.1, 4.3, 5.1_

- [ ] 7. Zintegrować widok z App.jsx
  - Stan `takeoff`; w `handleGenerate` po modelu wywołać `getQuantityTakeoff`
  - Przełącznik widoku 3D / Przedmiar (żeby nie zasłaniać modelu)
  - _Wymagania: 1.1, 1.2, 4.1, 4.2_

- [ ] 8. Weryfikacja i testy
  - Test API: simple 30×60 → posadzka 1800 m², stal dachu 21600 kg
  - Test: 2 doki + 1 brama → ryglówka 3 kpl, dock_doors 2 szt, gate_doors 1 szt
  - Test: słupy materiał m³>0, montaż szt = liczba słupów
  - Test: complex 2 moduły → stal dachu = 12×(suma powierzchni)
  - Test eksportu: /quantity-takeoff/export zwraca poprawny plik xlsx
  - Parsowanie .py (ast) i .jsx (esbuild); endpointy odpowiadają
  - _Wymagania: 6.1, 6.2, 6.3_
