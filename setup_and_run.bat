@echo off
chcp 65001 >nul 2>&1
title 딜사이트플러스 뉴스 클리퍼 설치 및 실행

echo ============================================
echo   딜사이트플러스 뉴스 클리퍼 설치 및 실행
echo ============================================
echo.

REM ── 1. Python 확인 ──
echo [1/5] Python 확인 중...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [오류] Python이 설치되어 있지 않습니다.
    echo.
    echo  1. https://www.python.org/downloads/ 에서 Python 3.12 설치
    echo  2. 설치 시 "Add Python to PATH" 반드시 체크
    echo  3. 설치 후 이 파일을 다시 실행하세요
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo        Python %%v 확인됨

REM ── 2. Edge WebDriver 확인 ──
echo.
echo [2/5] Edge WebDriver 확인 중...
where msedgedriver >nul 2>&1
if errorlevel 1 (
    echo.
    echo [경고] msedgedriver가 PATH에 없습니다.
    echo.
    echo  1. Edge 브라우저 주소창에 edge://settings/help 입력하여 버전 확인
    echo  2. https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/
    echo     에서 같은 버전 다운로드
    echo  3. 압축 풀어서 msedgedriver.exe를 C:\Windows 에 복사
    echo.
    set /p CONTINUE="Edge WebDriver 없이 계속 진행하시겠습니까? (y/n): "
    if /i not "!CONTINUE!"=="y" (
        if /i not "%CONTINUE%"=="y" (
            pause
            exit /b 1
        )
    )
) else (
    echo        msedgedriver 확인됨
)

REM ── 3. 패키지 설치 ──
echo.
echo [3/5] Python 패키지 설치 중...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [오류] 패키지 설치 실패
    pause
    exit /b 1
)
echo        패키지 설치 완료

REM ── 4. .env 파일 설정 ──
echo.
echo [4/5] 환경변수 설정 확인 중...
if not exist .env (
    copy .env.example .env >nul
    echo.
    echo [알림] .env 파일이 생성되었습니다.
    echo        아래 3가지를 입력해주세요.
    echo.

    set /p DS_ID="  딜사이트플러스 아이디: "
    set /p DS_PW="  딜사이트플러스 비밀번호: "
    set /p API_KEY="  Anthropic API Key (sk-ant-...): "

    REM .env 파일 직접 생성
    (
        echo # DealSitePlus credentials
        echo DEALSITEPLUS_ID=%DS_ID%
        echo DEALSITEPLUS_PW=%DS_PW%
        echo.
        echo # Claude API
        echo ANTHROPIC_API_KEY=%API_KEY%
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

REM ── 5. 서버 실행 ──
echo.
echo [5/5] 서버 시작 중...
echo.
echo ============================================
echo   브라우저에서 http://localhost:8000 접속
echo   종료하려면 이 창에서 Ctrl+C
echo ============================================
echo.
uvicorn app.main:app --host 0.0.0.0 --port 8000

pause
