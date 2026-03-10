@echo off
setlocal enabledelayedexpansion
title DealSitePlus News Clipper

echo ============================================
echo   DealSitePlus News Clipper - Auto Setup
echo ============================================
echo.

REM == Work in user's Desktop\DealSitePlus folder ==
set "WORK_DIR=%USERPROFILE%\Desktop\DealSitePlus"

REM == 1. Check Python ==
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 goto :install_python
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo        %%v found
goto :python_ok

:install_python
echo        Python not found. Installing...
echo.
winget --version >nul 2>&1
if errorlevel 1 goto :install_python_curl
echo        Installing via winget...
winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
if not errorlevel 1 goto :python_restart
:install_python_curl
echo        Downloading Python installer...
curl -L -o "%TEMP%\python_setup.exe" "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"
if errorlevel 1 goto :python_fail
echo        Installing Python...
"%TEMP%\python_setup.exe" /passive InstallAllUsers=0 PrependPath=1 Include_test=0
del "%TEMP%\python_setup.exe" >nul 2>&1
:python_restart
echo.
echo ============================================
echo   Python installed!
echo   Close this window, then double-click
echo   this bat file again.
echo ============================================
pause
exit /b 0
:python_fail
echo.
echo [ERROR] Could not install Python.
echo   Go to https://www.python.org/downloads/
echo   Download and install Python 3.12
echo   CHECK "Add Python to PATH"
echo   Then run this file again.
pause
exit /b 1
:python_ok

REM == 2. pip ==
echo [2/6] Checking pip...
python -m pip --version >nul 2>&1
if errorlevel 1 python -m ensurepip --upgrade >nul 2>&1
python -m pip install --upgrade pip >nul 2>&1
echo        OK

REM == 3. Download project ==
echo [3/6] Downloading project files...
if exist "%WORK_DIR%\app\main.py" (
    echo        Already downloaded - skipping
    goto :download_done
)
echo        Downloading from GitHub...
if not exist "%WORK_DIR%" mkdir "%WORK_DIR%"
curl -L -o "%TEMP%\dealsiteplus.zip" "https://github.com/wankyu4356/tallguy_productivity_for_others/archive/refs/heads/claude/adapt-deal-site-plus-FBPym.zip"
if errorlevel 1 goto :download_fail
echo        Extracting...
powershell -Command "Expand-Archive -Path '%TEMP%\dealsiteplus.zip' -DestinationPath '%TEMP%\dealsiteplus_tmp' -Force"
if errorlevel 1 goto :download_fail
xcopy "%TEMP%\dealsiteplus_tmp\tallguy_productivity_for_others-claude-adapt-deal-site-plus-FBPym\*" "%WORK_DIR%\" /E /Y /Q >nul
rd /s /q "%TEMP%\dealsiteplus_tmp" >nul 2>&1
del "%TEMP%\dealsiteplus.zip" >nul 2>&1
echo        Downloaded to %WORK_DIR%
:download_done
cd /d "%WORK_DIR%"

REM == 4. Install packages ==
echo [4/6] Installing packages...
python -m pip install fastapi "uvicorn[standard]" jinja2 python-multipart selenium anthropic pypdf reportlab python-docx holidays python-dateutil pydantic-settings aiofiles python-dotenv httpx tzdata beautifulsoup4 >nul 2>&1
if errorlevel 1 (
    echo        Retrying with output...
    python -m pip install fastapi "uvicorn[standard]" jinja2 python-multipart selenium anthropic pypdf reportlab python-docx holidays python-dateutil pydantic-settings aiofiles python-dotenv httpx tzdata beautifulsoup4
)
echo        OK

REM == 5. Setup .env ==
echo [5/6] Setting up config...
if exist .env goto :env_exists
echo.
echo   First time setup - enter your credentials:
echo.
set /p "DS_ID=  DealSitePlus ID: "
set /p "DS_PW=  DealSitePlus Password: "
set /p "API_KEY=  Anthropic API Key (sk-ant-...): "
echo DEALSITEPLUS_ID=!DS_ID!> .env
echo DEALSITEPLUS_PW=!DS_PW!>> .env
echo ANTHROPIC_API_KEY=!API_KEY!>> .env
echo CLAUDE_MODEL=claude-sonnet-4-20250514>> .env
echo OUTPUT_DIR=./output>> .env
echo LOG_LEVEL=INFO>> .env
echo HOST=0.0.0.0>> .env
echo PORT=8000>> .env
echo BROWSER_HEADLESS=true>> .env
echo CRAWL_TIMEOUT_MS=30000>> .env
echo NAVIGATION_TIMEOUT_MS=15000>> .env
echo MAX_CONCURRENT_PAGES=3>> .env
echo CLEANUP_HOURS=24>> .env
echo.
echo        Config saved
goto :env_done
:env_exists
echo        Config already exists
:env_done

REM == 6. Run ==
echo [6/6] Starting server...
echo.
echo ============================================
echo   Browser will open automatically.
echo   If not, go to http://localhost:8000
echo   To stop: close this window or Ctrl+C
echo ============================================
echo.
start http://localhost:8000
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
echo.
echo Server stopped.
pause

:download_fail
echo.
echo [ERROR] Download failed. Check your internet connection.
pause
exit /b 1
