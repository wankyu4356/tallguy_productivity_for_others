#!/usr/bin/env bash
# DealSite News Clipper — 난독화(코드 보호) 빌드
# app/ 의 파이썬 소스를 PyArmor 로 난독화한 뒤 PyInstaller 로 단일 exe 를 만든다.
set -euo pipefail

PY="${PYTHON:-python3}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
OBF="$ROOT/build_obf"

echo "============================================================"
echo "  DealSite News Clipper - 보호 빌드 (난독화)"
echo "============================================================"
echo

echo "[1/5] 의존성 확인..."
"$PY" -m pip install -q -r requirements.txt
"$PY" -m pip install -q pyinstaller pyarmor

echo "[2/5] 이전 산출물 정리..."
rm -rf "$OBF" "$ROOT/build" "$ROOT/dist"
mkdir -p "$OBF"

echo "[3/5] 파이썬 소스 난독화..."
# app 패키지 전체와 진입점을 난독화. 리소스(templates/static)는 그대로 복사.
"$PY" -m pyarmor.cli gen --recursive --output "$OBF" "$ROOT/app" "$ROOT/launcher.py"
# 난독화 대상이 아닌 리소스를 난독화된 app 트리에 덮어 넣는다
cp -r "$ROOT/app/templates" "$OBF/app/templates"
cp -r "$ROOT/app/static"    "$OBF/app/static"

echo "[4/5] 실행 파일 빌드..."
cd "$ROOT"
DEALSITE_SRC_ROOT="$OBF" "$PY" -m PyInstaller dealsite.spec --noconfirm

echo "[5/5] 정리..."
rm -rf "$OBF"

echo
echo "============================================================"
echo "  보호 빌드 완료: dist/DealSiteNewsClipper"
echo "  - 파이썬 소스가 암호화되어 디컴파일해도 로직을 읽을 수 없습니다."
echo "============================================================"
