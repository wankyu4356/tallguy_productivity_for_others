"""설정(.env) 온보딩 및 편집 라우터."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.paths import env_file
from app.services import env_store
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# 저장 요청에서 이 값이 오면 "기존 비밀 값을 그대로 둔다"는 뜻.
# 화면에는 마스킹된 문자열을 보여주므로, 사용자가 손대지 않은 필드를
# 마스킹된 문자열로 덮어쓰는 사고를 막는다.
UNCHANGED = "__UNCHANGED__"


class SettingsPayload(BaseModel):
    ANTHROPIC_API_KEY: str | None = None
    DEALSITEPLUS_ID: str | None = None
    DEALSITEPLUS_PW: str | None = None
    CLAUDE_MODEL: str | None = None
    BROWSER_HEADLESS: str | None = None


@router.get("/api/settings")
async def get_settings():
    """현재 설정값. 비밀 값은 마스킹해서 내려준다."""
    values = env_store.read_env()
    out: dict[str, object] = {}

    for key in env_store.EDITABLE_KEYS:
        raw = values.get(key, "")
        if key in env_store.SECRET_KEYS:
            out[key] = env_store.mask_secret(raw)
            out[f"{key}__set"] = bool(raw)
        else:
            out[key] = raw

    return {
        "values": out,
        "configured": env_store.is_configured(),
        "env_path": str(env_file()),
    }


@router.post("/api/settings")
async def save_settings(payload: SettingsPayload):
    """설정을 저장하고 즉시 반영한다."""
    updates: dict[str, str] = {}

    for key, value in payload.model_dump().items():
        if value is None:
            continue
        value = value.strip()
        # 비밀 값이 마스킹된 채로 돌아오면 변경하지 않은 것으로 본다
        if key in env_store.SECRET_KEYS and (value == UNCHANGED or "•" in value):
            continue
        updates[key] = value

    if not updates:
        return {"ok": True, "changed": [], "configured": env_store.is_configured()}

    try:
        env_store.write_env(updates)
    except OSError as e:
        logger.error(f"설정 저장 실패: {e}")
        return {
            "ok": False,
            "error": f"설정 파일을 저장하지 못했습니다: {e}",
            "env_path": str(env_file()),
        }

    return {
        "ok": True,
        "changed": sorted(updates),
        "configured": env_store.is_configured(),
    }


class KeyTestPayload(BaseModel):
    ANTHROPIC_API_KEY: str | None = None


@router.post("/api/settings/test-key")
async def test_key(payload: KeyTestPayload):
    """API 키가 실제로 동작하는지 아주 작은 요청으로 확인한다."""
    import anthropic

    from app.config import settings

    key = (payload.ANTHROPIC_API_KEY or "").strip()
    # 마스킹된 값이 오면 저장돼 있는 실제 키로 검사한다
    if not key or "•" in key or key == UNCHANGED:
        key = env_store.read_env().get("ANTHROPIC_API_KEY", "").strip()

    if not key:
        return {"ok": False, "error": "API 키가 비어 있습니다."}

    try:
        client = anthropic.Anthropic(api_key=key)
        client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=8,
            messages=[{"role": "user", "content": "hi"}],
        )
        return {"ok": True, "model": settings.CLAUDE_MODEL}
    except anthropic.AuthenticationError:
        return {"ok": False, "error": "인증 실패 — 키가 올바르지 않습니다."}
    except anthropic.NotFoundError:
        return {
            "ok": False,
            "error": f"모델 '{settings.CLAUDE_MODEL}' 을 찾을 수 없습니다. 모델명을 확인하세요.",
        }
    except anthropic.RateLimitError:
        # 키 자체는 유효하다는 뜻
        return {"ok": True, "model": settings.CLAUDE_MODEL, "note": "요청 한도에 걸렸지만 키는 유효합니다."}
    except anthropic.APIConnectionError:
        return {"ok": False, "error": "네트워크 연결에 실패했습니다. 인터넷 상태를 확인하세요."}
    except Exception as e:
        return {"ok": False, "error": f"확인 실패: {type(e).__name__} — {e}"}


@router.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request):
    from app.main import templates

    return templates.TemplateResponse(request, "setup.html", {
        "env_path": str(env_file()),
        "configured": env_store.is_configured(),
    })
