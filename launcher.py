"""딜사이트 News Clipper — 실행 진입점.

PyInstaller로 빌드한 exe를 더블클릭하면 이 파일이 실행된다.
비어 있는 포트를 찾아 로컬 웹 서버를 띄우고 기본 브라우저를 연다.
"""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
import webbrowser

ENV_TEMPLATE = """\
# ── 딜사이트 News Clipper 설정 ──
# 아래 3개 값을 채운 뒤 저장하고 프로그램을 다시 실행하세요.

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

BANNER = """
============================================================
   DealSite News Clipper
============================================================
"""


def find_free_port(start: int = 8000, end: int = 8100) -> int:
    """start~end 사이에서 실제로 바인딩 가능한 첫 포트를 돌려준다."""
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"{start}~{end} 사이에 사용 가능한 포트가 없습니다.")


def ensure_env_file() -> bool:
    """.env 가 없으면 템플릿을 만들어 준다. 계속 진행 가능하면 True."""
    from app.paths import env_file

    path = env_file()
    if not path.exists():
        path.write_text(ENV_TEMPLATE, encoding="utf-8")
        print(f"[설정 파일 생성] {path}\n")
        print("  처음 실행이라 설정 파일을 만들었습니다.")
        print("  ANTHROPIC_API_KEY 를 채운 뒤 다시 실행해 주세요.\n")
        _try_open_editor(path)
        return False
    return True


def _try_open_editor(path) -> None:
    """설정 파일을 사용자가 바로 고칠 수 있게 기본 편집기로 연다."""
    try:
        if sys.platform == "win32":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            os.system(f'open "{path}"')
        else:
            os.system(f'xdg-open "{path}" 2>/dev/null &')
    except Exception:
        pass


def check_api_key() -> bool:
    from app.config import settings

    if not settings.ANTHROPIC_API_KEY.strip():
        from app.paths import env_file

        print("[설정 필요] ANTHROPIC_API_KEY 가 비어 있습니다.\n")
        print(f"  {env_file()} 파일을 열어")
        print("  ANTHROPIC_API_KEY=sk-ant-... 형태로 채운 뒤 다시 실행해 주세요.\n")
        _try_open_editor(env_file())
        return False
    return True


def open_browser_when_ready(url: str, port: int, timeout: float = 30.0) -> None:
    """서버가 실제로 응답하기 시작하면 브라우저를 연다."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.4)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                webbrowser.open(url)
                return
        time.sleep(0.3)
    # 시간 내에 못 뜨면 그냥 열어본다 (사용자가 주소를 볼 수 있게)
    webbrowser.open(url)


def main() -> int:
    print(BANNER)

    if not ensure_env_file():
        return 1
    if not check_api_key():
        return 1

    port = find_free_port()
    url = f"http://127.0.0.1:{port}"

    from app.paths import output_dir, user_data_root

    output_dir().mkdir(parents=True, exist_ok=True)

    print(f"  작업 폴더 : {user_data_root()}")
    print(f"  결과 저장 : {output_dir()}")
    print(f"  주소      : {url}")
    print("\n  브라우저가 자동으로 열립니다.")
    print("  종료하려면 이 창을 닫거나 Ctrl+C 를 누르세요.\n")
    print("=" * 60 + "\n")

    threading.Thread(
        target=open_browser_when_ready, args=(url, port), daemon=True
    ).start()

    import uvicorn

    from app.main import app as fastapi_app

    uvicorn.run(fastapi_app, host="127.0.0.1", port=port, log_level="info")
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except KeyboardInterrupt:
        print("\n종료합니다.")
        code = 0
    except Exception:
        import traceback

        print("\n[오류가 발생했습니다]\n")
        traceback.print_exc()
        code = 1

    if code != 0 and sys.stdin and sys.stdin.isatty():
        input("\n계속하려면 Enter 키를 누르세요...")
    sys.exit(code)
