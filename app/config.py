from pathlib import Path
from pydantic_settings import BaseSettings

from app.paths import env_file, output_dir, user_data_root

# 은퇴(retired)한 모델 ID → 현재 후속 모델.
# 기존 .env에 옛 모델이 박혀 있으면 API가 404를 내고 분류가 전부 실패하므로,
# 사용자가 .env를 직접 고치지 않아도 되도록 자동으로 승계 모델로 바꿔준다.
RETIRED_MODEL_REPLACEMENTS = {
    "claude-sonnet-4-20250514": "claude-sonnet-5",
    "claude-opus-4-20250514": "claude-opus-4-8",
    "claude-3-7-sonnet-20250219": "claude-sonnet-5",
    "claude-3-5-sonnet-20241022": "claude-sonnet-5",
    "claude-3-5-sonnet-20240620": "claude-sonnet-5",
    "claude-3-5-haiku-20241022": "claude-haiku-4-5",
    "claude-3-opus-20240229": "claude-opus-4-8",
}


class Settings(BaseSettings):
    # DealSitePlus credentials
    DEALSITEPLUS_ID: str = ""
    DEALSITEPLUS_PW: str = ""

    # Claude API
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-5"

    # App settings
    OUTPUT_DIR: Path = output_dir()
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Browser settings
    BROWSER_HEADLESS: bool = True
    CRAWL_TIMEOUT_MS: int = 30000
    NAVIGATION_TIMEOUT_MS: int = 15000
    MAX_CONCURRENT_PAGES: int = 3

    # Cleanup
    CLEANUP_HOURS: int = 24

    # exe로 실행할 때도 exe 옆의 .env 를 읽도록 절대경로로 고정한다.
    model_config = {"env_file": str(env_file()), "env_file_encoding": "utf-8"}

    def validate_required(self) -> list[str]:
        errors = []
        if not self.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY is not set")
        return errors

    @property
    def has_dealsiteplus_credentials(self) -> bool:
        return bool(self.DEALSITEPLUS_ID and self.DEALSITEPLUS_PW)


settings = Settings()

# .env 에서 상대경로가 들어온 경우 exe 옆 폴더 기준으로 절대경로화한다.
if not settings.OUTPUT_DIR.is_absolute():
    settings.OUTPUT_DIR = (user_data_root() / settings.OUTPUT_DIR).resolve()

# .env에 은퇴한 모델이 남아 있으면 자동으로 승계 모델로 교체한다.
_replacement = RETIRED_MODEL_REPLACEMENTS.get(settings.CLAUDE_MODEL)
if _replacement:
    import logging

    logging.getLogger(__name__).warning(
        f"CLAUDE_MODEL '{settings.CLAUDE_MODEL}' 은(는) 서비스가 종료된 모델입니다. "
        f"'{_replacement}' 로 자동 변경합니다. .env 파일도 수정해 주세요."
    )
    settings.CLAUDE_MODEL = _replacement
