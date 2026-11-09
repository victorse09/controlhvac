param (
    [string]$InstallPath = "$env:LOCALAPPDATA\Programs\ControlHVAC"
)

$ErrorActionPreference = "Stop"
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "   Instalador de ControlHVAC para Windows    " -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$SourceDir = Join-Path $ScriptDir "ControlHVAC"

if (-not (Test-Path $SourceDir)) {
    $SourceDir = Join-Path $ScriptDir "dist\ControlHVAC"
}

if (-not (Test-Path $SourceDir)) {
    Write-Error "No se encontraron los archivos compilados en $SourceDir"
    exit 1
}

Write-Host "[1/3] Copiando archivos a $InstallPath..." -ForegroundColor Yellow
if (-not (Test-Path $InstallPath)) {
    New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
}

Copy-Item -Path "$SourceDir\*" -Destination $InstallPath -Recurse -Force

Write-Host "[2/3] Creando accesos directos..." -ForegroundColor Yellow
$WshShell = New-Object -ComObject WScript.Shell

# Desktop shortcut
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$DesktopShortcut = $WshShell.CreateShortcut((Join-Path $DesktopPath "ControlHVAC.lnk"))
$DesktopShortcut.TargetPath = (Join-Path $InstallPath "ControlHVAC.exe")
$DesktopShortcut.WorkingDirectory = $InstallPath
$DesktopShortcut.IconLocation = (Join-Path $InstallPath "assets\icons\app_icon.ico")
$DesktopShortcut.Description = "ControlHVAC - Sistema CMMS de Climatización"
$DesktopShortcut.Save()

# Start Menu shortcut
$StartMenuPrograms = [Environment]::GetFolderPath("Programs")
$AppStartMenuDir = Join-Path $StartMenuPrograms "ControlHVAC"
if (-not (Test-Path $AppStartMenuDir)) {
    New-Item -ItemType Directory -Path $AppStartMenuDir -Force | Out-Null
}
$StartShortcut = $WshShell.CreateShortcut((Join-Path $AppStartMenuDir "ControlHVAC.lnk"))
$StartShortcut.TargetPath = (Join-Path $InstallPath "ControlHVAC.exe")
$StartShortcut.WorkingDirectory = $InstallPath
$StartShortcut.IconLocation = (Join-Path $InstallPath "assets\icons\app_icon.ico")
$StartShortcut.Description = "ControlHVAC - Sistema CMMS de Climatización"
$StartShortcut.Save()

Write-Host "[3/3] Instalación completada con éxito!" -ForegroundColor Green
Write-Host ""
Write-Host "Puedes abrir ControlHVAC desde tu Escritorio o el Menú Inicio." -ForegroundColor Cyan
Write-Host "Ruta instalada: $InstallPath" -ForegroundColor Gray
Write-Host ""
