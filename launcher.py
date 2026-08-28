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


def prepare_env_file() -> None:
    """.env 가 없으면 만들어 둔다. 값이 비어 있어도 막지 않는다.

    API 키 입력은 브라우저의 온보딩 화면(/setup)에서 받는다. exe를 켠
    사용자가 콘솔을 읽고 파일을 손으로 고칠 필요가 없도록 하기 위함이다.
    """
    from app.services.env_store import ensure_env_file, is_configured

    path = ensure_env_file()
    if not is_configured():
        print(f"  설정 파일 : {path}")
        print("  아직 API 키가 없습니다 — 브라우저에서 바로 입력하실 수 있습니다.\n")


def _open_url(url: str) -> None:
    """기본 브라우저로 URL 을 연다.

    PyInstaller 로 묶은 exe 에서는 webbrowser 모듈이 기본 브라우저를 제대로
    찾지 못해 엉뚱한 파일 경로를 여는 경우가 있다. Windows 에서는 os.startfile
    이 가장 확실하므로 그것을 먼저 쓰고, 실패하면 webbrowser 로 넘어간다.
    """
    try:
        if sys.platform == "win32":
            os.startfile(url)  # type: ignore[attr-defined]
            return
    except Exception:
        pass
    try:
        webbrowser.open(url)
    except Exception:
        pass


def open_browser_when_ready(url: str, port: int, timeout: float = 40.0) -> None:
    """서버가 실제로 응답하기 시작하면 브라우저를 연다.

    서버가 뜨지 않으면 빈 페이지가 뜨는 것보다 콘솔의 주소 안내가 낫다.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.4)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                time.sleep(0.4)  # 서버가 완전히 준비되도록 살짝 여유
                _open_url(url)
                return
        time.sleep(0.3)
    # 시간 내에 서버가 안 떴으면 죽은 페이지를 여는 대신 안내만 남긴다.
    print("\n  [안내] 브라우저가 자동으로 열리지 않았습니다.")
    print(f"  아래 주소를 브라우저에 직접 입력해 주세요:  {url}\n")


def main() -> int:
    print(BANNER)

    prepare_env_file()

    port = find_free_port()
    url = f"http://127.0.0.1:{port}"

    from app.paths import output_dir, user_data_root

    output_dir().mkdir(parents=True, exist_ok=True)

    print(f"  작업 폴더 : {user_data_root()}")
    print(f"  결과 저장 : {output_dir()}")
    print()
    print("  +" + "-" * 46 + "+")
    print(f"  |  브라우저가 안 열리면 이 주소로 접속하세요       |")
    print(f"  |     {url:<40}|")
    print("  +" + "-" * 46 + "+")
    print("\n  종료하려면 이 창을 닫거나 Ctrl+C 를 누르세요.\n")
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
