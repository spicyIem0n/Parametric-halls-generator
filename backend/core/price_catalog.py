"""
PriceCatalog — baza cen jednostkowych pozycji przedmiaru, edytowalna w Excelu
(data/price_catalog.xlsx, arkusz "Ceny").

Kluczem pozycji jest jej "opis" — dokładnie ten sam tekst, który
TakeoffCalculator generuje dla danej pozycji przedmiaru (np.
"Słup prefabrykowany — materiał"). Po tym tekście program dopasowuje cenę.

Samorozbudowa katalogu:
Przy każdym liczeniu przedmiaru (sync_and_price_items) lista pozycji zwrócona
przez TakeoffCalculator jest porównywana z zawartością arkusza "Ceny". Każda
pozycja, której opisu jeszcze w arkuszu nie ma, zostaje dopisana jako nowy
wiersz z pustą ceną. Dzięki temu w miarę rozbudowy programu (nowe fabryki /
nowe rodzaje elementów -> nowe pozycje w TakeoffCalculator) katalog sam
uzupełnia się o brakujące wiersze, gotowe do ręcznego wpisania ceny w Excelu —
nie trzeba nigdzie osobno "rejestrować" nowej pozycji cenowej.

Istniejące wiersze (i wpisane w nich ceny) nigdy nie są nadpisywane
automatycznie. Jeśli plik jest w danej chwili otwarty na wyłączność w Excelu
(blokada zapisu w Windows), dopisanie nowych wierszy jest po prostu pomijane —
liczenie przedmiaru i tak się powiedzie, nowe pozycje pojawią się bez ceny do
czasu zamknięcia pliku.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

from openpyxl import load_workbook

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CATALOG_PATH = os.path.join(_DATA_DIR, "price_catalog.xlsx")

PRICES_SHEET = "Ceny"
COL_OPIS = "Opis pozycji"
COL_JEDNOSTKA = "Jednostka"
COL_CENA = "Cena jednostkowa [PLN]"
COL_UWAGI = "Uwagi"
PRICE_COLUMNS = [COL_OPIS, COL_JEDNOSTKA, COL_CENA, COL_UWAGI]


def _read_price_rows() -> List[dict]:
    wb = load_workbook(CATALOG_PATH, read_only=True, data_only=True)
    try:
        ws = wb[PRICES_SHEET]
        header = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
        idx = {}
        for name in PRICE_COLUMNS:
            if name not in header:
                raise ValueError(f"Brak kolumny '{name}' w arkuszu '{PRICES_SHEET}' pliku {CATALOG_PATH}")
            idx[name] = header.index(name)

        rows = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            opis = row[idx[COL_OPIS]] if idx[COL_OPIS] < len(row) else None
            if opis is None or str(opis).strip() == "":
                continue
            rows.append({col: (row[idx[col]] if idx[col] < len(row) else None) for col in PRICE_COLUMNS})
        return rows
    finally:
        wb.close()


def load_price_catalog() -> List[dict]:
    """
    Zwraca listę pozycji cennika (np. do podglądu w UI).
    Jeśli plik jest w danej chwili niedostępny do odczytu (np. otwarty na
    wyłączność w Excelu) albo uszkodzony — zwraca listę pustą zamiast
    wyjątku, żeby liczenie przedmiaru mogło się mimo to zakończyć (po prostu
    bez cen w tym przebiegu).
    """
    if not os.path.exists(CATALOG_PATH):
        return []
    try:
        return _read_price_rows()
    except Exception:
        return []


def _price_map() -> Dict[str, Optional[float]]:
    prices: Dict[str, Optional[float]] = {}
    for row in load_price_catalog():
        opis = str(row[COL_OPIS]).strip()
        cena = row[COL_CENA]
        prices[opis] = float(cena) if isinstance(cena, (int, float)) else None
    return prices


def _append_missing_rows(missing: List[dict]) -> bool:
    """
    Dopisuje brakujące pozycje (opis + jednostka, bez ceny) na końcu arkusza "Ceny".
    Zwraca False (po cichu), jeśli plik jest w tej chwili niedostępny do zapisu
    (np. otwarty w Excelu) — dopisanie zostaje wtedy odłożone do następnego wywołania.
    """
    try:
        wb = load_workbook(CATALOG_PATH)
        ws = wb[PRICES_SHEET]
        for item in missing:
            ws.append([item["opis"], item["jednostka"], None, ""])
        wb.save(CATALOG_PATH)
        return True
    except Exception:
        return False


def sync_and_price_items(items: List[dict]) -> List[dict]:
    """
    Dopasowuje ceny jednostkowe z katalogu do pozycji przedmiaru i dolicza wartość.

    1) Dla pozycji z `items`, których opisu nie ma jeszcze w katalogu — dopisuje
       je do pliku Excel z pustą ceną (samorozbudowa katalogu).
    2) Uzupełnia każdej pozycji cena_jedn (z katalogu, jeśli ustawiona) i wylicza
       wartosc = ilosc * cena_jedn (None, gdy ceny brak).

    Modyfikuje i zwraca tę samą listę `items` (in place), zgodnie z formatem
    zwracanym przez TakeoffCalculator.compute().

    Awaria katalogu (plik zablokowany, uszkodzony, brak arkusza) nigdy nie
    przerywa liczenia przedmiaru — w najgorszym razie pozycje zostają bez cen.
    """
    if not os.path.exists(CATALOG_PATH):
        return items

    try:
        existing_opisy = {str(r[COL_OPIS]).strip() for r in load_price_catalog()}

        missing_unique: List[dict] = []
        seen = set()
        for it in items:
            opis = it["opis"]
            if opis not in existing_opisy and opis not in seen:
                seen.add(opis)
                missing_unique.append({"opis": opis, "jednostka": it["jednostka"]})

        if missing_unique:
            _append_missing_rows(missing_unique)

        prices = _price_map()
    except Exception:
        prices = {}

    for it in items:
        cena = prices.get(it["opis"])
        it["cena_jedn"] = cena
        it["wartosc"] = round(it["ilosc"] * cena, 2) if cena is not None else None

    return items
