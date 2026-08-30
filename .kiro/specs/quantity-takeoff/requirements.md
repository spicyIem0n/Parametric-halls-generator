# Wymagania — Moduł przedmiaru ilościowego

## Wprowadzenie

Program generuje parametryczny model 3D hali. Celem tego modułu jest automatyczne tworzenie tabeli przedmiarowej (quantity takeoff) na podstawie wygenerowanego modelu. Tabela ma wypełniać się automatycznie po kliknięciu „Buduj Model 3D", być prezentowana w osobnym oknie/widoku aplikacji oraz umożliwiać eksport do pliku Excel (.xlsx) w identycznym układzie jak w programie.

Przedmiar rozbija zakres na poszczególne komponenty (nie zbiorczo). Każda pozycja występuje w dwóch wariantach: materiał i montaż (pozycje bliźniacze). Sposób ustalania cen pozostaje na razie nierozwiązany — kolumny ceny i wartości są obecne, ale niewypełniane automatycznie.

## Zasady ilościowania (uzgodnione)

- Wszystkie słupy (główne, szczytowe, pośrednie pod obudowę) traktowane są jako prefabrykaty żelbetowe: materiał w m³, montaż w szt.
- Stopy fundamentowe: materiał w m³, montaż w m³.
- Konstrukcja stalowa dachu (dźwigary + płatwie + stężenia dachowe): wskaźnikowo 12 kg/m² liczone przez powierzchnię hali (szerokość × długość), w kg — materiał i montaż. Wskaźnik do późniejszego uściślenia.
- Ryglówka bram i doków: konstrukcja stalowa 400 kg/komplet na każdą bramę lub dok; jednostka kpl — materiał i montaż.
- Płyta warstwowa ścienna, pokrycie dachu, ściany PPOŻ, pomieszczenia/biura: m².
- Posadzka: m². Podbudowa: m³. Podwaliny: materiał m³, montaż mb.
- Bramy dokowe, bramy kurierskie, świetliki, klapy dymowe: szt. Doki (fartuchy): kpl. Pasma świetlne: m².
- Tryb Complex: przedmiar zbiorczy (suma wszystkich modułów).

## Wymagania

### Wymaganie 1: Automatyczne generowanie przedmiaru z modelu

**Historyjka użytkownika:** Jako kosztorysant chcę, aby po wygenerowaniu modelu 3D tabela przedmiarowa wypełniła się automatycznie ilościami policzonymi z modelu, tak aby nie wprowadzać danych ręcznie.

#### Kryteria akceptacji

1. GDY użytkownik kliknie „Buduj Model 3D" WTEDY system liczy przedmiar na podstawie wygenerowanych komponentów i aktualizuje tabelę przedmiarową.
2. GDY model zostanie przeliczony WTEDY każda pozycja przedmiaru ma wyliczoną ilość w swojej jednostce miary.
3. GDY model jest w trybie Complex (wiele modułów) WTEDY ilości są sumowane zbiorczo dla całej hali.
4. GDY komponent jest markerem wizualnym (np. reserve_zone_marker, reserve_truss_marker) WTEDY jest pomijany w przedmiarze materiałowym.

### Wymaganie 2: Struktura tabeli przedmiarowej

**Historyjka użytkownika:** Jako kosztorysant chcę tabelę o standardowym układzie kolumn ofertowych, tak aby móc jej używać bez przeróbek.

#### Kryteria akceptacji

1. GDY tabela jest wyświetlana WTEDY zawiera kolumny: L.p., Opis pozycji, Jednostka miary, Ilość, Cena jednostkowa, Wartość, Uwagi.
2. GDY pozycja dotyczy komponentu WTEDY występuje w dwóch wierszach: „... — materiał" i „... — montaż" (pozycje bliźniacze).
3. GDY opis pozycji jest tworzony WTEDY jest prosty, bez szczegółów (np. „Słup prefabrykowany", „Płyta warstwowa", „Konstrukcja stalowa dachu").
4. GDY jednostki miary są przypisywane WTEDY są zgodne z uzgodnionymi zasadami ilościowania (m³, szt, kg, m², mb, kpl).
5. GDY cena jednostkowa nie jest ustalona WTEDY kolumny Cena jednostkowa i Wartość pozostają puste (niewypełniane automatycznie).

### Wymaganie 3: Pozycje przedmiaru

**Historyjka użytkownika:** Jako kosztorysant chcę, aby przedmiar obejmował wszystkie istotne komponenty hali w rozbiciu na materiał i montaż, tak aby oferta była kompletna.

#### Kryteria akceptacji

1. GDY w modelu są słupy WTEDY przedmiar zawiera „Słup prefabrykowany — materiał" [m³] oraz „Słup prefabrykowany — montaż" [szt].
2. GDY w modelu są stopy fundamentowe WTEDY przedmiar zawiera „Stopa fundamentowa — materiał" [m³] oraz „Stopa fundamentowa — montaż" [m³].
3. GDY w modelu jest dach WTEDY przedmiar zawiera „Konstrukcja stalowa dachu — materiał" [kg] oraz „... — montaż" [kg], liczone jako 12 kg/m² × powierzchnia hali.
4. GDY w modelu są bramy lub doki WTEDY przedmiar zawiera „Ryglówka bram/doków — materiał" [kpl] oraz „... — montaż" [kpl], liczone jako liczba otworów (400 kg/kpl jako informacja pomocnicza).
5. GDY w modelu jest obudowa ścienna WTEDY przedmiar zawiera „Płyta warstwowa — materiał" [m²] oraz „... — montaż" [m²].
6. GDY w modelu jest pokrycie dachu WTEDY przedmiar zawiera „Pokrycie dachu — materiał" [m²] oraz „... — montaż" [m²].
7. GDY w modelu jest posadzka WTEDY przedmiar zawiera „Posadzka przemysłowa — materiał" [m²] oraz „... — montaż" [m²]; podbudowa w m³.
8. GDY w modelu są bramy dokowe, kurierskie, świetliki lub klapy dymowe WTEDY każda ma pozycje materiał + montaż w [szt]; pasma świetlne w [m²]; doki (fartuchy) w [kpl].
9. GDY w modelu są ściany PPOŻ, stężenia, pomieszczenia techniczne lub biura WTEDY mają odpowiednie pozycje materiał + montaż (m², mb) zgodnie z zasadami.
10. GDY dana grupa komponentów nie występuje w modelu WTEDY jej pozycje nie pojawiają się w tabeli (lub mają ilość zero — decyzja projektowa).

### Wymaganie 4: Osobne okno/widok przedmiaru

**Historyjka użytkownika:** Jako użytkownik chcę oglądać przedmiar w osobnym widoku, tak aby nie zasłaniał modelu 3D i był czytelny.

#### Kryteria akceptacji

1. GDY użytkownik otworzy widok przedmiaru WTEDY tabela jest wyświetlana w osobnym oknie/panelu aplikacji.
2. GDY model zostanie przeliczony WTEDY widok przedmiaru odzwierciedla aktualne ilości.
3. GDY tabela jest pusta (brak modelu) WTEDY widok pokazuje czytelny stan pusty.

### Wymaganie 5: Eksport do Excel

**Historyjka użytkownika:** Jako kosztorysant chcę wyeksportować tabelę do pliku .xlsx w tym samym układzie co w programie, tak aby kontynuować pracę w arkuszu.

#### Kryteria akceptacji

1. GDY użytkownik kliknie „Eksportuj do Excel" WTEDY system generuje plik .xlsx z tabelą przedmiarową.
2. GDY plik jest generowany WTEDY zawiera te same kolumny i wiersze co tabela w programie (L.p., Opis, Jednostka, Ilość, Cena jednostkowa, Wartość, Uwagi).
3. GDY plik jest generowany WTEDY kolumny ceny i wartości są obecne, lecz puste (do wypełnienia w arkuszu).
4. GDY eksport się powiedzie WTEDY plik jest pobierany przez przeglądarkę z sensowną nazwą (np. przedmiar_hala_SZERxDL.xlsx).

### Wymaganie 6: Poprawność i weryfikowalność

**Historyjka użytkownika:** Jako opiekun projektu chcę, aby liczenie przedmiaru dało się zweryfikować, tak aby ufać ilościom.

#### Kryteria akceptacji

1. GDY generowany jest przedmiar dla znanej hali WTEDY test API potwierdza poprawne wartości (np. powierzchnia posadzki = szer × dł, stal dachu = 12 × szer × dł, ryglówka kpl = liczba otworów).
2. GDY backend i frontend są uruchomione WTEDY parsują się bez błędów, a nowy endpoint przedmiaru odpowiada.
3. GDY zmienia się model WTEDY ilości w przedmiarze zmieniają się spójnie z modelem.
