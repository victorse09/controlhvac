@echo off
chcp 65001 > nul
title Instalador de ControlHVAC
powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0installer_gui.ps1"
