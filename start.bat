@echo off
echo Inicjalizacja środowiska Hale Parametryczne...

:: 1. Dodanie przenośnego Node.js do ścieżki
:: Jeśli Twój folder z node nazywa się inaczej, zmień "node_portable" poniżej
set PATH=%CD%\node_portable;%PATH%

:: 2. Uruchomienie serwera Backend w osobnym oknie
:: ADMIN_TOKEN chroni panel administratora (przełączniki funkcji, np. trial/pelna wersja).
:: WAZNE: przy wystawieniu backendu na serwer dostepny dla innych uzytkownikow,
:: ustaw wlasny, tajny token ponizej (domyslny jest publicznie znany z kodu zrodlowego).
cd backend
set ADMIN_TOKEN=zmien-mnie-w-ADMIN_TOKEN
start "Serwer Obliczeniowy (Backend)" cmd /k "python -m uvicorn main:app --reload"

:: 3. Uruchomienie interfejsu Frontend
cd ..\frontend
echo Sprawdzanie bibliotek frontendu...
call npm install
echo Uruchamianie interfejsu...
npm run dev