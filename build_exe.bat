@echo off
REM Build PortfolioIsMoving into a single .exe file (for non-developers).
REM Run this on Windows after installing Python + pyinstaller:
REM   pip install pyinstaller
REM Then double-click this file. The .exe will appear in the dist\ folder.

cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python not found. Install it from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Installing pyinstaller (one time)...
python -m pip install --user pyinstaller

echo.
echo Building PortfolioIsMoving.exe ...
python -m PyInstaller --noconfirm --onefile --name PortfolioIsMoving app.py

echo.
echo Done! Your app is at: dist\PortfolioIsMoving.exe
echo Send that single .exe file to your friends. They just double-click it.
echo.
pause
