# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 빌드 스펙 — 딜사이트 News Clipper.

빌드:  pyinstaller dealsite.spec --noconfirm
결과:  dist/DealSiteNewsClipper(.exe)
"""

import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# --- 번들에 포함할 리소스 (templates / static) ---
datas = [
    ("app/templates", "app/templates"),
    ("app/static", "app/static"),
]
binaries = []

# 런타임에 데이터 파일이 필요한 패키지들.
#  tzdata   : Windows에 IANA 타임존 DB가 없어 Asia/Seoul 조회가 실패함
#  docx     : 새 문서 생성용 default.docx 템플릿이 패키지 안에 들어있음
#  reportlab: 내장 폰트/AFM 메트릭 파일
#  holidays : 국가별 공휴일 정의 모듈
for pkg in ("tzdata", "docx", "reportlab", "holidays", "anthropic"):
    try:
        pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
        datas += pkg_datas
        binaries += pkg_binaries
    except Exception as exc:  # 설치되지 않았으면 건너뛴다
        print(f"[spec] collect_all({pkg}) 건너뜀: {exc}")

# 동적 import 때문에 정적 분석으로는 안 잡히는 모듈들
hiddenimports = []
for pkg in ("uvicorn", "anthropic", "selenium", "pydantic", "pydantic_settings", "holidays"):
    try:
        hiddenimports += collect_submodules(pkg)
    except Exception as exc:
        print(f"[spec] collect_submodules({pkg}) 건너뜀: {exc}")

hiddenimports += [
    "app",
    "app.main",
    "app.config",
    "app.paths",
    "email.mime.multipart",
    "email.mime.text",
    "encodings.idna",
    "multipart",
    "aiofiles",
    "dateutil",
    "bs4",
    "pypdf",
    "docx",
    "tzdata",
]

a = Analysis(
    ["launcher.py"],
    pathex=[os.path.abspath(".")],
    binaries=binaries,
    datas=datas,
    hiddenimports=sorted(set(hiddenimports)),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "PyQt5", "PySide2", "notebook", "IPython"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 아이콘은 있을 때만 사용 (Windows는 .ico 만 허용)
_icon = "app/static/img/dealsite-logo.ico"
icon_arg = _icon if os.path.exists(_icon) else None

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="DealSiteNewsClipper",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,          # 진행 로그와 오류를 사용자가 볼 수 있게 콘솔 유지
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_arg,
)
