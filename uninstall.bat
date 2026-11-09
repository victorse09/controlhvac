@echo off
chcp 65001 > nul
title Desinstalador de ControlHVAC
echo ========================================================
echo        Desinstalador de ControlHVAC para Windows       
echo ========================================================
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall.ps1"
echo.
echo Presiona cualquier tecla para salir...
pause > nul
