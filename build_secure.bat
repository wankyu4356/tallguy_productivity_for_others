@echo off
setlocal
chcp 65001 >nul
title DealSite News Clipper - Secure Build

set "ROOT=%~dp0"
set "OBF=%ROOT%build_obf"

echo ============================================================
echo   DealSite News Clipper - 보호 빌드 (난독화)
echo ============================================================
echo.

echo [1/5] 의존성 확인...
python -m pip install -q -r requirements.txt
python -m pip install -q pyinstaller pyarmor
if errorlevel 1 ( echo [오류] 의존성 설치 실패 & pause & exit /b 1 )

echo [2/5] 이전 산출물 정리...
if exist "%OBF%" rmdir /s /q "%OBF%"
if exist "%ROOT%build" rmdir /s /q "%ROOT%build"
if exist "%ROOT%dist" rmdir /s /q "%ROOT%dist"
mkdir "%OBF%"

echo [3/5] 파이썬 소스 난독화...
python -m pyarmor gen --recursive --output "%OBF%" "%ROOT%app" "%ROOT%launcher.py"
if errorlevel 1 ( echo [오류] 난독화 실패 & pause & exit /b 1 )
xcopy "%ROOT%app\templates" "%OBF%\app\templates" /E /I /Y /Q >nul
xcopy "%ROOT%app\static"    "%OBF%\app\static"    /E /I /Y /Q >nul

echo [4/5] 실행 파일 빌드...
set "DEALSITE_SRC_ROOT=%OBF%"
python -m PyInstaller dealsite.spec --noconfirm
if errorlevel 1 ( echo [오류] 빌드 실패 & pause & exit /b 1 )

echo [5/5] 정리...
rmdir /s /q "%OBF%"

echo.
echo ============================================================
echo   보호 빌드 완료: dist\DealSiteNewsClipper.exe
echo   파이썬 소스가 암호화되어 디컴파일해도 로직을 읽을 수 없습니다.
echo ============================================================
pause
