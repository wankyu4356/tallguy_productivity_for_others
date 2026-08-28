"""웹 UI에서 .env 설정을 읽고 쓰기 위한 모듈.

프로그램을 다시 켜지 않고도 값을 바꿀 수 있도록, 파일에 저장한 뒤
실행 중인 settings 객체와 os.environ 에도 즉시 반영한다.
"""

from __future__ import annotations

import os
from pathlib import Path

from app.paths import env_file
from app.utils.logging import get_logger

logger = get_logger(__name__)

# 웹 UI에서 편집을 허용할 키. 여기 없는 키는 무시한다.
EDITABLE_KEYS = (
    "ANTHROPIC_API_KEY",
    "DEALSITEPLUS_ID",
    "DEALSITEPLUS_PW",
    "CLAUDE_MODEL",
    "BROWSER_HEADLESS",
    "LOG_LEVEL",
)

# 화면에 그대로 노출하면 안 되는 키
SECRET_KEYS = ("ANTHROPIC_API_KEY", "DEALSITEPLUS_PW")

DEFAULT_TEMPLATE = """\
# ── 딜사이트 News Clipper 설정 ──
# 이 파일은 웹 화면(설정)에서도 수정할 수 있습니다.

# 딜사이트플러스 로그인 정보 (비워두면 브라우저에서 직접 로그인)
DEALSITEPLUS_ID=
DEALSITEPLUS_PW=

# Claude API 키 (필수) — https://console.anthropic.com 에서 발급
ANTHROPIC_API_KEY=

# ── 아래는 보통 건드릴 필요가 없습니다 ──
CLAUDE_MODEL=claude-sonnet-5
LOG_LEVEL=INFO
BROWSER_HEADLESS=false
CRAWL_TIMEOUT_MS=30000
NAVIGATION_TIMEOUT_MS=15000
MAX_CONCURRENT_PAGES=3
CLEANUP_HOURS=24
"""


def ensure_env_file() -> Path:
    """.env 가 없으면 주석이 달린 기본 템플릿으로 만든다."""
    path = env_file()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(DEFAULT_TEMPLATE, encoding="utf-8")
        logger.info(f"설정 파일 생성: {path}")
    return path


def read_env() -> dict[str, str]:
    """.env 를 파싱해 key=value 사전으로 돌려준다."""
    path = env_file()
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def mask_secret(value: str) -> str:
    """비밀 값을 화면에 보여줄 형태로 가린다."""
    if not value:
        return ""
    if len(value) <= 12:
        return "•" * len(value)
    return f"{value[:7]}{'•' * 12}{value[-4:]}"


def write_env(updates: dict[str, str]) -> None:
    """주석과 줄 순서를 유지한 채 값만 바꿔 저장한다.

    빈 문자열은 '값을 지운다'는 뜻으로 처리한다. 호출하는 쪽에서 미리
    '변경 없음'인 항목을 제외해서 넘겨야 한다.
    """
    path = ensure_env_file()
    updates = {k: v for k, v in updates.items() if k in EDITABLE_KEYS}
    if not updates:
        return

    lines = path.read_text(encoding="utf-8").splitlines()
    seen: set[str] = set()

    for i, raw in enumerate(lines):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key = stripped.partition("=")[0].strip()
        if key in updates:
            lines[i] = f"{key}={updates[key]}"
            seen.add(key)

    # 파일에 아직 없던 키는 끝에 덧붙인다
    missing = [k for k in updates if k not in seen]
    if missing:
        lines.append("")
        for key in missing:
            lines.append(f"{key}={updates[key]}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _apply_runtime(updates)
    logger.info(f"설정 저장: {', '.join(sorted(updates))}")


def _apply_runtime(updates: dict[str, str]) -> None:
    """재시작 없이 현재 프로세스에 값을 반영한다."""
    from app.config import RETIRED_MODEL_REPLACEMENTS, settings

    for key, value in updates.items():
        os.environ[key] = value

        if key == "BROWSER_HEADLESS":
            setattr(settings, key, value.strip().lower() in ("1", "true", "yes", "on"))
        elif key == "CLAUDE_MODEL":
            setattr(settings, key, RETIRED_MODEL_REPLACEMENTS.get(value, value))
        elif hasattr(settings, key):
            setattr(settings, key, value)


def is_configured() -> bool:
    """최소 설정(API 키)이 끝났는지."""
    from app.config import settings

    return bool(settings.ANTHROPIC_API_KEY.strip())
