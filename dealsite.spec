# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 빌드 스펙 — 딜사이트 News Clipper.

빌드:  pyinstaller dealsite.spec --noconfirm
결과:  dist/DealSiteNewsClipper(.exe)
"""

import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# 난독화 빌드에서는 build_obf/ 를, 일반 빌드에서는 현재 폴더를 소스로 쓴다.
SRC = os.environ.get("DEALSITE_SRC_ROOT", ".")
ENTRY = os.path.join(SRC, "launcher.py")

# --- 번들에 포함할 리소스 (templates / static) ---
datas = [
    (os.path.join(SRC, "app/templates"), "app/templates"),
    (os.path.join(SRC, "app/static"), "app/static"),
]
binaries = []
hiddenimports = []

# 런타임에 데이터 파일이 필요한 패키지들.
#  tzdata   : Windows에 IANA 타임존 DB가 없어 Asia/Seoul 조회가 실패함
#  docx     : 새 문서 생성용 default.docx 템플릿이 패키지 안에 들어있음
#  reportlab: 내장 폰트/AFM 메트릭 파일
#  holidays : 국가별 공휴일 정의 모듈
# 난독화 빌드에서는 app 코드의 import 가 블롭에 가려 PyInstaller 가
# 서드파티 의존성을 자동 발견하지 못한다. 따라서 앱이 쓰는 모든 패키지를
# 명시적으로 통째 수집한다. (일반 빌드에도 무해하다.)
# requirements.txt 의 모든 패키지 + 그 전이 의존성을 자동 계산해 통째 수집한다.
# (난독화되면 app 코드의 import 가 안 보이므로, 앱이 쓰는 배포판 전체를 명시 포함)
import importlib.metadata as _md
import re as _re

def _dist_closure(seed_dists):
    """배포판 이름들의 전이 의존성 폐쇄를 구한다."""
    seen, stack = set(), list(seed_dists)
    while stack:
        name = _re.split(r"[<>=!;\[ ]", stack.pop().strip())[0].lower().replace("_", "-")
        if not name or name in seen:
            continue
        seen.add(name)
        try:
            for req in (_md.requires(name) or []):
                # "extra == ..." 조건이 붙은 선택적 의존성은 건너뛴다
                if "extra ==" in req:
                    continue
                stack.append(req)
        except _md.PackageNotFoundError:
            pass
    return seen

# requirements.txt 시드
_seed = []
_req_file = os.path.join(os.path.abspath("."), "requirements.txt")
if os.path.exists(_req_file):
    for line in open(_req_file, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#"):
            _seed.append(line)

_dist_to_import = {
    "python-docx": "docx", "python-dateutil": "dateutil", "python-dotenv": "dotenv",
    "python-multipart": "multipart", "beautifulsoup4": "bs4", "pyyaml": "yaml",
    "pillow": "PIL", "uvicorn": "uvicorn", "pydantic-settings": "pydantic_settings",
    "typing-extensions": "typing_extensions",
}
for _dist in _dist_closure(_seed):
    _imp = _dist_to_import.get(_dist, _dist.replace("-", "_"))
    try:
        _d, _b, _h = collect_all(_imp)
        datas += _d; binaries += _b; hiddenimports += _h
    except Exception as exc:
        print(f"[spec] collect_all({_imp}) 건너뜀: {exc}")

# 동적 import 때문에 정적 분석으로는 안 잡히는 모듈들
for pkg in ("uvicorn", "anthropic", "selenium", "pydantic", "pydantic_settings", "holidays"):
    try:
        hiddenimports += collect_submodules(pkg)
    except Exception as exc:
        print(f"[spec] collect_submodules({pkg}) 건너뜀: {exc}")

# 난독화 런타임 (일반 빌드에는 없음 — 있으면 포함)
import glob as _glob
for _rt in _glob.glob(os.path.join(SRC, "pyarmor_runtime_*")):
    _name = os.path.basename(_rt)
    hiddenimports.append(_name)
    datas.append((_rt, _name))

# 난독화 빌드에서는 import 체인이 블롭 안에 숨어 PyInstaller 가 추적하지 못한다.
# 원본 app 트리를 직접 스캔해 모든 서브모듈을 강제 포함한다.
def _all_app_modules():
    mods = []
    src_app = os.path.join(os.path.abspath("."), "app")
    for root, _dirs, files in os.walk(src_app):
        for fn in files:
            if not fn.endswith(".py"):
                continue
            rel = os.path.relpath(os.path.join(root, fn), os.path.dirname(src_app))
            mod = rel[:-3].replace(os.sep, ".")
            if mod.endswith(".__init__"):
                mod = mod[: -len(".__init__")]
            mods.append(mod)
    return mods

hiddenimports += _all_app_modules()

hiddenimports += [
    "app",
    "app.main",
    "app.config",
    "app.paths",
    "app.routers.settings",
    "app.services.env_store",
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
    [ENTRY],
    pathex=[os.path.abspath(SRC)],
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
