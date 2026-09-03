"""Pydantic request/response models for the MVP API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.security.auth import Role


class RegisterRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=1, max_length=100)
    role: Role = Role.FARMER

    @field_validator("phone")
    @classmethod
    def _clean_phone(cls, value: str) -> str:
        return value.strip()


class LoginRequest(BaseModel):
    phone: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: Role


class FarmerProfile(BaseModel):
    user_id: str
    name: str
    phone: str
    email: Optional[str] = None
    district: Optional[str] = None
    crop: Optional[str] = None
    farm_size_acres: Optional[float] = None
    irrigation_type: Optional[str] = None
    language: str = "en"


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    district: Optional[str] = Field(None, min_length=1, max_length=100)
    crop: Optional[str] = Field(None, min_length=1, max_length=100)
    farm_size_acres: Optional[float] = Field(None, ge=0.1, le=2000)
    irrigation_type: Optional[str] = Field(None, min_length=1, max_length=50)
    language: Optional[str] = Field(None, pattern="^(en|ur)$")


class DashboardResponse(BaseModel):
    user: Dict[str, Any]
    weather: Dict[str, Any]
    farm_health: Dict[str, Any]
    market: Dict[str, Any]
    satellite: Dict[str, Any]
    risk_assessment: Optional[Dict[str, Any]] = None
    quick_actions: List[Dict[str, str]]


class PredictionResponse(BaseModel):
    predicted_class: str
    confidence: float
    model_version: str
    uncertain: bool
    warning: Optional[str] = None


class PestCitation(BaseModel):
    fact_id: str
    category: str
    source_page: int
    source_section: str
    source_excerpt: str


class PestAlertItem(BaseModel):
    fact_id: str
    category: str
    crop: Optional[str] = None
    pest_or_disease: Optional[str] = None
    district: Optional[str] = None
    date_or_period: Optional[str] = None
    advisory_text: Optional[str] = None
    pesticide_name: Optional[str] = None
    active_ingredient: Optional[str] = None
    formulation: Optional[str] = None
    explicit_dose_text: Optional[str] = None
    safety_text: Optional[str] = None
    quality_control_status: Optional[str] = None
    source_page: int
    source_section: str
    source_excerpt: str
    confidence: float
    reviewed: bool


class PestAlertsResponse(BaseModel):
    district: Optional[str] = None
    crop: Optional[str] = None
    category: Optional[str] = None
    source_status: str
    alerts: List[PestAlertItem]


class PestSourceInfo(BaseModel):
    title: str
    year: str
    filename: str
    ingestion_timestamp: Optional[str] = None
    page_count: int
    num_facts: int
    num_review_queue: int
    num_chunks: int
    status: str


class PestSourcesResponse(BaseModel):
    sources: List[PestSourceInfo]


class AdvisoryResponse(BaseModel):
    crop: Optional[str] = None
    pest: Optional[str] = None
    district: Optional[str] = None
    status: str
    source_status: str
    matched: bool
    reason: Optional[str] = None
    recommendations: List[str]
    dose_guidance: Optional[str] = None
    safety_notice: Optional[str] = None
    citations: List[PestCitation] = []
    updated_at: str


class AdvisoryRequest(BaseModel):
    crop: Optional[str] = Field(None, min_length=1, max_length=100)
    pest: Optional[str] = Field(None, min_length=1, max_length=100)
    district: Optional[str] = Field(None, min_length=1, max_length=100)

    @field_validator("crop", "pest", "district", mode="before")
    @classmethod
    def _strip_optional(cls, value: Optional[str]) -> Optional[str]:
        if isinstance(value, str):
            return value.strip() or None
        return value

    @model_validator(mode="after")
    def _require_at_least_one(self):
        if not self.crop and not self.pest and not self.district:
            raise ValueError("At least one of crop, pest, or district is required.")
        return self


class ScanResponse(BaseModel):
    scan_id: str
    predicted_class: str
    confidence: float
    model_version: str
    uncertain: bool
    warning: Optional[str] = None
    scanned_at: str


class DistrictListResponse(BaseModel):
    districts: List[str]


class SatelliteRecord(BaseModel):
    year: int
    month: int
    district: str
    normalized_district: str
    ndvi_mean: Optional[float] = None
    ndvi_median: Optional[float] = None
    ndwi_mean: Optional[float] = None
    ndwi_median: Optional[float] = None
    valid_pixel_count: Optional[int] = None
    observation_count: Optional[int] = None
    cloud_or_quality_fraction: Optional[float] = None
    satellite_source: str
    product_id: str
    spatial_scale_m: int
    period_start: str
    period_end: str
    data_status: str
    no_coverage_flag: bool
    quality_flag: str
    source_processing_timestamp: str
    attention_status: str
    attention_evidence: str


class SatelliteDistrictItem(BaseModel):
    district: str
    normalized_district: str
    has_authoritative_polygon: bool
    data_status: str
    coverage_percentage: str


class SatelliteDistrictsResponse(BaseModel):
    total_districts: int
    districts: List[SatelliteDistrictItem]


class SatelliteHistoryResponse(BaseModel):
    district: str
    normalized_district: str
    total_records: int
    start_period: Optional[str] = None
    end_period: Optional[str] = None
    records: List[SatelliteRecord]


class SatelliteCoverageResponse(BaseModel):
    district: str
    normalized_district: str
    has_authoritative_polygon: bool
    total_expected_months: int
    months_with_satellite_data: int
    coverage_percentage: str
    data_status: str
    polygon_source: str
    notes: str


# ─── Open-Meteo Live Weather & Forecast Models ──────────────────────────────


class WeatherCurrentData(BaseModel):
    district: str
    normalized_district: str
    latitude: float
    longitude: float
    status: str
    temperature_c: Optional[float] = None
    humidity_percent: Optional[float] = None
    precipitation_mm: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    wind_gusts_kmh: Optional[float] = None
    weather_code: Optional[int] = None
    weather_description: Optional[str] = None
    fetched_at: Optional[str] = None
    expires_at: Optional[str] = None
    cache_status: Optional[str] = None
    source: str = "Open-Meteo / ECMWF IFS / DWD ICON"
    attribution: str = "Weather data by Open-Meteo.com under CC BY 4.0"
    is_mock: bool = False
    warning: Optional[str] = None


class HourlyForecastItem(BaseModel):
    time: str
    temperature_2m: Optional[float] = None
    relative_humidity_2m: Optional[float] = None
    dewpoint_2m: Optional[float] = None
    precipitation: Optional[float] = None
    vapour_pressure_deficit: Optional[float] = None
    et0_fao_evapotranspiration: Optional[float] = None
    wind_speed_10m: Optional[float] = None
    wind_gusts_10m: Optional[float] = None
    weather_code: Optional[int] = None
    soil_temperature_0cm: Optional[float] = None
    soil_temperature_6cm: Optional[float] = None
    soil_temperature_18cm: Optional[float] = None
    soil_moisture_0_to_1cm: Optional[float] = None
    soil_moisture_1_to_3cm: Optional[float] = None
    soil_moisture_3_to_9cm: Optional[float] = None
    soil_moisture_9_to_27cm: Optional[float] = None
    shortwave_radiation: Optional[float] = None
    direct_normal_irradiance: Optional[float] = None


class DailyForecastItem(BaseModel):
    date: str
    temperature_2m_max: Optional[float] = None
    temperature_2m_min: Optional[float] = None
    precipitation_sum: Optional[float] = None
    precipitation_probability_max: Optional[float] = None
    shortwave_radiation_sum: Optional[float] = None
    et0_fao_evapotranspiration: Optional[float] = None


class WeatherForecastResponse(BaseModel):
    district: str
    normalized_district: str
    latitude: float
    longitude: float
    status: str
    forecast_days: int
    fetched_at: Optional[str] = None
    expires_at: Optional[str] = None
    cache_status: Optional[str] = None
    daily: List[DailyForecastItem] = Field(default_factory=list)
    hourly: List[HourlyForecastItem] = Field(default_factory=list)
    source: str = "Open-Meteo / ECMWF IFS / DWD ICON"
    attribution: str = "Weather data by Open-Meteo.com under CC BY 4.0"
    warning: Optional[str] = None


# ─── AMIS Punjab Market Price Models ───────────────────────────────────────


class MarketCommodityItem(BaseModel):
    commodity_id: int
    commodity_name: str
    default_unit: str = "Rs/100Kg"
    status: str = "allowlisted_poc"


class MarketCommoditiesResponse(BaseModel):
    total_commodities: int
    commodities: List[MarketCommodityItem]


class MarketPriceItem(BaseModel):
    record_id: str
    price_date: str
    source_displayed_date: Optional[str] = None
    province: str = "Punjab"
    district: Optional[str] = None
    market_name: str
    market_id_or_source_label: Optional[str] = None
    commodity_name: str
    commodity_id: int
    variety: Optional[str] = "Standard"
    min_price_raw: Optional[str] = None
    max_price_raw: Optional[str] = None
    fqp_price_raw: Optional[str] = None
    quantity_raw: Optional[str] = None
    unit_raw: Optional[str] = None
    min_price_pkr: Optional[float] = None
    max_price_pkr: Optional[float] = None
    fqp_price_pkr: Optional[float] = None
    quantity: Optional[float] = None
    unit: str = "Rs/100Kg"
    source_name: str = "Official AMIS Punjab"
    source_url: str
    retrieved_at: str
    parser_version: str = "amis_poc_v1"
    data_status: str
    validation_status: str = "validated"
    source_age_days: Optional[int] = None
    retrieval_age_hours: Optional[float] = None
    warning: Optional[str] = None


class MarketLatestResponse(BaseModel):
    commodity: str
    market: Optional[str] = None
    total_records: int
    records: List[MarketPriceItem]


class MarketHistoryResponse(BaseModel):
    commodity: str
    market: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    total_records: int
    records: List[MarketPriceItem]


class MarketMoverItem(BaseModel):
    commodity_id: int
    commodity_name: str
    market_name: str
    current_price_pkr: float
    previous_price_pkr: Optional[float] = None
    price_change_pkr: Optional[float] = None
    price_change_pct: Optional[float] = None
    unit: str = "Rs/100Kg"
    price_date: str
    direction: str = "stable"  # "up", "down", "stable"


class MarketMoversResponse(BaseModel):
    generated_at_utc: str
    tracked_count: int
    gainers: List[MarketMoverItem]
    decliners: List[MarketMoverItem]
    data_status: str = "official_amis"


class LandUtilizationItem(BaseModel):
    district: str
    total_farm_area_acres: float
    cultivated_area_acres: float
    uncultivated_area_acres: float
    total_cropped_area_acres: float
    cultivated_share_pct: float
    cropping_intensity_pct: float
    wheat_area_acres: float
    wheat_share_pct: float
    rice_area_acres: float
    rice_share_pct: float
    cotton_area_acres: float
    cotton_share_pct: float
    sugarcane_area_acres: float
    sugarcane_share_pct: float
    maize_area_acres: float
    maize_share_pct: float
    fodder_area_acres: float
    fodder_share_pct: float
    orchard_area_acres: float
    orchard_share_pct: float
    kharif_total_acres: float
    rabi_total_acres: float
    data_source: str
    source_year: int


class LandUtilizationResponse(BaseModel):
    total_districts: int
    data: List[LandUtilizationItem]


class WaterAvailabilityItem(BaseModel):
    district: str
    total_cultivated_area_acres: float
    irrigated_area_acres: float
    unirrigated_area_acres: float
    irrigation_coverage_pct: float
    canal_only_acres: float
    canal_only_pct: float
    canal_and_tubewell_acres: float
    canal_and_tubewell_pct: float
    tubewell_only_acres: float
    tubewell_only_pct: float
    barani_rainfed_acres: float
    barani_share_pct: float
    sailaba_flood_acres: float
    groundwater_reliance_pct: float
    canal_surface_reliance_pct: float
    primary_irrigation_mode: str
    water_source_classification: str
    provincial_annual_canal_withdrawals_maf: float
    provincial_per_capita_water_m3_year: float
    falkenmark_stress_category: str
    data_source: str
    source_year: int


class WaterAvailabilityResponse(BaseModel):
    total_districts: int
    data: List[WaterAvailabilityItem]


class AgriGdpItem(BaseModel):
    fiscal_year: str
    region: str
    agri_gdp_share_pct: float
    agri_growth_rate_pct: float
    crops_subsector_share_pct: float
    important_crops_share_pct: float
    other_crops_share_pct: float
    livestock_subsector_share_pct: float
    forestry_subsector_share_pct: float
    fishing_subsector_share_pct: float
    punjab_agri_value_add_share_pct: float
    data_source: str


class AgriGdpResponse(BaseModel):
    total_records: int
    data: List[AgriGdpItem]


class AgriTradeItem(BaseModel):
    commodity_group: str
    commodity_name: str
    fiscal_year: str
    value_million_usd: float
    quantity_thousand_mt: float
    share_of_trade_pct: float
    partner_countries: str
    trade_type: str  # "export" or "import"
    data_source: str


class AgriTradeResponse(BaseModel):
    trade_type: str
    total_records: int
    total_value_million_usd: float
    data: List[AgriTradeItem]


class AgriTradeSummaryItem(BaseModel):
    fiscal_year: str
    total_agri_exports_million_usd: float
    total_agri_imports_million_usd: float
    agri_trade_balance_million_usd: float
    agri_share_of_total_national_exports_pct: float
    agri_share_of_total_national_imports_pct: float
    top_export_commodity: str
    top_import_commodity: str
    data_source: str


class AgriTradeSummaryResponse(BaseModel):
    total_records: int
    data: List[AgriTradeSummaryItem]


class NotificationItem(BaseModel):
    id: str
    user_id: str = "default_farmer"
    type: str  # "weather_alert", "market_mover", "advisory_reminder"
    title: str
    title_ur: str
    message: str
    message_ur: str
    body: Optional[str] = None
    severity: str = "info"  # "info", "warning", "critical"
    created_at_utc: str
    is_read: bool = False
    source_attribution: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if not self.body:
            self.body = self.message


class NotificationListResponse(BaseModel):
    total_notifications: int
    unread_count: int
    notifications: List[NotificationItem]


class NotificationUnreadCountResponse(BaseModel):
    unread_count: int
    total_notifications: int


class NotificationPreferences(BaseModel):
    user_id: str = "default_farmer"
    selected_district: str = "Lahore District"
    selected_market: str = "Lahore"
    selected_crops: List[str] = Field(default_factory=lambda: ["Wheat", "Rice Basmati Super (New)", "Cotton", "Potato Fresh"])
    alert_types: List[str] = Field(default_factory=lambda: ["weather", "market", "advisory"])
    channels: List[str] = Field(default_factory=lambda: ["in_app", "local"])
    enable_weather_alerts: bool = True
    enable_market_alerts: bool = True
    enable_advisory_reminders: bool = True
    heatwave_temp_threshold: float = 40.0
    rainfall_threshold_mm: float = 25.0
    frost_temp_threshold: float = 3.0
    market_mover_threshold_pct: float = 10.0
    fcm_token: Optional[str] = None
    fcm_status: str = "not_configured"
    updated_at_utc: str


class NotificationPreferencesResponse(BaseModel):
    preferences: NotificationPreferences


class NotificationPreferencesUpdateRequest(BaseModel):
    selected_district: Optional[str] = None
    selected_market: Optional[str] = None
    selected_crops: Optional[List[str]] = None
    alert_types: Optional[List[str]] = None
    channels: Optional[List[str]] = None
    enable_weather_alerts: Optional[bool] = None
    enable_market_alerts: Optional[bool] = None
    enable_advisory_reminders: Optional[bool] = None
    heatwave_temp_threshold: Optional[float] = None
    rainfall_threshold_mm: Optional[float] = None
    frost_temp_threshold: Optional[float] = None
    market_mover_threshold_pct: Optional[float] = None
    fcm_token: Optional[str] = None


class NotificationMarkReadRequest(BaseModel):
    notification_ids: Optional[List[str]] = None
    mark_all: bool = False


class NotificationMarkReadResponse(BaseModel):
    marked_count: int
    success: bool = True


class NotificationEvaluateResponse(BaseModel):
    evaluated_at_utc: str
    new_alerts_count: int
    new_alerts: List[NotificationItem]








