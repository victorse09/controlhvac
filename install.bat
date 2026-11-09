@echo off
chcp 65001 > nul
title Instalador de ControlHVAC
echo ========================================================
echo          Instalador de ControlHVAC para Windows        
echo ========================================================
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
echo.
echo Presiona cualquier tecla para salir...
pause > nul
