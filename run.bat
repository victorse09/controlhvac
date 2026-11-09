@echo off
REM ============================================================
REM ControlHVAC - CMMS de Climatización
REM Script de ejecución para Windows
REM ============================================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"
set "REQUIREMENTS=%SCRIPT_DIR%requirements.txt"
set "PYTHON_MIN_MAJOR=3"
set "PYTHON_MIN_MINOR=10"

echo ============================================
echo   ControlHVAC - CMMS de Climatizacion
echo ============================================
echo.

REM --- 1. Check Python version ---
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no encontrado. Por favor instale Python %PYTHON_MIN_MAJOR%.%PYTHON_MIN_MINOR%+
    echo         Descargue desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set PYTHON_VERSION=%%i
for /f "tokens=*" %%i in ('python -c "import sys; print(sys.version_info.major)"') do set PY_MAJOR=%%i
for /f "tokens=*" %%i in ('python -c "import sys; print(sys.version_info.minor)"') do set PY_MINOR=%%i

if %PY_MAJOR% lss %PYTHON_MIN_MAJOR% (
    echo [ERROR] Python %PYTHON_VERSION% detectado. Se requiere Python %PYTHON_MIN_MAJOR%.%PYTHON_MIN_MINOR%+
    pause
    exit /b 1
)
if %PY_MAJOR% equ %PYTHON_MIN_MAJOR% (
    if %PY_MINOR% lss %PYTHON_MIN_MINOR% (
        echo [ERROR] Python %PYTHON_VERSION% detectado. Se requiere Python %PYTHON_MIN_MAJOR%.%PYTHON_MIN_MINOR%+
        pause
        exit /b 1
    )
)

echo [OK] Python %PYTHON_VERSION% detectado

REM --- 2. Create virtual environment if it doesn't exist ---
if not exist "%VENV_DIR%" (
    echo [INFO] Creando entorno virtual...
    python -m venv "%VENV_DIR%"
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual
        pause
        exit /b 1
    )
    echo [OK] Entorno virtual creado en %VENV_DIR%
) else (
    echo [OK] Entorno virtual encontrado
)

REM --- 3. Activate virtual environment ---
echo [INFO] Activando entorno virtual...
call "%VENV_DIR%\Scripts\activate.bat"
echo [OK] Entorno virtual activado

REM --- 4. Upgrade pip ---
echo [INFO] Actualizando pip...
python -m pip install --upgrade pip --quiet

REM --- 5. Install/update dependencies ---
if exist "%REQUIREMENTS%" (
    echo [INFO] Verificando dependencias...
    pip install -r "%REQUIREMENTS%" --quiet
    if %errorlevel% neq 0 (
        echo [ERROR] Error al instalar dependencias
        call deactivate
        pause
        exit /b 1
    )
    echo [OK] Dependencias instaladas/actualizadas
) else (
    echo [ERROR] Archivo requirements.txt no encontrado
    call deactivate
    pause
    exit /b 1
)

REM --- 6. Run the application ---
echo.
echo [INFO] Iniciando ControlHVAC...
echo ============================================
echo.

cd /d "%SCRIPT_DIR%"
python -m src.main

REM --- 7. Deactivate on exit ---
set EXIT_CODE=%errorlevel%
echo.
echo [INFO] Desactivando entorno virtual...
call deactivate
echo [OK] Aplicacion cerrada

if %EXIT_CODE% neq 0 (
    echo.
    echo [WARN] La aplicacion termino con codigo de error: %EXIT_CODE%
    pause
)

exit /b %EXIT_CODE%
