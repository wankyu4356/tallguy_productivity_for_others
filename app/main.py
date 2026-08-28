import asyncio
import shutil
import time
import webbrowser
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.paths import static_dir, templates_dir
from app.models.schemas import SessionState
from app.routers import health, clipper, settings as settings_router
from app.services.browser import BrowserManager
from app.utils.logging import setup_logging, get_logger

logger = get_logger(__name__)

# In-memory session store
sessions: dict[str, SessionState] = {}

# Browser manager singleton
browser_manager = BrowserManager()


def cleanup_old_sessions():
    """Remove output directories older than CLEANUP_HOURS."""
    if not settings.OUTPUT_DIR.exists():
        return
    cutoff = time.time() - settings.CLEANUP_HOURS * 3600
    for p in settings.OUTPUT_DIR.iterdir():
        if p.is_dir() and p.name != ".gitkeep" and p.stat().st_mtime < cutoff:
            shutil.rmtree(p, ignore_errors=True)
            logger.info(f"Cleaned up old session: {p.name}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.LOG_LEVEL)

    # 설정 파일이 없으면 만들어 둔다. 값이 비어 있어도 서버는 띄우고,
    # 웹 화면(/setup)에서 입력받는다 — exe를 켠 사용자가 콘솔을 볼 필요가 없도록.
    from app.services.env_store import ensure_env_file, is_configured

    ensure_env_file()
    if not is_configured():
        logger.warning("ANTHROPIC_API_KEY 미설정 — /setup 화면에서 입력받습니다.")

    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cleanup_old_sessions()

    await browser_manager.start()
    logger.info("Application started")

    yield
    await browser_manager.stop()
    logger.info("Application stopped")


app = FastAPI(title="딜사이트플러스 News Clipper", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=static_dir()), name="static")
templates = Jinja2Templates(directory=templates_dir())


# Python 3.14: Jinja2 LRUCache creates cache_key = (name, globals_dict) which is
# unhashable. This no-op cache bypasses the issue entirely.
class _NoOpCache:
    def get(self, key, default=None):
        return default
    def __setitem__(self, key, value):
        pass
    def __contains__(self, key):
        return False
    def clear(self):
        pass

templates.env.cache = _NoOpCache()  # type: ignore[assignment]

app.include_router(health.router)
app.include_router(clipper.router)
app.include_router(settings_router.router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    from fastapi.responses import RedirectResponse

    from app.services.business_day import get_clipping_window
    from app.services.env_store import is_configured

    # 최초 실행: 아직 API 키가 없으면 온보딩 화면으로
    if not is_configured():
        return RedirectResponse("/setup", status_code=307)

    date_from, date_to = get_clipping_window()
    return templates.TemplateResponse(request, "index.html", {
        "date_from": date_from,
        "date_to": date_to,
        "date_from_str": date_from.strftime("%Y-%m-%dT%H:%M"),
        "date_to_str": date_to.strftime("%Y-%m-%dT%H:%M"),
        "sessions": sessions,
    })
