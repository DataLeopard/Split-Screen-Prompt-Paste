@echo off
echo ============================================
echo  Split Screen Prompt Paste - Setup
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo Setup complete! Run the app with:
echo   python app.py
echo.
echo Or double-click  start.bat  /  stop.bat
pause
