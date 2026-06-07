@echo off
chcp 65001 >nul
title ChartRace Studio
cd /d "%~dp0"
where py >nul 2>nul && (set PY=py) || (set PY=python)
%PY% -c "import yfinance, matplotlib, numpy, imageio_ffmpeg" 1>nul 2>nul
if errorlevel 1 (
  echo Installiere fehlende Pakete in dieses Python ... (einmalig)
  %PY% -m pip install -r requirements.txt
)
%PY% chartrace_studio.py
if errorlevel 1 (
  echo.
  echo Es ist ein Fehler aufgetreten. Bitte Meldung oben pruefen.
  pause
)
