@echo off
echo ===================================================
echo 🏗️ Start - Parametryczny Generator Hal Przemyslowych
echo ===================================================

echo [1/3] Uruchamianie serwera Backend (FastAPI)...
start "Backend - FastAPI" cmd /k "cd backend && uvicorn main:app --reload"

echo [2/3] Uruchamianie serwera Frontend (React)...
:: Jesli uzywasz Create React App, zamien "npm run dev" na "npm start"
start "Frontend - React" cmd /k "cd frontend && npm run dev"

echo [3/3] Oczekiwanie na inicjalizacje uslug (5 sekund)...
timeout /t 5 /nobreak > NUL

echo Otwieranie przegladarki...
:: Jesli uzywasz Create React App, zamien 5173 na 3000
start http://localhost:5173

echo ✅ Gotowe! Mozesz zaczac projektowac.