@echo off
REM ============================================================
REM  PortfolioIsMoving - Setup Launcher (Windows)
REM
REM  Double-click this file. It will:
REM    1. Check Python is installed
REM    2. Install the small libraries it needs (one time)
REM    3. Open the setup screen in your browser
REM
REM  You only need this once to configure your portfolio.
REM  After that, monitoring runs free in the cloud 24/7.
REM ============================================================
title PortfolioIsMoving - Setup
cd /d "%~dp0"

echo.
echo ============================================
echo   PortfolioIsMoving - Setup
echo ============================================
echo.

REM ---------------------------------------------------------
REM  Step 1: Find Python
REM ---------------------------------------------------------
set "PY="

where python >nul 2>nul
if %errorlevel%==0 goto found_python

where py >nul 2>nul
if %errorlevel%==0 goto found_py

goto no_python

:found_python
set "PY=python"
goto python_ok

:found_py
set "PY=py"
goto python_ok

:no_python
echo  [!] Python is not installed or not on PATH.
echo.
echo  Please install it first:
echo    1. Go to  https://www.python.org/downloads/
echo    2. Click the yellow "Download Python" button
echo    3. Open the downloaded file
echo    4. IMPORTANT: tick "Add Python to PATH" at the bottom
echo    5. Click "Install Now"
echo.
echo  Then double-click this file again.
echo.
pause
exit /b 1

:python_ok
echo  [OK] Python found: %PY%
echo.

REM ---------------------------------------------------------
REM  Step 2: Check / install required libraries (one time)
REM ---------------------------------------------------------
%PY% -c "import requests, pytz" >nul 2>nul
if %errorlevel%==0 goto deps_ok

echo  Installing two small libraries (requests, pytz)...
echo  This happens once and takes a few seconds.
echo.
%PY% -m pip install --user requests pytz
if %errorlevel%==0 goto deps_ok

echo.
echo  [!] Could not install libraries. Check your internet
echo      connection and try again.
echo.
pause
exit /b 1

:deps_ok
echo  [OK] Libraries already installed.
echo.

REM ---------------------------------------------------------
REM  Step 3: Launch the setup screen
REM ---------------------------------------------------------
echo  Opening the setup screen in your browser...
echo  (If it does not open, go to  http://localhost:8000 )
echo.
echo  When you are done, close this window.
echo.
%PY% app.py
