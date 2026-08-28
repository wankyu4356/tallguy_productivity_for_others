@echo off
setlocal
title DealSite News Clipper - Build

echo ============================================================
echo   DealSite News Clipper - Build (standard)
echo ============================================================
echo.

REM == 1. Python check ==
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo   Install Python 3.11+ from https://www.python.org/downloads/
    echo   and check "Add Python to PATH" during setup.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo   %%v

echo.
echo [1/3] Installing dependencies (first run takes a few minutes)...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if errorlevel 1 ( echo [ERROR] dependency install failed & pause & exit /b 1 )
python -m pip install pyinstaller
if errorlevel 1 ( echo [ERROR] PyInstaller install failed & pause & exit /b 1 )

echo.
echo [2/3] Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo [3/3] Building (5-10 minutes)...
python -m PyInstaller dealsite.spec --noconfirm
if errorlevel 1 ( echo. & echo [ERROR] build failed - see messages above & pause & exit /b 1 )

echo.
echo ============================================================
echo   Build complete
echo ============================================================
echo.
echo   Executable: dist\DealSiteNewsClipper.exe
echo.
echo   How to use:
echo     1) copy dist\DealSiteNewsClipper.exe anywhere you like
echo     2) double-click it - the browser opens automatically
echo     3) enter your Claude API key on the first screen
echo.
pause
