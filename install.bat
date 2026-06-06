@echo off
chcp 65001 >nul
title ChartRace Studio - Installation
echo ============================================
echo   ChartRace Studio - Abhaengigkeiten
echo ============================================
echo.
where py >nul 2>nul
if %errorlevel%==0 (set PY=py) else (set PY=python)
echo Verwende: %PY%
%PY% -m pip install --upgrade pip
%PY% -m pip install -r "%~dp0requirements.txt"
echo.
if %errorlevel%==0 (echo Fertig! Du kannst jetzt start.bat doppelklicken.) else (echo FEHLER bei der Installation - siehe Meldungen oben.)
echo.
pause
