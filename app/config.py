from __future__ import annotations

from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

ASSESSMENT_NUMBER = "+18054398008"
ROOT = Path(__file__).resolve().parents[1]
CALLS_DIR = ROOT / "calls"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str
    openai_realtime_model: str = "gpt-realtime-2.1"
    openai_realtime_voice: str = "marin"

    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str

    public_base_url: str

    log_level: str = "INFO"

    @property
    def public_https_url(self) -> str:
        return self.public_base_url.rstrip("/")

    @property
    def public_wss_url(self) -> str:
        base = self.public_base_url.rstrip("/")
        if base.startswith("https://"):
            return "wss://" + base.removeprefix("https://")
        if base.startswith("http://"):
            return "ws://" + base.removeprefix("http://")
        raise ValueError("PUBLIC_BASE_URL must begin with http:// or https://")


def get_settings() -> Settings:
    settings = Settings()
    validate_originating_number(settings.twilio_phone_number)
    return settings


def validate_destination(number: str) -> None:
    """Hard safety boundary required by the assessment."""
    if number != ASSESSMENT_NUMBER:
        raise ValueError(
            f"Outbound destination blocked. This project may call only {ASSESSMENT_NUMBER}."
        )


def validate_originating_number(number: str) -> None:
    if not number.startswith("+") or not number[1:].isdigit():
        raise ValueError("TWILIO_PHONE_NUMBER must be in E.164 format, e.g. +13334445555.")


class CallMetadata(BaseModel):
    scenario_id: str
    call_sid: str | None = None
    status: str = "created"
    recording_sid: str | None = None
    recording_duration_seconds: int | None = None
