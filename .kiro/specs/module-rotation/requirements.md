# Wymagania — Obrót modułów hali (układ współrzędnych)

## Wprowadzenie

Tryb Complex pozwala składać halę z wielu modułów. Każdy moduł ma parametr `frame_orientation` (0° lub 90°), który ma decydować o kierunku ram (dźwigarów) tego modułu. Obecnie obrót nie działa poprawnie: przy `frame_orientation=90` zamieniane są jedynie wymiary width↔length, przez co hala zmienia proporcje, ale ramy nadal biegną w tym samym kierunku (wzdłuż globalnej osi X). Wcześniejsza próba obracania gotowych komponentów o 90° łamała geometrię obudowy, dachu i płatwi, ponieważ zamieniała wymiary skali (scale X↔Z) elementów.

Celem jest wprowadzenie mechanizmu, w którym każdy moduł jest generowany w swoim **lokalnym układzie współrzędnych** (gdzie generatory zawsze działają identycznie — ramy zawsze wzdłuż lokalnej osi X), a następnie cały moduł jest **transformowany do układu globalnego** przez rotację wokół osi Y i translację. Dzięki temu nie trzeba modyfikować żadnego z generatorów geometrii. Mechanizm musi być zaprojektowany dla dowolnego kąta obrotu wokół osi Y (nie tylko 0° i 90°), aby w przyszłości umożliwić np. 45°, choć w pierwszej iteracji UI udostępnia jedynie 0° i 90°.

Kluczowy wniosek techniczny: renderer (Three.js) stosuje transformacje w kolejności scale → rotation → position na jednostkowym boxie. Oznacza to, że komponent może zostać poprawnie obrócony przez ustawienie jego `rotation_y` i przeliczenie `position`, **bez** zamiany wektora `scale` — mesh obróci się jako spójna bryła. To jest podstawa proponowanego rozwiązania.

## Wymagania

### Wymaganie 1: Obrót ram modułu w przestrzeni 3D

**Historyjka użytkownika:** Jako projektant chcę, aby po ustawieniu modułu na orientację 90° jego ramy (dźwigary) były fizycznie prostopadłe do ram modułu nieobróconego, tak aby móc modelować rzeczywiste układy hal z krzyżującymi się kierunkami konstrukcji.

#### Kryteria akceptacji

1. GDY moduł ma `frame_orientation = 0` WTEDY system generuje go bez obrotu (ramy wzdłuż globalnej osi X).
2. GDY moduł ma `frame_orientation = 90` WTEDY system obraca cały moduł (wszystkie elementy) o 90° wokół osi Y, tak że ramy biegną wzdłuż globalnej osi Z.
3. GDY moduł ma dowolny kąt `frame_orientation` (przyszłościowo, np. 45°) WTEDY mechanizm transformacji obraca cały moduł o ten kąt bez zmian w generatorach; UI w pierwszej iteracji ogranicza wybór do 0° i 90°.
4. GDY moduł jest obrócony o 90° WTEDY osie słupów, które w module nieobróconym leżały wzdłuż X, po obrocie leżą wzdłuż Z (i odwrotnie).
5. JEŻELI dwa moduły o identycznych wymiarach mają różne `frame_orientation` (0 i 90) WTEDY ich układy ram są względem siebie prostopadłe.

### Wymaganie 2: Zachowanie poprawnej geometrii wszystkich elementów po obrocie

**Historyjka użytkownika:** Jako projektant chcę, aby po obrocie modułu wszystkie jego elementy (dach, obudowa, płatwie, stężenia, doki, świetliki) zachowały prawidłowy kształt i proporcje, tak aby model 3D był realistyczny i kompletny.

#### Kryteria akceptacji

1. GDY moduł jest obrócony o 90° WTEDY każdy element (słup, panel obudowy, płatew, panel dachowy, dźwigar) zachowuje swoje oryginalne wymiary własne (grubość, wysokość, długość) — nie ulega spłaszczeniu ani deformacji.
2. GDY moduł jest obrócony WTEDY spadki dachu, kalenica i okapy są zorientowane spójnie z obróconą bryłą.
3. GDY moduł jest obrócony WTEDY panele obudowy pozostają na właściwych ścianach (podłużnych i szczytowych) obróconej bryły.
4. GDY moduł jest obrócony WTEDY liczba i typy wygenerowanych elementów są takie same jak dla modułu nieobróconego o zamienionych wymiarach (kompletność geometrii).
5. GDY renderer wyświetla obrócony element WTEDY stosuje transformację tak, że bryła jest obrócona jako całość (bez zamiany wektora scale elementu).
6. GDY moduł jest obrócony WTEDY WSZYSTKIE jego elementy podrzędne — w tym świetliki, klapy dymowe, pasma świetlne, doki, bramy, biura zewnętrzne, antresole wewnętrzne, pomieszczenia techniczne, strefy rezerwy, stężenia i ściany pożarowe — są obrócone razem z modułem jako spójna całość.

### Wymaganie 3: Poprawne pozycjonowanie i wymiary bryły na rzucie

**Historyjka użytkownika:** Jako projektant chcę, aby obrócony moduł zajmował na rzucie prostokąt o właściwych proporcjach i w miejscu wskazanym przez pozycję modułu, tak aby rozmieszczenie i styki modułów były zgodne z tym, co widzę w edytorze 2D.

#### Kryteria akceptacji

1. GDY moduł o wymiarach użytkownika width×length ma `frame_orientation=90` WTEDY jego obrys na rzucie ma wymiary length (wzdłuż globalnej osi X) × width (wzdłuż globalnej osi Z).
2. GDY moduł jest umieszczony w pozycji (position_x, position_z) WTEDY środek jego obrysu znajduje się w tym punkcie niezależnie od orientacji.
3. GDY edytor rzutu 2D rysuje obrócony moduł WTEDY prostokąt, znaczniki kierunku ram i wykrywanie styków są zgodne z fizycznym obrysem po obrocie.
4. GDY widok 3D i rzut 2D pokazują ten sam moduł WTEDY jego obrys i orientacja ram są spójne między oboma widokami.

### Wymaganie 4: Styki, dylatacje i ściany między modułami po obrocie

**Historyjka użytkownika:** Jako projektant chcę, aby logika połączeń (dylatacja, ściana wewnętrzna, ściana pożarowa, attyka przy różnicy wysokości) działała poprawnie także dla modułów obróconych, tak aby styki były realistyczne niezależnie od orientacji.

#### Kryteria akceptacji

1. GDY dwa moduły stykają się bokami a jeden lub oba są obrócone WTEDY system poprawnie wykrywa linię styku na podstawie rzeczywistych obrysów (po obrocie).
2. GDY na styku wybrano dylatację lub „bez ściany" WTEDY ściany wewnętrzne na linii styku są usuwane zgodnie z dotychczasową logiką, uwzględniając obrócone obrysy.
3. GDY moduły na styku mają różną wysokość WTEDY ściana attykowa wyższego modułu ponad dachem niższego jest zachowana, zgodnie z dotychczasową logiką.
4. GDY moduły mają prostopadłe ramy (różne `frame_orientation`) WTEDY opcja połączenia „bez ściany" jest zablokowana (walidacja), ponieważ konstrukcje nie kooperują.

### Wymaganie 5: Kompatybilność wsteczna i brak zmian w generatorach

**Historyjka użytkownika:** Jako opiekun projektu chcę, aby wprowadzenie obrotu nie wymagało zmian w istniejących generatorach elementów ani nie psuło istniejących projektów, tak aby ryzyko regresji było minimalne.

#### Kryteria akceptacji

1. GDY wprowadzany jest mechanizm obrotu WTEDY żaden z istniejących generatorów (ColumnFactory, RoofFactory, CladdingFactory, RoofLightFactory, DockFactory itd.) nie wymaga modyfikacji logiki generowania.
2. GDY moduł ma `frame_orientation=0` WTEDY wynik generacji jest identyczny z zachowaniem sprzed zmiany (brak regresji dla nieobróconych modułów).
3. GDY wczytywany jest starszy plik projektu bez pełnych pól modułu WTEDY generacja działa z wartościami domyślnymi (brak błędów walidacji).
4. GDY tryb Simple generuje pojedynczą halę WTEDY jego zachowanie pozostaje niezmienione.

### Wymaganie 6: Weryfikowalność rozwiązania

**Historyjka użytkownika:** Jako opiekun projektu chcę, aby poprawność obrotu dała się zweryfikować obiektywnie, tak aby potwierdzić że ramy rzeczywiście się obracają i geometria jest kompletna.

#### Kryteria akceptacji

1. GDY generowane są dwa moduły o identycznych wymiarach i różnych orientacjach WTEDY test API potwierdza, że rozpiętość ram jednego modułu leży wzdłuż X, a drugiego wzdłuż Z.
2. GDY generowany jest obrócony moduł WTEDY liczba elementów każdej kategorii (słupy, panele, płatwie, dach) jest niezerowa i porównywalna z modułem nieobróconym.
3. GDY zmiana jest wdrożona WTEDY frontend i backend parsują się bez błędów, a serwer odpowiada na żądania generacji.
