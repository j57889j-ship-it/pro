from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    database_url: str
    redis_url: str
    admin_ids: str
    target_channel_id: int | None = None
    webhook_url: str | None = None
    webhook_secret: str | None = None
    app_name: str = "Sahifa Quiz"
    top_limit: int = 10
    points_per_correct: int = 10
    max_questions_per_import: int = 100
    default_quiz_questions: int = 10
    quiz_answer_lock_seconds: int = 8
    webhook_max_connections: int = 20
    max_txt_bytes: int = 1_000_000

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    @property
    def super_admin_ids(self) -> set[int]:
        result: set[int] = set()
        for raw in self.admin_ids.split(","):
            raw = raw.strip()
            if raw:
                result.add(int(raw))
        return result


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
