@echo off
chcp 65001 >nul
title ChartRace Studio
where py >nul 2>nul
if %errorlevel%==0 (set PY=py) else (set PY=python)
cd /d "%~dp0"
%PY% chartrace_studio.py
if %errorlevel% neq 0 (
  echo.
  echo Es ist ein Fehler aufgetreten. Hast du install.bat ausgefuehrt?
  pause
)
