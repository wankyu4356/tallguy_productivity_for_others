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
if exist "%WORK_DIR%\app\main.py" goto :already_downloaded
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
goto :download_done
:already_downloaded
echo        Already downloaded - skipping
:download_done
cd /d "%WORK_DIR%"

REM == 4. Install packages ==
echo [4/6] Installing packages...
python -m pip install fastapi "uvicorn[standard]" jinja2 python-multipart selenium anthropic pypdf reportlab python-docx holidays python-dateutil pydantic-settings aiofiles python-dotenv httpx tzdata beautifulsoup4 >nul 2>&1
if errorlevel 1 goto :pip_fail
echo        OK
goto :pip_ok
:pip_fail
echo        Retrying...
python -m pip install fastapi "uvicorn[standard]" jinja2 python-multipart selenium anthropic pypdf reportlab python-docx holidays python-dateutil pydantic-settings aiofiles python-dotenv httpx tzdata beautifulsoup4
:pip_ok

REM == 5. Setup .env ==
echo [5/6] Setting up config...
if exist .env goto :env_check

echo.
echo   ============================================
echo   First time setup!
echo   ============================================
echo.
echo   A settings file will now open in Notepad.
echo.
echo   You need to change 3 things:
echo.
echo     Line 1: DEALSITEPLUS_ID
echo       = your DealSitePlus login ID
echo.
echo     Line 2: DEALSITEPLUS_PW
echo       = your DealSitePlus password
echo.
echo     Line 3: ANTHROPIC_API_KEY
echo       = your Claude API key (starts with sk-ant-...)
echo.
echo   ============================================
echo   HOW TO SAVE:
echo     1. Change YOUR_ID_HERE to your real ID
echo     2. Change YOUR_PW_HERE to your real password
echo     3. Change YOUR_API_KEY_HERE to your real key
echo     4. Press Ctrl+S to save
echo     5. Close Notepad (click X)
echo   ============================================
echo.

echo DEALSITEPLUS_ID=YOUR_ID_HERE> .env
echo DEALSITEPLUS_PW=YOUR_PW_HERE>> .env
echo ANTHROPIC_API_KEY=YOUR_API_KEY_HERE>> .env
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

echo   Opening Notepad now...
echo.
notepad .env
echo.
echo   ============================================
echo   Did you:
echo     - Change YOUR_ID_HERE to your real ID?
echo     - Change YOUR_PW_HERE to your real password?
echo     - Change YOUR_API_KEY_HERE to your real key?
echo     - Press Ctrl+S to save?
echo     - Close Notepad?
echo   ============================================
echo.
echo   Press any key to continue...
pause >nul
goto :env_validate

:env_check
echo        Config file found
goto :env_validate

:env_validate
findstr /C:"YOUR_ID_HERE" .env >nul 2>&1
if not errorlevel 1 goto :env_not_filled
findstr /C:"YOUR_PW_HERE" .env >nul 2>&1
if not errorlevel 1 goto :env_not_filled
findstr /C:"YOUR_API_KEY_HERE" .env >nul 2>&1
if not errorlevel 1 goto :env_not_filled
echo        Config OK
goto :env_done

:env_not_filled
echo.
echo   [!!] Settings still have placeholder values!
echo.
echo   You need to replace:
echo     YOUR_ID_HERE      with your DealSitePlus ID
echo     YOUR_PW_HERE      with your DealSitePlus password
echo     YOUR_API_KEY_HERE  with your Anthropic API key
echo.
echo   Opening Notepad again...
echo   Edit the values, then Ctrl+S to save, then close Notepad.
echo.
notepad .env
echo   Press any key after saving and closing Notepad...
pause >nul
goto :env_validate

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
exit /b 0

:download_fail
echo.
echo [ERROR] Download failed. Check your internet connection.
pause
exit /b 1
