@echo off
setlocal EnableDelayedExpansion

:: ============================================================
:: run.bat -- Tuition Manager launcher for Windows
:: Same behaviour as run.sh on Linux.
:: Double-click this file or run it from a terminal.
:: ============================================================

set SCRIPT_DIR=%~dp0
set VENV_DIR=%SCRIPT_DIR%venv
set VENV_PYTHON=%VENV_DIR%\Scripts\python.exe
set VENV_PIP=%VENV_DIR%\Scripts\pip.exe
set VENV_STREAMLIT=%VENV_DIR%\Scripts\streamlit.exe
set PACKAGES=streamlit sqlalchemy pandas reportlab plotly

echo.
echo ============================================================
echo   Tuition Manager
echo ============================================================

::Python Version Check
echo.
echo [1/5] Checking for Python 3.10+...

where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: python not found in PATH.
    echo  Download and install Python 3.10+ from https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=1,2 delims=." %%a in ('python -c "import sys; print(str(sys.version_info.major)+'.'+str(sys.version_info.minor))"') do (
    set PY_MAJOR=%%a
    set PY_MINOR=%%b
)

if !PY_MAJOR! LSS 3 (
    echo  ERROR: Python 3.10+ required. Found !PY_MAJOR!.!PY_MINOR!.
    pause
    exit /b 1
)
if !PY_MAJOR! EQU 3 if !PY_MINOR! LSS 10 (
    echo  ERROR: Python 3.10+ required. Found !PY_MAJOR!.!PY_MINOR!.
    pause
    exit /b 1
)

echo  Python !PY_MAJOR!.!PY_MINOR! found.

:: Create venv if missing
echo.
echo [2/5] Checking virtual environment...

if not exist "%VENV_DIR%\" (
    echo  Creating virtual environment...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo  ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo  Virtual environment created.
) else (
    echo  Virtual environment already exists, skipping.
)

:: Upgrade pip
echo.
echo [3/5] Checking pip...
"%VENV_PIP%" install --upgrade pip --quiet
echo  pip is up to date.

:: Install Missing Packages
echo.
echo [4/5] Checking required packages...

@REM set MISSING=
@REM for %%p in (%PACKAGES%) do (
@REM     "%VENV_PYTHON%" -c "import %%p" >nul 2>&1
@REM     if errorlevel 1 (
@REM         set MISSING=!MISSING! %%p
@REM     )
@REM )

@REM if "!MISSING!"=="" (
@REM     echo  All packages already installed.
@REM ) else (
@REM     echo  Installing:!MISSING!
@REM     "%VENV_PIP%" install !MISSING! --quiet
@REM     if errorlevel 1 (
@REM         echo  ERROR: Package installation failed.
@REM         pause
@REM         exit /b 1
@REM     )
@REM     echo  Packages installed.
@REM )

"%VENV_PIP%" install -r requirements.txt 

:: Create missing Directories
echo.
echo [5/5] Checking directories...

if not exist "%SCRIPT_DIR%data\" (
    mkdir "%SCRIPT_DIR%data"
    echo  Created: data\
)
if not exist "%SCRIPT_DIR%reports\" (
    mkdir "%SCRIPT_DIR%reports"
    echo  Created: reports\
)
echo  Directories ready.

:: Launch
echo.
echo ============================================================
echo   Starting Tuition Manager at http://localhost:8501
echo   Press Ctrl+C to stop the server.
echo ============================================================
echo.

cd /d "%SCRIPT_DIR%"
"%VENV_STREAMLIT%" run app.py