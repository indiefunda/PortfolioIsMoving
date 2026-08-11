@echo off
REM ============================================================
REM  PortfolioIsMoving - Package a zip for your friends
REM
REM  Double-click this file. It creates a clean zip containing
REM  ONLY what your friends need (no secrets, no .git).
REM  The config is a clean starter (no pre-set tickers).
REM ============================================================
title PortfolioIsMoving - Make zip
cd /d "%~dp0"

echo.
echo ============================================
echo   PortfolioIsMoving - Make zip
echo ============================================
echo.

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd"') do set STAMP=%%i
set ZIPNAME=PortfolioIsMoving_%STAMP%.zip
set STAGE=%TEMP%\pim_zip_%STAMP%

REM Clean up any old staging folder / zip
if exist "%STAGE%" rmdir /s /q "%STAGE%"
if exist "%ZIPNAME%" del /f /q "%ZIPNAME%"

echo  Staging files...
mkdir "%STAGE%"
mkdir "%STAGE%\.github\workflows"
copy /y "app.py"            "%STAGE%\app.py"            >nul
copy /y "monitor.py"        "%STAGE%\monitor.py"        >nul
copy /y "start.bat"         "%STAGE%\start.bat"         >nul
copy /y "requirements.txt"  "%STAGE%\requirements.txt"  >nul
copy /y "README.md"         "%STAGE%\README.md"         >nul
copy /y ".github\workflows\monitor.yml"  "%STAGE%\.github\workflows\monitor.yml"  >nul

REM Write a clean starter config (no pre-set tickers) for the zip.
echo {"tickers": [], "threshold_pct": 5.0, "enabled": true, "provider": "finnhub"} > "%STAGE%\config_local.json"

echo  Creating %ZIPNAME% ...
powershell -NoProfile -Command "Compress-Archive -Path '%STAGE%\*' -DestinationPath '%ZIPNAME%' -Force"

if errorlevel 1 (
    echo.
    echo  [!] Something went wrong creating the zip.
    echo.
    pause
    exit /b 1
)

REM Clean up staging
rmdir /s /q "%STAGE%"

echo.
echo  [OK] Created: %ZIPNAME%
echo.
echo  This zip contains ONLY what your friends need:
echo    - start.bat           (double-click to start)
echo    - app.py, monitor.py  (the app)
echo    - requirements.txt    (dependencies)
echo    - README.md           (step-by-step guide)
echo    - config_local.json   (clean starter, no tickers)
echo    - .github\workflows\monitor.yml  (for the free 24/7 cloud monitor)
echo.
echo  It does NOT contain secrets or the .git folder.
echo  Give this zip to a friend. They unzip, run start.bat,
echo  and follow the guide in README.md.
echo.
pause
