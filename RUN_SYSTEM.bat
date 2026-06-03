@echo off
REM Real-time Highway Traffic Monitoring System Startup
REM ====================================================

setlocal enabledelayedexpansion

echo.
echo ========================================
echo Real-time Traffic Monitoring System
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo [INFO] Installing dependencies...
pip install -r requirements.txt --quiet

REM Run main.py
echo [INFO] Starting Traffic Monitoring System...
python main.py

pause
