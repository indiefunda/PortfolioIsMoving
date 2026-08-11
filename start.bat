@echo off
REM PortfolioIsMoving - Setup launcher for Windows
REM Opens the local setup page in your browser.
title PortfolioIsMoving - Setup

cd /d "%~dp0"

REM Find Python
where python >nul 2>nul
if %errorlevel%==0 (
    set PY=python
) else (
    where py >nul 2>nul
    if %errorlevel%==0 (
        set PY=py
    ) else (
        echo.
        echo Python is not installed. Please install it from https://www.python.org/downloads/
        echo Make sure to tick "Add Python to PATH" during installation.
        echo.
        pause
        exit /b 1
    )
)

REM Make sure dependencies are installed
%PY% -c "import requests, pytz" >nul 2>nul
if %errorlevel% neq 0 (
    echo Installing required libraries (one time)...
    %PY% -m pip install --user requests pytz
)

echo.
echo Opening PortfolioIsMoving setup in your browser...
echo Close this window when you are done.
echo.
%PY% app.py
