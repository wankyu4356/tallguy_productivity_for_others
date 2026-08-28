@echo off
setlocal
chcp 65001 >nul
title DealSite News Clipper - Build

echo ============================================================
echo   DealSite News Clipper - EXE Build
echo ============================================================
echo.

REM == 1. Python 확인 ==
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python 을 찾을 수 없습니다.
    echo   https://www.python.org/downloads/ 에서 Python 3.11 이상을 설치하고
    echo   설치 시 "Add Python to PATH" 를 반드시 체크하세요.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo   %%v

REM == 2. 의존성 설치 ==
echo.
echo [1/3] 의존성 설치 중... (처음 한 번은 몇 분 걸립니다)
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [오류] 의존성 설치 실패
    pause
    exit /b 1
)
python -m pip install pyinstaller
if errorlevel 1 (
    echo [오류] PyInstaller 설치 실패
    pause
    exit /b 1
)

REM == 3. 이전 빌드 정리 ==
echo.
echo [2/3] 이전 빌드 정리...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM == 4. 빌드 ==
echo.
echo [3/3] 빌드 중... (5~10분 정도 걸립니다)
python -m PyInstaller dealsite.spec --noconfirm
if errorlevel 1 (
    echo.
    echo [오류] 빌드 실패. 위 메시지를 확인하세요.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   빌드 완료
echo ============================================================
echo.
echo   실행 파일: dist\DealSiteNewsClipper.exe
echo.
echo   배포 방법:
echo     1) dist\DealSiteNewsClipper.exe 를 원하는 폴더에 복사
echo     2) 더블클릭하면 .env 설정 파일이 자동 생성됩니다
echo     3) ANTHROPIC_API_KEY 를 채우고 다시 실행하면 브라우저가 열립니다
echo.
pause
