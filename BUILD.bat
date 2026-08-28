@echo off
setlocal enabledelayedexpansion
title DealSite News Clipper - One-Click Build

REM ============================================================
REM  Single-file bootstrap: download -> setup -> obfuscate -> build
REM  Just double-click this file. Nothing else needs to be present.
REM ============================================================

set "WORK_DIR=%USERPROFILE%\Desktop\DealSiteBuild"
set "REPO_URL=https://github.com/wankyu4356/tallguy_productivity_for_others.git"
set "BRANCH=claude/adapt-deal-site-plus-FBPym"
set "ZIP_URL=https://github.com/wankyu4356/tallguy_productivity_for_others/archive/refs/heads/claude/adapt-deal-site-plus-FBPym.zip"
set "ZIP_DIR=tallguy_productivity_for_others-claude-adapt-deal-site-plus-FBPym"
set "OUT=%USERPROFILE%\Desktop\DealSiteNewsClipper.exe"

echo ============================================================
echo   DealSite News Clipper - One-Click Build
echo ============================================================
echo.

REM == 1. Python ==
echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 goto :install_python
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo        %%v
goto :python_ok

:install_python
echo        Python not found. Installing...
winget --version >nul 2>&1
if errorlevel 1 goto :python_curl
winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
if not errorlevel 1 goto :python_restart
:python_curl
echo        Downloading Python installer...
curl -L -o "%TEMP%\py_setup.exe" "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"
if errorlevel 1 goto :python_fail
"%TEMP%\py_setup.exe" /passive InstallAllUsers=0 PrependPath=1 Include_test=0
del "%TEMP%\py_setup.exe" >nul 2>&1
:python_restart
echo.
echo ============================================================
echo   Python installed. Please CLOSE this window and
echo   double-click BUILD.bat again.
echo ============================================================
pause
exit /b 0
:python_fail
echo [ERROR] Could not install Python automatically.
echo   Install Python 3.11+ from https://www.python.org/downloads/
echo   Check "Add Python to PATH" during setup, then run this again.
pause
exit /b 1
:python_ok

REM == 2. Download the project ==
echo.
echo [2/5] Downloading project...
git --version >nul 2>&1
if errorlevel 1 goto :zip_download
if exist "%WORK_DIR%\.git" goto :git_update

git clone -b %BRANCH% --single-branch --depth 1 "%REPO_URL%" "%WORK_DIR%"
if errorlevel 1 goto :zip_download
echo        Cloned to %WORK_DIR%
goto :have_repo

:git_update
echo        Updating existing copy...
cd /d "%WORK_DIR%"
git fetch origin %BRANCH% --depth 1 >nul 2>&1
git reset --hard origin/%BRANCH% >nul 2>&1
goto :have_repo

:zip_download
echo        Downloading ZIP...
if not exist "%WORK_DIR%" mkdir "%WORK_DIR%"
curl -L -o "%TEMP%\dealsite.zip" "%ZIP_URL%"
if errorlevel 1 goto :download_fail
powershell -NoProfile -Command "Expand-Archive -Path '%TEMP%\dealsite.zip' -DestinationPath '%TEMP%\dealsite_tmp' -Force"
if errorlevel 1 goto :download_fail
xcopy "%TEMP%\dealsite_tmp\%ZIP_DIR%\*" "%WORK_DIR%\" /E /Y /Q >nul
rd /s /q "%TEMP%\dealsite_tmp" >nul 2>&1
del "%TEMP%\dealsite.zip" >nul 2>&1
echo        Extracted to %WORK_DIR%

:have_repo
cd /d "%WORK_DIR%"
if not exist requirements.txt (
    echo [ERROR] Download looks incomplete - requirements.txt missing.
    echo   Delete "%WORK_DIR%" and run BUILD.bat again.
    pause
    exit /b 1
)

REM == 3. Dependencies ==
echo.
echo [3/5] Installing dependencies (first run takes a few minutes)...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if errorlevel 1 ( echo [ERROR] dependency install failed & pause & exit /b 1 )
python -m pip install pyinstaller pyarmor
if errorlevel 1 ( echo [ERROR] build-tool install failed & pause & exit /b 1 )

REM == 4. Obfuscate + build ==
echo.
echo [4/5] Obfuscating and building (5-10 minutes)...
set "OBF=%WORK_DIR%\build_obf"
if exist "%OBF%" rmdir /s /q "%OBF%"
if exist "%WORK_DIR%\build" rmdir /s /q "%WORK_DIR%\build"
if exist "%WORK_DIR%\dist" rmdir /s /q "%WORK_DIR%\dist"
mkdir "%OBF%"

python -m pyarmor.cli gen --recursive --output "%OBF%" "%WORK_DIR%\app" "%WORK_DIR%\launcher.py"
if errorlevel 1 ( echo [ERROR] obfuscation failed & pause & exit /b 1 )
xcopy "%WORK_DIR%\app\templates" "%OBF%\app\templates" /E /I /Y /Q >nul
xcopy "%WORK_DIR%\app\static"    "%OBF%\app\static"    /E /I /Y /Q >nul

set "DEALSITE_SRC_ROOT=%OBF%"
python -m PyInstaller dealsite.spec --noconfirm
if errorlevel 1 ( echo [ERROR] build failed - see messages above & pause & exit /b 1 )
rmdir /s /q "%OBF%"

REM == 5. Deliver ==
echo.
echo [5/5] Finishing...
if not exist "%WORK_DIR%\dist\DealSiteNewsClipper.exe" (
    echo [ERROR] build finished but exe not found.
    pause
    exit /b 1
)
copy /Y "%WORK_DIR%\dist\DealSiteNewsClipper.exe" "%OUT%" >nul

echo.
echo ============================================================
echo   Done!
echo.
echo   Your program is on the Desktop:
echo     DealSiteNewsClipper.exe
echo.
echo   Double-click it to run. Enter your Claude API key on the
echo   first screen. The Python source inside is encrypted.
echo ============================================================
echo.
echo Open the Desktop now? Press any key...
pause >nul
explorer "%USERPROFILE%\Desktop"
exit /b 0

:download_fail
echo [ERROR] Download failed. Check your internet connection and try again.
pause
exit /b 1
