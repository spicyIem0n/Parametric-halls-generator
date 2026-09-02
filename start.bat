@echo off
echo Inicjalizacja środowiska Hale Parametryczne...

:: 1. Dodanie przenośnego Node.js do ścieżki
:: Jeśli Twój folder z node nazywa się inaczej, zmień "node_portable" poniżej
set PATH=%CD%\node_portable;%PATH%

:: 2. Uruchomienie serwera Backend w osobnym oknie
cd backend
start "Serwer Obliczeniowy (Backend)" cmd /k "python -m uvicorn main:app --reload"

:: 3. Uruchomienie interfejsu Frontend
cd ..\frontend
echo Sprawdzanie bibliotek frontendu...
call npm install
echo Uruchamianie interfejsu...
npm run dev