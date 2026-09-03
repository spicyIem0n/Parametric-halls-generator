"""
AdminAuth — minimalna ochrona panelu administratora prostym tokenem
(wspólnym hasłem), bez kont użytkowników.

Token ustawia się zmienną środowiskową ADMIN_TOKEN na maszynie, na której
działa backend (patrz start.bat). Jeśli zmienna nie jest ustawiona, używany
jest token domyślny — wystarczający do pracy lokalnej/deweloperskiej, ale
KONIECZNIE do zmiany przy wystawieniu backendu na serwer dostępny dla innych
użytkowników (inaczej każdy zna domyślny token).
"""

import os

_DEFAULT_TOKEN = "zmien-mnie-w-ADMIN_TOKEN"


def get_admin_token() -> str:
    return os.environ.get("ADMIN_TOKEN", _DEFAULT_TOKEN)


def is_using_default_token() -> bool:
    return "ADMIN_TOKEN" not in os.environ


def check_admin_token(token: str) -> bool:
    return bool(token) and token == get_admin_token()
