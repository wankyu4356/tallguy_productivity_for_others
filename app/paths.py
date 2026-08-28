"""실행 형태(개발/PyInstaller exe)에 따라 경로를 해석한다.

PyInstaller onefile로 묶으면 번들 리소스는 임시 폴더(sys._MEIPASS)에 풀리고
종료 시 사라진다. 따라서 읽기 전용 리소스(templates/static)와
쓰기 가능한 사용자 데이터(.env, output/)의 위치를 분리해야 한다.
"""

from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    """PyInstaller로 패키징된 실행 파일로 동작 중인지."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def resource_root() -> Path:
    """번들에 포함된 읽기 전용 리소스의 루트."""
    if is_frozen():
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


def app_root() -> Path:
    """templates/ 와 static/ 을 담고 있는 app 패키지 경로."""
    return resource_root() / "app"


def templates_dir() -> Path:
    return app_root() / "templates"


def static_dir() -> Path:
    return app_root() / "static"


def user_data_root() -> Path:
    """쓰기 가능한 폴더. exe면 exe가 놓인 폴더, 개발 중이면 저장소 루트.

    .env 와 output/ 이 여기에 놓이므로 사용자가 exe 옆에서 바로 찾을 수 있다.
    """
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def env_file() -> Path:
    return user_data_root() / ".env"


def output_dir() -> Path:
    return user_data_root() / "output"
