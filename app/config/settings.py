"""MVP configuration loaded from environment variables.

No secrets are hard-coded; defaults are development-only and are overridden by .env.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, List, Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Kisaan Dost MVP"
    environment: str = "dev"
    api_prefix: str = "/api/v1"
    cors_origins: Any = Field(default=["http://localhost:3000", "http://localhost:8080", "http://localhost:8000"])

    # Auth
    jwt_secret_key: str = Field(default="change-me-in-every-env", min_length=8)
    jwt_access_token_minutes: int = 60
    jwt_algorithm: str = "HS256"

    # Rate limiting
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    login_rate_limit_requests: int = 100
    login_rate_limit_window_seconds: int = 60

    # Database Configuration (PostgreSQL / SQLite fallback)
    database_url: Optional[str] = Field(default=None)
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "kisaan_dost"
    db_user: str = "kisaan_user"
    db_password: str = ""
    use_database: bool = False

    # Data paths (relative to project root, which is the parent of app/)
    project_root: Path = Path(__file__).resolve().parent.parent.parent
    model_path: Path = Field(default=Path("Kisaan_Dost_Data/models/best_plantvillage_model_v2.pt"))
    class_mapping_path: Path = Field(default=Path("Kisaan_Dost_Data/data/processed/plantvillage_class_mapping.csv"))
    weather_csv_path: Path = Field(default=Path("Kisaan_Dost_Data/processed/district_monthly_weather.csv"))
    coordinates_csv_path: Path = Field(default=Path("Kisaan_Dost_Data/processed/district_coordinates.csv"))
    satellite_csv_path: Path = Field(default=Path("Kisaan_Dost_Data/processed/district_monthly_satellite_v1.csv"))
    satellite_coverage_csv_path: Path = Field(default=Path("Kisaan_Dost_Data/processed/district_monthly_satellite_coverage_v1.csv"))
    satellite_join_audit_csv_path: Path = Field(default=Path("Kisaan_Dost_Data/processed/district_monthly_satellite_join_audit_v1.csv"))
    # Open-Meteo live weather settings
    open_meteo_base_url: str = "https://api.open-meteo.com/v1/forecast"
    open_meteo_timeout_seconds: float = 5.0
    open_meteo_current_ttl_seconds: int = 1800  # 30 min
    open_meteo_forecast_ttl_seconds: int = 3600  # 60 min
    open_meteo_rate_limit_requests: int = 60
    open_meteo_rate_limit_window_seconds: int = 60

    # AMIS Punjab Market Prices
    amis_prices_csv_path: Path = Field(default=Path("Kisaan_Dost_Data/processed/amis_market_prices_v1.csv"))
    amis_review_queue_csv_path: Path = Field(default=Path("Kisaan_Dost_Data/processed/amis_market_price_review_queue_v1.csv"))
    amis_commodity_catalog_csv_path: Path = Field(default=Path("Kisaan_Dost_Data/processed/amis_commodity_catalog_v1.csv"))
    amis_market_catalog_csv_path: Path = Field(default=Path("Kisaan_Dost_Data/processed/amis_market_catalog_v1.csv"))
    amis_stale_threshold_days: int = 3

    # Phase 8 Agri Statistics & Water Availability
    land_utilization_csv_path: Path = Field(default=Path("Kisaan_Dost_Data/processed/district_land_utilization_v1.csv"))
    water_availability_csv_path: Path = Field(default=Path("Kisaan_Dost_Data/processed/district_water_availability_v1.csv"))

    # Phase 9 GDP and Trade Statistics
    agri_gdp_csv_path: Path = Field(default=Path("Kisaan_Dost_Data/processed/agri_gdp_trends_v1.csv"))
    agri_exports_csv_path: Path = Field(default=Path("Kisaan_Dost_Data/processed/agri_exports_v1.csv"))
    agri_imports_csv_path: Path = Field(default=Path("Kisaan_Dost_Data/processed/agri_imports_v1.csv"))
    agri_trade_summary_csv_path: Path = Field(default=Path("Kisaan_Dost_Data/processed/agri_trade_summary_v1.csv"))

    # Pesticide annual report ingestion
    pesticide_pdf_path: Path = Field(default=Path("../Kisaan_Dost_Data/Annual Report 2024-25_copy.pdf"))
    pesticide_facts_csv_path: Path = Field(default=Path("data/processed/pesticide_report_facts.csv"))
    pesticide_chunks_jsonl_path: Path = Field(default=Path("data/processed/pesticide_report_chunks.jsonl"))
    pesticide_meta_json_path: Path = Field(default=Path("data/processed/pesticide_report_ingestion_meta.json"))
    pesticide_advisory_rate_limit_requests: int = 10
    pesticide_advisory_rate_limit_window_seconds: int = 60
    pesticide_max_citations: int = 5

    # Upload security
    upload_max_bytes: int = 5 * 1024 * 1024  # 5 MB
    upload_allowed_types: List[str] = Field(default=["image/jpeg", "image/png"])
    upload_allowed_extensions: List[str] = Field(default=[".jpg", ".jpeg", ".png"])

    # Inference
    confidence_threshold: float = 0.75

    # Application data directory (uploads, audit logs, user store)
    data_dir: Path = Field(default=Path("app_data"))

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("upload_allowed_types", "upload_allowed_extensions", mode="before")
    @classmethod
    def _split_lists(cls, value):
        if isinstance(value, str):
            return [item.strip().lower() for item in value.split(",") if item.strip()]
        return value

    def model_full_path(self) -> Path:
        if self.model_path.is_absolute():
            return self.model_path.resolve()
        return (self.project_root / self.model_path).resolve()

    def class_mapping_full_path(self) -> Path:
        if self.class_mapping_path.is_absolute():
            return self.class_mapping_path.resolve()
        return (self.project_root / self.class_mapping_path).resolve()

    def weather_csv_full_path(self) -> Path:
        if self.weather_csv_path.is_absolute():
            return self.weather_csv_path.resolve()
        return (self.project_root / self.weather_csv_path).resolve()

    def coordinates_csv_full_path(self) -> Path:
        if self.coordinates_csv_path.is_absolute():
            return self.coordinates_csv_path.resolve()
        return (self.project_root / self.coordinates_csv_path).resolve()

    def satellite_csv_full_path(self) -> Path:
        if self.satellite_csv_path.is_absolute():
            return self.satellite_csv_path.resolve()
        return (self.project_root / self.satellite_csv_path).resolve()

    def satellite_coverage_csv_full_path(self) -> Path:
        if self.satellite_coverage_csv_path.is_absolute():
            return self.satellite_coverage_csv_path.resolve()
        return (self.project_root / self.satellite_coverage_csv_path).resolve()

    def satellite_join_audit_csv_full_path(self) -> Path:
        if self.satellite_join_audit_csv_path.is_absolute():
            return self.satellite_join_audit_csv_path.resolve()
        return (self.project_root / self.satellite_join_audit_csv_path).resolve()

    def pesticide_pdf_full_path(self) -> Path:
        if self.pesticide_pdf_path.is_absolute():
            return self.pesticide_pdf_path.resolve()
        return (self.project_root / self.pesticide_pdf_path).resolve()

    def pesticide_facts_csv_full_path(self) -> Path:
        return self.project_root / self.pesticide_facts_csv_path

    def pesticide_chunks_jsonl_full_path(self) -> Path:
        return self.project_root / self.pesticide_chunks_jsonl_path

    def pesticide_meta_json_full_path(self) -> Path:
        return self.project_root / self.pesticide_meta_json_path

    def amis_prices_csv_full_path(self) -> Path:
        if self.amis_prices_csv_path.is_absolute():
            return self.amis_prices_csv_path.resolve()
        return (self.project_root / self.amis_prices_csv_path).resolve()

    def uploads_dir(self) -> Path:
        path = self.project_root / self.data_dir / "uploads"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def audit_log_path(self) -> Path:
        path = self.project_root / self.data_dir / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path / "audit.log"

    def user_store_path(self) -> Path:
        path = self.project_root / self.data_dir / "store"
        path.mkdir(parents=True, exist_ok=True)
        return path / "users.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
