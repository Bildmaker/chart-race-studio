@echo off
chcp 65001 >nul
title chart-race-studio - Push zu GitHub
cd /d "%~dp0"
echo Pushe zu https://github.com/Bildmaker/chart-race-studio.git ...
git push origin main
echo.
echo Falls eine Meldung zu .git\config.lock erscheint: diese eine Datei loeschen und erneut versuchen.
pause
