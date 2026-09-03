"""
FeatureFlags — proste globalne przełączniki funkcji programu (włącz/wyłącz),
np. do rozróżnienia wersji trialowej od pełnej albo do wyłączenia funkcji na
życzenie.

Model celowo prosty, dopasowany do dzisiejszej architektury (brak kont
użytkowników, jeden backend = jedno wdrożenie dla jednego klienta/triala):
- Flagi są GLOBALNE dla całej instancji backendu — nie ma pojęcia "różni
  użytkownicy tego samego serwera widzą różne funkcje". Rozróżnienie
  trial/płatna wersja odbywa się przez to, że każdy klient/trial ma własne
  wdrożenie backendu z własnym plikiem flag.
- Stan trzymany w pliku data/feature_flags.json (tworzony automatycznie z
  wartościami domyślnymi przy pierwszym uruchomieniu).
- Zmiana flagi wymaga tokenu administratora (zmienna środowiskowa ADMIN_TOKEN)
  — patrz core.admin_auth.
"""

from __future__ import annotations

import json
import os
import threading
from typing import Dict

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
FLAGS_PATH = os.path.join(_DATA_DIR, "feature_flags.json")

# Domyślny stan każdej flagi, gdy plik jeszcze nie istnieje albo jej brakuje
# w istniejącym pliku (np. flaga dodana w nowszej wersji programu).
DEFAULT_FLAGS: Dict[str, bool] = {
    "price_catalog_edit": True,  # pobieranie/wgrywanie cennika (price_catalog.xlsx)
}

# Etykiety do wyświetlenia w panelu administratora.
FLAG_LABELS: Dict[str, str] = {
    "price_catalog_edit": "Edycja cennika (pobierz/wgraj price_catalog.xlsx)",
}

_LOCK = threading.Lock()


def _read_raw() -> Dict[str, bool]:
    if not os.path.exists(FLAGS_PATH):
        return {}
    try:
        with open(FLAGS_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def get_flags() -> Dict[str, bool]:
    """Zwraca aktualny stan wszystkich znanych flag (uzupełniony wartościami domyślnymi)."""
    raw = _read_raw()
    return {name: bool(raw.get(name, default)) for name, default in DEFAULT_FLAGS.items()}


def is_enabled(name: str) -> bool:
    """Czy dana funkcja jest włączona. Nieznana nazwa flagi -> traktowana jako włączona
    (żeby literówka w nazwie flagi nigdy nie wyłączyła cichcem czegoś ważnego)."""
    return get_flags().get(name, True)


def set_flag(name: str, value: bool) -> Dict[str, bool]:
    """Ustawia jedną flagę i zapisuje stan na dysku. Zwraca pełny, zaktualizowany stan."""
    if name not in DEFAULT_FLAGS:
        raise ValueError(f"Nieznana flaga funkcji: '{name}'")
    with _LOCK:
        current = get_flags()
        current[name] = bool(value)
        os.makedirs(_DATA_DIR, exist_ok=True)
        tmp_path = FLAGS_PATH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(current, fh, ensure_ascii=False, indent=2)
        os.replace(tmp_path, FLAGS_PATH)
        return current
