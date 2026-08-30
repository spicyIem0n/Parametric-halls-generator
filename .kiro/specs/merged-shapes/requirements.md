# Wymagania — Hale o kształtach złożonych z prostokątów (scalanie modułów)

## Wprowadzenie

Tryb Complex pozwala składać halę z wielu prostokątnych modułów stykających się bokami. Obecnie połączenie typu „bez ściany / scalone" (none) usuwa jedynie ściany na linii styku, ale pozostawia zdublowane słupy i fundamenty obu modułów. Celem tej funkcji jest umożliwienie tworzenia hal o kształtach złożonych (L, T, U, krzyż) poprzez prawdziwe scalenie stykających się modułów w jedną przestrzeń: usunięcie ścian oraz zdublowanego rzędu słupów i stóp na wspólnej krawędzi, tak aby powstała jedna spójna bryła zamiast dwóch sklejonych hal.

Zakres pierwszej iteracji: kąty proste (moduły stykają się bokami prostopadle); scalenie usuwa ściany (już działa) oraz zdublowany rząd słupów i fundamentów na styku (jeden wspólny rząd pozostaje); walidacja że moduły faktycznie przylegają. Poza zakresem tej iteracji: wspólna rynna koszowa, łączenie połaci dachu, dowolne kąty.

## Zasady uzgodnione

- Kąty proste — moduły stykają się bokami pod kątem 90°.
- Przy scaleniu (none) na linii styku pozostaje JEDEN rząd słupów (usuwamy zdublowany rząd drugiego modułu).
- Fundamenty pod usuniętymi słupami są również usuwane (pozostaje jeden rząd stóp).
- Ściany na styku usuwane jak dotychczas; bez wprowadzania rynny koszowej ani łączenia połaci dachu.
- Funkcja dotyczy trybu Complex. Tryb Simple pozostaje bez zmian (pojedynczy prostokąt).

## Wymagania

### Wymaganie 1: Scalanie modułów w jedną przestrzeń

**Historyjka użytkownika:** Jako projektant chcę połączyć dwa stykające się moduły opcją „scal (jedna przestrzeń)", aby uzyskać halę o kształcie L/T/U bez wewnętrznych ścian i zdublowanych słupów na styku.

#### Kryteria akceptacji

1. GDY dwa moduły stykają się bokiem a połączenie ma typ „none" (scalone) WTEDY ściany na linii styku są usuwane (jak dotychczas).
2. GDY połączenie jest typu „none" WTEDY zdublowany rząd słupów na linii styku jest usuwany, pozostaje jeden wspólny rząd.
3. GDY słup na linii styku jest usuwany WTEDY usuwany jest również fundament (stopa) pod tym słupem.
4. GDY moduły są scalone WTEDY powstała bryła wygląda jak jedna spójna przestrzeń (kształt L/T/U/krzyż), a nie dwie osobne hale.

### Wymaganie 2: Zachowanie konstrukcji nośnej

**Historyjka użytkownika:** Jako projektant chcę, aby po scaleniu pozostał kompletny, sensowny układ konstrukcji, tak aby model był realistyczny.

#### Kryteria akceptacji

1. GDY zdublowany rząd słupów jest usuwany WTEDY pozostający rząd słupów zachowuje ciągłość konstrukcji na całej linii styku.
2. GDY moduły mają różną liczbę naw lub różny rozstaw na styku WTEDY usuwane są tylko słupy faktycznie pokrywające się na linii styku (w obszarze wspólnym), pozostałe pozostają.
3. GDY moduł ma elementy inne niż słupy/fundamenty/ściany na styku (dźwigary, płatwie) WTEDY nie są one usuwane (scalenie dotyczy tylko ścian, słupów i stóp na linii styku).

### Wymaganie 3: Poprawne rozpoznanie linii styku

**Historyjka użytkownika:** Jako projektant chcę, aby system prawidłowo wykrywał wspólną krawędź scalanych modułów, także gdy jeden jest obrócony, tak aby usunięcie dotyczyło właściwych elementów.

#### Kryteria akceptacji

1. GDY dwa moduły stykają się bokiem WTEDY system wyznacza linię styku na podstawie rzeczywistych obrysów modułów (po ewentualnym obrocie).
2. GDY styk jest częściowy (moduły nie pokrywają się na całej długości boku) WTEDY usuwanie słupów/stóp dotyczy tylko wspólnego odcinka styku.
3. GDY moduły nie przylegają (jest przerwa) WTEDY scalenie nie jest stosowane i połączenie pozostaje bez efektu scalenia.

### Wymaganie 4: Interfejs wyboru scalenia

**Historyjka użytkownika:** Jako użytkownik chcę wyraźnie wskazać, że dwa moduły mają być scalone w jedną przestrzeń, tak aby świadomie tworzyć kształty złożone.

#### Kryteria akceptacji

1. GDY użytkownik wybiera typ połączenia na styku WTEDY opcja „Bez ściany (scalone)" jest dostępna i czytelnie opisana jako scalenie w jedną przestrzeń.
2. GDY moduły mają prostopadłe ramy (różne orientacje) WTEDY opcja scalenia „none" pozostaje zablokowana (jak dotychczas), bo konstrukcje nie kooperują.
3. GDY scalenie jest wybrane WTEDY panel połączeń informuje o efekcie (usunięcie ścian i zdublowanych słupów).

### Wymaganie 5: Kompatybilność wsteczna i brak regresji

**Historyjka użytkownika:** Jako opiekun projektu chcę, aby zmiana nie zepsuła istniejących trybów i projektów, tak aby ryzyko było minimalne.

#### Kryteria akceptacji

1. GDY połączenie ma typ inny niż „none" (expansion_joint, internal_wall, fire_wall) WTEDY zachowuje się jak dotychczas (bez usuwania słupów).
2. GDY tryb to Simple WTEDY generacja pozostaje niezmieniona.
3. GDY starszy projekt jest wczytany WTEDY generacja działa bez błędów.
4. GDY moduł nie ma żadnego połączenia „none" WTEDY jego słupy i fundamenty pozostają kompletne.

### Wymaganie 6: Weryfikowalność

**Historyjka użytkownika:** Jako opiekun projektu chcę zweryfikować poprawność scalania, aby ufać rezultatowi.

#### Kryteria akceptacji

1. GDY dwa moduły są scalone WTEDY test API potwierdza mniejszą liczbę słupów i fundamentów na linii styku niż przy dylatacji (usunięty jeden rząd).
2. GDY moduły są scalone WTEDY test potwierdza brak ścian (sandwich_panel) na linii styku.
3. GDY zmiana jest wdrożona WTEDY backend i frontend parsują się bez błędów, a endpointy odpowiadają.
