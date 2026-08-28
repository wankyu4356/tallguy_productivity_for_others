@echo off
setlocal
title DealSite News Clipper - Secure Build

set "ROOT=%~dp0"
set "OBF=%ROOT%build_obf"

echo ============================================================
echo   DealSite News Clipper - Secure Build (obfuscated)
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.11+ and add it to PATH.
    pause
    exit /b 1
)

echo [1/5] Installing dependencies...
python -m pip install -q -r requirements.txt
python -m pip install -q pyinstaller pyarmor
if errorlevel 1 ( echo [ERROR] dependency install failed & pause & exit /b 1 )

echo [2/5] Cleaning previous output...
if exist "%OBF%" rmdir /s /q "%OBF%"
if exist "%ROOT%build" rmdir /s /q "%ROOT%build"
if exist "%ROOT%dist" rmdir /s /q "%ROOT%dist"
mkdir "%OBF%"

echo [3/5] Obfuscating Python sources...
python -m pyarmor.cli gen --recursive --output "%OBF%" "%ROOT%app" "%ROOT%launcher.py"
if errorlevel 1 ( echo [ERROR] obfuscation failed & pause & exit /b 1 )
xcopy "%ROOT%app\templates" "%OBF%\app\templates" /E /I /Y /Q >nul
xcopy "%ROOT%app\static"    "%OBF%\app\static"    /E /I /Y /Q >nul

echo [4/5] Building executable...
set "DEALSITE_SRC_ROOT=%OBF%"
python -m PyInstaller dealsite.spec --noconfirm
if errorlevel 1 ( echo [ERROR] build failed & pause & exit /b 1 )

echo [5/5] Cleaning up...
rmdir /s /q "%OBF%"

echo.
echo ============================================================
echo   Secure build complete: dist\DealSiteNewsClipper.exe
echo   Python sources are encrypted - decompiling won't reveal logic.
echo ============================================================
pause
