@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title 딜사이트플러스 뉴스 클리퍼 설치 및 실행

echo ============================================
echo   딜사이트플러스 뉴스 클리퍼 설치 및 실행
echo ============================================
echo.

REM ── 1. Python 확인 및 자동 설치 ──
echo [1/6] Python 확인 중...
python --version >nul 2>&1
if errorlevel 1 (
    echo        Python이 없습니다. 자동 설치를 시작합니다...
    echo.

    REM winget으로 시도
    winget --version >nul 2>&1
    if not errorlevel 1 (
        echo        winget으로 Python 설치 중...
        winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
        if errorlevel 1 (
            goto :python_manual
        )
        echo.
        echo [알림] Python 설치 완료. PATH 적용을 위해 이 창을 닫고
        echo        setup_and_run.bat 를 다시 실행해주세요.
        echo.
        pause
        exit /b 0
    )

    REM winget 없으면 curl로 직접 다운로드
    echo        winget이 없어 직접 다운로드합니다...
    curl -L -o "%TEMP%\python_installer.exe" "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"
    if errorlevel 1 (
        goto :python_manual
    )
    echo        Python 설치 프로그램 실행 중...
    "%TEMP%\python_installer.exe" /passive InstallAllUsers=0 PrependPath=1 Include_test=0
    if errorlevel 1 (
        goto :python_manual
    )
    del "%TEMP%\python_installer.exe" >nul 2>&1
    echo.
    echo [알림] Python 설치 완료. PATH 적용을 위해 이 창을 닫고
    echo        setup_and_run.bat 를 다시 실행해주세요.
    echo.
    pause
    exit /b 0
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo        Python %%v 확인됨

REM ── 2. pip 확인 ──
echo.
echo [2/6] pip 확인 중...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo        pip 설치 중...
    python -m ensurepip --upgrade
)
python -m pip install --upgrade pip >nul 2>&1
echo        pip 확인됨

REM ── 3. Edge 브라우저 확인 ──
echo.
echo [3/6] Edge 브라우저 확인 중...
if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" (
    echo        Edge 브라우저 확인됨
) else if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" (
    echo        Edge 브라우저 확인됨
) else (
    echo.
    echo [경고] Edge 브라우저를 찾을 수 없습니다.
    echo        Windows 10/11에는 기본 설치되어 있어야 합니다.
    echo        없다면 https://www.microsoft.com/edge 에서 설치해주세요.
    echo.
)
echo        (EdgeDriver는 Selenium이 자동으로 다운로드합니다)

REM ── 4. 패키지 설치 ──
echo.
echo [4/6] Python 패키지 설치 중...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [오류] 패키지 설치 실패
    pause
    exit /b 1
)
echo        패키지 설치 완료

REM ── 5. .env 파일 설정 ──
echo.
echo [5/6] 환경변수 설정 확인 중...
if not exist .env (
    echo.
    echo [알림] .env 파일이 없습니다. 설정을 입력해주세요.
    echo.

    set /p "DS_ID=  딜사이트플러스 아이디: "
    set /p "DS_PW=  딜사이트플러스 비밀번호: "
    set /p "API_KEY=  Anthropic API Key (sk-ant-...): "

    (
        echo # DealSitePlus credentials
        echo DEALSITEPLUS_ID=!DS_ID!
        echo DEALSITEPLUS_PW=!DS_PW!
        echo.
        echo # Claude API
        echo ANTHROPIC_API_KEY=!API_KEY!
        echo CLAUDE_MODEL=claude-sonnet-4-20250514
        echo.
        echo # App settings
        echo OUTPUT_DIR=./output
        echo LOG_LEVEL=INFO
        echo HOST=0.0.0.0
        echo PORT=8000
        echo.
        echo # Browser settings
        echo BROWSER_HEADLESS=true
        echo CRAWL_TIMEOUT_MS=30000
        echo NAVIGATION_TIMEOUT_MS=15000
        echo MAX_CONCURRENT_PAGES=3
        echo.
        echo # Cleanup
        echo CLEANUP_HOURS=24
    ) > .env

    echo.
    echo        .env 설정 완료
) else (
    echo        .env 파일 이미 존재함 (기존 설정 유지)
)

REM ── 6. 서버 실행 ──
echo.
echo [6/6] 서버 시작 중...
echo.
echo ============================================
echo   브라우저에서 http://localhost:8000 접속
echo   종료하려면 이 창에서 Ctrl+C
echo ============================================
echo.

REM 브라우저 자동 열기
start http://localhost:8000

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

echo.
echo 서버가 종료되었습니다.
pause
exit /b 0

:python_manual
echo.
echo [오류] Python 자동 설치에 실패했습니다.
echo.
echo  수동 설치 방법:
echo  1. https://www.python.org/downloads/ 접속
echo  2. "Download Python 3.12" 클릭
echo  3. 설치 시 "Add Python to PATH" 반드시 체크
echo  4. 설치 후 이 파일을 다시 실행하세요
echo.
pause
exit /b 1
