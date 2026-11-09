#!/bin/bash
# ============================================================
# ControlHVAC - CMMS de Climatización
# Script de ejecución para Linux/macOS
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
REQUIREMENTS="$SCRIPT_DIR/requirements.txt"
PYTHON_MIN_VERSION="3.10"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  ControlHVAC - CMMS de Climatización${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# --- 1. Check Python version ---
PYTHON_CMD=""
# If venv already exists and specifies an executable in pyvenv.cfg, prefer it
if [ -f "$VENV_DIR/pyvenv.cfg" ]; then
    CFG_EXEC=$(grep -E '^executable\s*=' "$VENV_DIR/pyvenv.cfg" | sed -E 's/^executable\s*=\s*//')
    if [ -n "$CFG_EXEC" ] && [ -x "$CFG_EXEC" ]; then
        PYTHON_CMD="$CFG_EXEC"
        # Repair broken symlinks when system /usr/bin/python3 upgrades minor version
        if [ -L "$VENV_DIR/bin/python3" ]; then
            CURRENT_TARGET=$(readlink -f "$VENV_DIR/bin/python3" 2>/dev/null || true)
            CFG_TARGET=$(readlink -f "$CFG_EXEC" 2>/dev/null || true)
            if [ -n "$CFG_TARGET" ] && [ "$CURRENT_TARGET" != "$CFG_TARGET" ]; then
                echo -e "${YELLOW}[INFO] Reparando enlaces del entorno virtual hacia $CFG_EXEC...${NC}"
                PY_BASENAME=$(basename "$CFG_EXEC")
                ln -sf "$CFG_EXEC" "$VENV_DIR/bin/$PY_BASENAME"
                ln -sf "$PY_BASENAME" "$VENV_DIR/bin/python3"
                ln -sf "$PY_BASENAME" "$VENV_DIR/bin/python"
            fi
        fi
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}[ERROR] Python no encontrado. Por favor instale Python ${PYTHON_MIN_VERSION}+${NC}"
        exit 1
    fi
fi

PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.major)")
PY_MINOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.minor)")

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    echo -e "${RED}[ERROR] Python ${PYTHON_VERSION} detectado. Se requiere Python ${PYTHON_MIN_VERSION}+${NC}"
    exit 1
fi

echo -e "${GREEN}[OK] Python ${PYTHON_VERSION} detectado ($PYTHON_CMD)${NC}"

# --- 2. Create virtual environment if it doesn't exist ---
if [ ! -f "$VENV_DIR/bin/activate" ] && [ ! -f "$VENV_DIR/Scripts/activate" ]; then
    echo -e "${YELLOW}[INFO] Creando entorno virtual...${NC}"
    if ! "$PYTHON_CMD" -m venv "$VENV_DIR"; then
        echo -e "${RED}[ERROR] No se pudo crear el entorno virtual. Asegúrese de tener instalado python3-venv${NC}"
        exit 1
    fi
    echo -e "${GREEN}[OK] Entorno virtual creado en $VENV_DIR${NC}"
else
    echo -e "${GREEN}[OK] Entorno virtual encontrado${NC}"
fi

# --- 3. Activate virtual environment ---
echo -e "${YELLOW}[INFO] Activando entorno virtual...${NC}"
if [ -f "$VENV_DIR/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
elif [ -f "$VENV_DIR/Scripts/activate" ]; then
    # shellcheck disable=SC1091
    source "$VENV_DIR/Scripts/activate"
else
    echo -e "${RED}[ERROR] No se encontró el script de activación del entorno virtual${NC}"
    exit 1
fi
echo -e "${GREEN}[OK] Entorno virtual activado${NC}"

# --- 4. Verify/Bootstrap pip and dependencies ---
if ! python -m pip --version &> /dev/null; then
    echo -e "${YELLOW}[INFO] Inicializando pip en el entorno virtual...${NC}"
    python -m ensurepip --upgrade &> /dev/null || true
fi

# Check if required packages are already importable to avoid failing or waiting when offline
if python -c "import PySide6, reportlab, openpyxl, matplotlib" &> /dev/null; then
    echo -e "${GREEN}[OK] Dependencias verificadas en el entorno virtual${NC}"
else
    echo -e "${YELLOW}[INFO] Actualizando pip...${NC}"
    python -m pip install --upgrade pip --quiet 2>/dev/null || true

    # --- 5. Install/update dependencies ---
    if [ -f "$REQUIREMENTS" ]; then
        echo -e "${YELLOW}[INFO] Verificando e instalando dependencias desde requirements.txt...${NC}"
        if ! python -m pip install -r "$REQUIREMENTS" --quiet; then
            echo -e "${RED}[ERROR] Error al instalar dependencias${NC}"
            deactivate 2>/dev/null || true
            exit 1
        fi
        echo -e "${GREEN}[OK] Dependencias instaladas/actualizadas${NC}"
    else
        echo -e "${RED}[ERROR] Archivo requirements.txt no encontrado${NC}"
        deactivate 2>/dev/null || true
        exit 1
    fi
fi

# --- 6. Run the application ---
echo ""
echo -e "${BLUE}[INFO] Iniciando ControlHVAC...${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

cd "$SCRIPT_DIR" || exit 1
export QT_LOGGING_RULES="kf.iconthemes.debug=false;kf.iconthemes.warning=false"
python -m src.main
EXIT_CODE=$?

# --- 7. Deactivate on exit ---
echo ""
echo -e "${YELLOW}[INFO] Desactivando entorno virtual...${NC}"
deactivate 2>/dev/null || true
echo -e "${GREEN}[OK] Aplicación cerrada${NC}"

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo -e "${YELLOW}[WARN] La aplicación terminó con código de error: $EXIT_CODE${NC}"
fi

exit $EXIT_CODE
