#!/usr/bin/env bash
# DealSite News Clipper — macOS / Linux 빌드 스크립트
set -euo pipefail

echo "============================================================"
echo "  DealSite News Clipper - Build"
echo "============================================================"
echo

PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null 2>&1 || { echo "[오류] $PY 를 찾을 수 없습니다."; exit 1; }
echo "  $($PY --version)"

echo
echo "[1/3] 의존성 설치 중..."
"$PY" -m pip install --upgrade pip >/dev/null
"$PY" -m pip install -r requirements.txt
"$PY" -m pip install pyinstaller

echo
echo "[2/3] 이전 빌드 정리..."
rm -rf build dist

echo
echo "[3/3] 빌드 중... (5~10분 소요)"
"$PY" -m PyInstaller dealsite.spec --noconfirm

echo
echo "============================================================"
echo "  빌드 완료"
echo "============================================================"
echo
echo "  실행 파일: dist/DealSiteNewsClipper"
echo
echo "  배포 방법:"
echo "    1) dist/DealSiteNewsClipper 를 원하는 폴더에 복사"
echo "    2) 실행하면 .env 설정 파일이 자동 생성됩니다"
echo "    3) ANTHROPIC_API_KEY 를 채우고 다시 실행하면 브라우저가 열립니다"
echo
