$ErrorActionPreference = "Stop"
Write-Host "==============================================" -ForegroundColor Yellow
Write-Host "   Desinstalador de ControlHVAC para Windows  " -ForegroundColor Yellow
Write-Host "==============================================" -ForegroundColor Yellow
Write-Host ""

$InstallPath = "$env:LOCALAPPDATA\Programs\ControlHVAC"
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$DesktopShortcut = Join-Path $DesktopPath "ControlHVAC.lnk"
$StartMenuPrograms = [Environment]::GetFolderPath("Programs")
$AppStartMenuDir = Join-Path $StartMenuPrograms "ControlHVAC"

if (Test-Path $DesktopShortcut) {
    Remove-Item $DesktopShortcut -Force
    Write-Host "Acceso directo de escritorio eliminado." -ForegroundColor Gray
}

if (Test-Path $AppStartMenuDir) {
    Remove-Item $AppStartMenuDir -Recurse -Force
    Write-Host "Acceso de Menú Inicio eliminado." -ForegroundColor Gray
}

if (Test-Path $InstallPath) {
    Remove-Item $InstallPath -Recurse -Force
    Write-Host "Archivos de la aplicación eliminados." -ForegroundColor Gray
}

Write-Host "Desinstalación finalizada con éxito." -ForegroundColor Green
