from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Kisaan Dost API"
    environment: str = "dev"  # dev | staging | prod
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Data stores
    database_url: str = "postgresql+asyncpg://kd:kd@localhost:5432/kisaandost"
    redis_url: str = "redis://localhost:6379/0"

    # Auth (RULES.md §7)
    jwt_secret_key: str = "change-me-in-every-env"
    jwt_access_token_minutes: int = 30
    jwt_refresh_token_days: int = 30

    # OTP policy (RULES.md §7.2)
    otp_length: int = 6
    otp_ttl_seconds: int = 300
    otp_max_attempts: int = 5
    otp_max_sends_per_hour: int = 3

    # Google Earth Engine — workers only, never exposed to clients
    gee_project: str = ""
    gee_service_account_json: str = ""  # path or inline JSON; secret manager in prod

    # Integrations
    weather_api_base_url: str = ""
    weather_api_key: str = ""
    sms_provider_url: str = ""
    sms_provider_key: str = ""
    fcm_credentials_json: str = ""

    sentry_dsn: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
