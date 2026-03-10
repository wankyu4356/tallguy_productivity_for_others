@echo off
setlocal enabledelayedexpansion
title DealSitePlus News Clipper - Setup and Run

echo ============================================
echo   DealSitePlus News Clipper - Setup and Run
echo ============================================
echo.

REM == 1. Check Python ==
echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 goto :no_python
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo        %%v found
goto :python_ok

:no_python
echo        Python not found. Trying to install...
echo.
winget --version >nul 2>&1
if errorlevel 1 goto :no_winget
echo        Installing Python via winget...
winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
echo.
echo [!!] Python installed. Close this window and run setup_and_run.bat again.
echo.
pause
exit /b 0

:no_winget
echo        winget not available. Downloading Python installer...
curl -L -o "%TEMP%\python_installer.exe" "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"
if errorlevel 1 goto :python_fail
echo        Running Python installer...
"%TEMP%\python_installer.exe" /passive InstallAllUsers=0 PrependPath=1 Include_test=0
del "%TEMP%\python_installer.exe" >nul 2>&1
echo.
echo [!!] Python installed. Close this window and run setup_and_run.bat again.
echo.
pause
exit /b 0

:python_fail
echo.
echo [ERROR] Python auto-install failed.
echo.
echo   1. Go to https://www.python.org/downloads/
echo   2. Download Python 3.12
echo   3. CHECK "Add Python to PATH" during install
echo   4. Run this file again
echo.
pause
exit /b 1

:python_ok

REM == 2. Check pip ==
echo.
echo [2/5] Checking pip...
python -m pip --version >nul 2>&1
if errorlevel 1 python -m ensurepip --upgrade >nul 2>&1
python -m pip install --upgrade pip >nul 2>&1
echo        pip OK

REM == 3. Install packages ==
echo.
echo [3/5] Installing Python packages...
python -m pip install -r requirements.txt
if errorlevel 1 goto :pip_fail
echo        Packages installed
goto :pip_ok

:pip_fail
echo.
echo [ERROR] Package install failed.
pause
exit /b 1

:pip_ok

REM == 4. Setup .env ==
echo.
echo [4/5] Checking .env config...
if exist .env (
    echo        .env exists - keeping current settings
    goto :env_done
)
echo.
echo   .env not found. Enter your credentials:
echo.
set /p "DS_ID=  DealSitePlus ID: "
set /p "DS_PW=  DealSitePlus Password: "
set /p "API_KEY=  Anthropic API Key: "
echo # DealSitePlus credentials> .env
echo DEALSITEPLUS_ID=!DS_ID!>> .env
echo DEALSITEPLUS_PW=!DS_PW!>> .env
echo.>> .env
echo # Claude API>> .env
echo ANTHROPIC_API_KEY=!API_KEY!>> .env
echo CLAUDE_MODEL=claude-sonnet-4-20250514>> .env
echo.>> .env
echo # App settings>> .env
echo OUTPUT_DIR=./output>> .env
echo LOG_LEVEL=INFO>> .env
echo HOST=0.0.0.0>> .env
echo PORT=8000>> .env
echo.>> .env
echo # Browser settings>> .env
echo BROWSER_HEADLESS=true>> .env
echo CRAWL_TIMEOUT_MS=30000>> .env
echo NAVIGATION_TIMEOUT_MS=15000>> .env
echo MAX_CONCURRENT_PAGES=3>> .env
echo.>> .env
echo # Cleanup>> .env
echo CLEANUP_HOURS=24>> .env
echo.
echo        .env created

:env_done

REM == 5. Start server ==
echo.
echo [5/5] Starting server...
echo.
echo ============================================
echo   Open http://localhost:8000 in your browser
echo   Press Ctrl+C to stop the server
echo ============================================
echo.
start http://localhost:8000
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
echo.
echo Server stopped.
pause
