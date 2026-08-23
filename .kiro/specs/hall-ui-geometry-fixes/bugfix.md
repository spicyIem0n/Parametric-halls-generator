# Bugfix Requirements Document

## Introduction

Zgłoszenie dotyczy panelu kontrolek (`frontend/src/components/Controls.jsx`) oraz geometrii dachu dwuspadowego i mechanizmu ręcznego doboru gabarytów w generatorze hal.

Badanie kodu wykazało jedną wspólną przyczynę dwóch najpoważniejszych objawów ([3] znikający model przy dachu grawitacyjnym i [7] niedziałający tryb ręczny):
funkcja `handleChange` w `Controls.jsx` konwertuje **każdą** wartość pola (poza checkboxem) przez `parseFloat`, również wartości pól `<select>` typu tekstowego. Wybór `gravity`, `manual` (słupy) albo `manual` (fundamenty) zapisuje więc do stanu `NaN`, `JSON.stringify` zamienia `NaN` na `null`, a Pydantic odrzuca żądanie błędem 422 (`Input should be a valid string`). `api.js` przechwytuje błąd i zwraca `{ components: [] }`, więc scena 3D zostaje wyczyszczona — model "znika".

Weryfikacja backendu (uruchomienie generatora bezpośrednio w Pythonie) potwierdziła, że:
- generacja dla `gravity` **nie** wyrzuca wyjątku (3441 komponentów przy 30×60 m) — objaw jest po stronie frontendu,
- tryb `manual` w `ColumnFactory` i `FoundationFactory` **działa** poprawnie, gdy wartość `column_method`/`foundation_method` dotrze jako `"manual"` (przekroje 0.7/0.8/0.9 i stopy 2.9/3.1/3.3 zamiast domyślnych),
- niezależnie od powyższego poszycie dachu grawitacyjnego jest odbite: połacie tworzą literę V (okap 11.58 m, kalenica 8.88 m) podczas gdy dźwigary tworzą ∧ (kalenica 11.44 m, okap 8.80 m) — panele przebijają konstrukcję,
- kategorie `external_dock` i `internal_dock` w `manual_sizes` / `manual_column_sections` nie są odczytywane przez żadną fabrykę (martwe pola formularza), a kategorii `external_corner` nie ma wcale,
- `cladding_orientation` istnieje w modelu, ale nie jest czytane przez żadną fabrykę i nie ma kontrolki w UI.

Zakres poprawki obejmuje ponadto usprawnienia UI: ręczne wpisywanie wymiarów głównych, poszerzone zakresy suwaków, nowy selektor doków z wyborem typu i zaznaczaniem zakresu (Shift), zmiany nazw sekcji oraz pionowy układ obudowy z poziomymi ryglami montażowymi.

## Bug Analysis

### Current Behavior (Defect)

Stan obecny — zachowanie zaobserwowane w kodzie i potwierdzone uruchomieniem generatora.

1.1 WHEN użytkownik wybiera w sekcji "2. Geometria Dachu" opcję "Grawitacyjne (Dwuspadowy)" THEN `handleChange` zapisuje `parseFloat('gravity')` czyli `NaN` do `params.roof_drainage_type`, żądanie do `/generate-hall` przenosi `null`, backend odpowiada 422, `api.js` zwraca pustą listę komponentów i model 3D znika ze sceny.

1.2 WHEN model jest generowany z `roof_drainage_type='gravity'` (żądanie z poprawną wartością tekstową) THEN `RoofFactory` nadaje połaciom rotację `-angle` dla strony lewej i `+angle` dla prawej, co daje poszycie w kształcie litery V (najwyżej przy okapach, najniżej w kalenicy), odwrotnie do dźwigarów tworzących kalenicę w osi hali — panele przecinają konstrukcję i wystają ponad okapy.

1.3 WHEN model jest generowany z `roof_drainage_type='gravity'` THEN `GridSystem3D.get_parapet_height()` zwraca wysokość kalenicy + 0.20 m i `CladdingFactory` obudowuje ściany wzdłużne pełną wysokością attyki (dla 30 m i 10° o ~2.8 m ponad okap), więc dach dwuspadowy jest zabudowany prostopadłościenną skrzynią zamiast zakończyć się na okapie.

1.4 WHEN użytkownik wybiera w sekcji "5. Konstrukcja i Fundamenty" opcję "Ręczne przekroje [X, Z]" lub "Gabaryty ręczne [A, B, H]" THEN `handleChange` zapisuje `NaN` do `column_method` / `foundation_method`, backend odpowiada 422 i model 3D znika — ręczne wprowadzanie gabarytów jest nieosiągalne z UI.

1.5 WHEN formularz ręcznych gabarytów jest wyświetlany THEN system pokazuje pola dla kategorii `external_dock` i `internal_dock`, których żadna fabryka nie odczytuje (`ColumnFactory` i `FoundationFactory` czytają wyłącznie `external_main`, `internal_main`, `intermediate_cladding`), więc edycja tych pól nie zmienia geometrii.

1.6 WHEN model jest generowany THEN system nie rozróżnia słupów narożnych — brak kategorii `external_corner`, a wszystkie słupy skrajnych osi ram otrzymują przekrój i stopę `external_main`; słupy szczytowe i pośrednie pod obudowę dzielą jedną kategorię `intermediate_cladding`.

1.7 WHEN użytkownik edytuje pole ręcznego gabarytu THEN handler modyfikuje tablicę w istniejącym obiekcie stanu w miejscu (`newParams.manual_column_sections[type][i] = ...` na płaskiej kopii `{ ...params }`), więc poprzedni stan zostaje nadpisany i zmiana nie jest wykrywalna przez porównanie referencji.

1.8 WHEN użytkownik chce ustawić dokładną wartość szerokości, długości, wysokości w świetle, ilości naw lub rozstawu ram w sekcji "1. Geometria Główna" THEN system udostępnia wyłącznie suwak (`input type="range"`), bez pola do wpisania liczby.

1.9 WHEN użytkownik potrzebuje hali większej niż zakresy suwaków THEN system ogranicza szerokość do 10–60 m, długość do 10–120 m i ilość naw do 1–4, bez możliwości przekroczenia tych wartości.

1.10 WHEN użytkownik konfiguruje doki w sekcji "3. Logistyka i Doki" THEN system pozwala wyłącznie klikać pojedyncze slot-y cyklicznie (`none → dock → gate → none`), bez wyboru rodzaju z listy i bez zaznaczania zakresu slotów.

1.11 WHEN użytkownik przegląda panel kontrolek THEN sekcja obudowy nosi nazwę "4. Obudowa Ruukki", a sekcja konstrukcji "5. Konstrukcja i Fundamenty".

1.12 WHEN parametr `cladding_orientation` ma wartość `'vertical'` THEN backend ignoruje go (żadna fabryka nie odczytuje tego pola), obudowa jest generowana jak dla `'horizontal'` jako pojedyncze panele pełnej wysokości attyki na slot, bez podziału i bez poziomych rygli montażowych; UI nie udostępnia przełącznika orientacji.

### Expected Behavior (Correct)

2.1 WHEN użytkownik wybiera w sekcji geometrii dachu opcję "Grawitacyjne (Dwuspadowy)" THEN system SHALL przekazać `roof_drainage_type` jako łańcuch `"gravity"` (bez konwersji numerycznej pól tekstowych), otrzymać poprawną odpowiedź z `/generate-hall` i wyświetlić model 3D.

2.2 WHEN model jest generowany z `roof_drainage_type='gravity'` THEN system SHALL wygenerować poszycie dachowe zgodne z geometrią dźwigarów: kalenica w osi hali, spadek w kierunku okapów, połacie oparte na górnym pasie dźwigara bez przecinania konstrukcji.

2.3 WHEN model jest generowany z `roof_drainage_type='gravity'` THEN system SHALL zakończyć obudowę ścian wzdłużnych na poziomie okapu (z zachowaniem zamknięcia ścian szczytowych do linii połaci), tak aby bryła dachu dwuspadowego była widoczna zamiast zabudowana attyką.

2.4 WHEN użytkownik wybiera ręczny dobór przekrojów słupów lub gabarytów stóp THEN system SHALL przekazać `column_method` / `foundation_method` jako łańcuch `"manual"`, wygenerować model bez błędu i zastosować wpisane wartości do geometrii odpowiednich elementów.

2.5 WHEN formularz ręcznych gabarytów jest wyświetlany THEN system SHALL pokazywać wyłącznie kategorie faktycznie odczytywane przez fabryki, w podziale na: słupy główne zewnętrzne (`external_main`), słupy zewnętrzne narożne (`external_corner`), słupy zewnętrzne pośrednie pod obudowę (`external_intermediate_cladding`) i słupy wewnętrzne (`internal_main`), z odpowiadającym podziałem stóp fundamentowych.

2.6 WHEN model jest generowany THEN system SHALL rozpoznać słupy narożne (przecięcie osi skrajnej X ze skrajną osią Z) jako kategorię `external_corner` i nadać im przekrój oraz stopę z tej kategorii, a słupom pośrednim pod obudowę kategorię `external_intermediate_cladding`.

2.7 WHEN użytkownik edytuje pole ręcznego gabarytu THEN system SHALL zaktualizować stan niemutowalnie (nowe tablice i nowy obiekt słownika) i natychmiast pokazać wpisaną wartość w polu.

2.8 WHEN użytkownik ustawia szerokość, długość, wysokość w świetle, ilość naw lub rozstaw ram THEN system SHALL udostępnić pole numeryczne obok suwaka, przyjąć wartość wpisaną z klawiatury, utrzymać synchronizację obu kontrolek w obu kierunkach i ograniczyć wynik do dopuszczalnego zakresu parametru.

2.9 WHEN użytkownik korzysta z suwaków geometrii głównej THEN system SHALL udostępnić zakresy trzykrotnie większe: szerokość do 180 m, długość do 360 m, ilość naw do 12.

2.10 WHEN użytkownik konfiguruje doki THEN system SHALL udostępnić na górze sekcji rozwijaną listę rodzaju otworu (m.in. brak / dok / brama), zastosować wybrany rodzaj do pojedynczo klikniętego slotu oraz — przy kliknięciu z przytrzymanym klawiszem Shift — do całego zakresu slotów od ostatnio klikniętego do bieżącego.

2.11 WHEN użytkownik przegląda panel kontrolek THEN system SHALL wyświetlić sekcję obudowy pod nazwą "ŚCIANY ZEWNĘTRZNE" oraz sekcję konstrukcji pod nazwą "KONSTRUKCJA".

2.12 WHEN użytkownik wybierze pionowy układ obudowy (`cladding_orientation='vertical'`) THEN system SHALL wygenerować obudowę jako pionowe płyty o szerokości modularnej wybranego panelu z katalogu oraz dodać poziome rygle stalowe stanowiące podkonstrukcję ich montażu, z uwzględnieniem otworów doków i bram.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN `roof_drainage_type='vacuum'` THEN system SHALL CONTINUE TO generować dach kopertowy ze spadkami, wpustami dachowymi (`drainage_inlet`) i słupkami dystansowymi według `drainage_zones_x` / `drainage_zones_z` / `roof_slope_percent`.

3.2 WHEN `column_method='default'` i `foundation_method='default'` THEN system SHALL CONTINUE TO stosować gabaryty z `DEFAULTS` (przekroje 0.4×0.4 i 0.3×0.3, stopy 2.0×2.0, 1.5×1.5, 1.2×1.2).

3.3 WHEN użytkownik przesuwa suwak parametru liczbowego THEN system SHALL CONTINUE TO aktualizować wartość parametru i przeliczać model po naciśnięciu "Buduj Model 3D".

3.4 WHEN użytkownik klika pojedynczy slot doku bez klawisza Shift THEN system SHALL CONTINUE TO ustawiać stan tylko tego slotu, a przyciski "Max Doki L/R" i "Czyść L/R" SHALL CONTINUE TO wypełniać i czyścić całą stronę hali.

3.5 WHEN `cladding_orientation='horizontal'` THEN system SHALL CONTINUE TO generować obudowę jak dotychczas, w tym wycięcia otworów dla doków i bram oraz zamknięcia narożników na ścianach szczytowych.

3.6 WHEN w przęśle po danej stronie znajduje się dok THEN system SHALL CONTINUE TO stosować `dock_foundation_depth` dla słupów i stóp w tym obszarze.

3.7 WHEN model jest generowany THEN system SHALL CONTINUE TO korzystać z `GridSystem3D` jako jedynego źródła pozycji osi, slotów i wysokości oraz zatrzaskiwać długość hali do wielokrotności rozstawu ram.

3.8 WHEN backend zwraca komponenty THEN system SHALL CONTINUE TO zachować kontrakt `Component3D` (`type`, `position`, `rotation`, `scale`, `meta`), a `Scene3D` SHALL CONTINUE TO mapować typy na materiały, kategorie widoczności i podświetlenie wymagań PPOŻ.

3.9 WHEN użytkownik korzysta z sekcji 6–10 (PPOŻ, pomieszczenia techniczne, biura zewnętrzne, antresole, rezerwa pod biura) THEN system SHALL CONTINUE TO działać bez zmian.

3.10 WHEN `hall_type='complex'` THEN system SHALL CONTINUE TO generować bloki z transformacją offsetu i rotacji według `BlockDefinition`.

3.11 WHEN model jest generowany THEN walidacja `/validate-hall` SHALL CONTINUE TO zwracać listę kolizji w obecnym formacie, a panel kontrolek SHALL CONTINUE TO wyświetlać je jako ostrzeżenia i błędy.
