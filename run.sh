#!/usr/bin/env bash

set -euo pipefail

# PATHS
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
PYTHON_BIN="python3"
REQUIRED_PACKAGES="streamlit sqlalchemy pandas reportlab plotly"

# COLOURS
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
RESET="\033[0m"

log()  { echo -e "${GREEN}[run]${RESET} $*"; }
warn() { echo -e "${YELLOW}[warn]${RESET} $*"; }
die()  { echo -e "${RED}[error]${RESET} $*" >&2; exit 1; }

# Python Version Check
log "Checking for Python 3..."
if ! command -v "$PYTHON_BIN" &>/dev/null; then
    die "python3 not found. Install Python 3.10 or later and try again."
fi

PYTHON_VERSION=$("$PYTHON_BIN" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [[ "$PYTHON_MAJOR" -lt 3 ]] || [[ "$PYTHON_MAJOR" -eq 3 && "$PYTHON_MINOR" -lt 10 ]]; then
    die "Python 3.10+ required. Found $PYTHON_VERSION."
fi
log "Python $PYTHON_VERSION found."

# Create venv, if missing
if [[ ! -d "$VENV_DIR" ]]; then
    log "Creating virtual environment at $VENV_DIR..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    log "Virtual environment created."
else
    log "Virtual environment already exists, skipping creation."
fi

# Activate venv
log "Activating virtual environment..."
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

# Check and upgrade pip
log "Checking pip..."
"$VENV_PIP" install --upgrade pip --quiet

# Install missing packages
log "Checking required packages..."
MISSING=""
for pkg in $REQUIRED_PACKAGES; do
    # Use the importable name (strip version specifiers if any)
    import_name=$(echo "$pkg" | cut -d'[' -f1 | cut -d'=' -f1 | cut -d'>' -f1 | cut -d'<' -f1)
    if ! "$VENV_PYTHON" -c "import $import_name" &>/dev/null 2>&1; then
        MISSING="$MISSING $pkg"
    fi
done

if [[ -n "$MISSING" ]]; then
    log "Installing:$MISSING"
    "$VENV_PIP" install $MISSING --quiet
    log "Packages installed."
else
    log "All packages already installed."
fi

# Create required directories, if missing
for dir in data reports; do
    if [[ ! -d "$SCRIPT_DIR/$dir" ]]; then
        mkdir -p "$SCRIPT_DIR/$dir"
        log "Created missing directory: $dir/"
    fi
done

# Run the app
log "Starting Tuition Manager..."
echo ""
cd "$SCRIPT_DIR"
exec "$VENV_DIR/bin/streamlit" run app.py "$@"