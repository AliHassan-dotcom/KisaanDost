"""SQLAlchemy ORM models for Kisaan Dost PostgreSQL database."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def _gen_uuid() -> str:
    return str(uuid.uuid4())


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(50), nullable=True)
    district = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now_utc, onupdate=_now_utc, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    scans = relationship("CropScan", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")


class CropScan(Base):
    __tablename__ = "crop_scans"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    image_path = Column(String(500), nullable=False)
    predicted_disease = Column(String(255), nullable=False)
    confidence_score = Column(Float, nullable=False)
    model_version = Column(String(50), default="v2", nullable=False)
    district = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now_utc, nullable=False)

    user = relationship("User", back_populates="scans")


class WeatherCache(Base):
    __tablename__ = "weather_cache"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    district = Column(String(100), nullable=False, index=True)
    temperature_2m = Column(Float, nullable=True)
    relative_humidity_2m = Column(Float, nullable=True)
    precipitation = Column(Float, default=0.0, nullable=True)
    wind_speed_10m = Column(Float, nullable=True)
    status = Column(String(50), default="live", nullable=False)
    source_url = Column(String(500), nullable=True)
    retrieved_at = Column(DateTime(timezone=True), default=_now_utc, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)


class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    price_date = Column(String(20), nullable=False, index=True)
    province = Column(String(100), default="Punjab", nullable=False)
    district = Column(String(100), nullable=True, index=True)
    market_name = Column(String(100), nullable=False, index=True)
    market_id_or_source_label = Column(String(100), nullable=True)
    commodity_name = Column(String(100), nullable=False, index=True)
    commodity_id = Column(Integer, nullable=True)
    variety = Column(String(100), nullable=True)
    min_price_pkr = Column(Float, nullable=True)
    max_price_pkr = Column(Float, nullable=True)
    fqp_price_pkr = Column(Float, nullable=True)
    quantity = Column(Float, nullable=True)
    unit = Column(String(50), default="100 Kg", nullable=False)
    source_name = Column(String(100), default="AMIS Punjab", nullable=False)
    source_url = Column(String(500), nullable=True)
    source_displayed_date = Column(String(50), nullable=True)
    retrieved_at = Column(DateTime(timezone=True), default=_now_utc, nullable=False)
    data_status = Column(String(50), default="live", nullable=False)
    validation_status = Column(String(50), default="pass", nullable=False)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    selected_crops = Column(JSON, default=list, nullable=False)
    primary_district = Column(String(100), default="Lahore District", nullable=False)
    primary_market = Column(String(100), default="Lahore", nullable=False)
    alert_types = Column(JSON, default=lambda: ["weather", "market", "advisory"], nullable=False)
    notification_channels = Column(JSON, default=lambda: ["in_app", "local"], nullable=False)
    threshold_settings = Column(JSON, default=dict, nullable=False)
    fcm_config_status = Column(String(50), default="not_configured", nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now_utc, onupdate=_now_utc, nullable=False)

    user = relationship("User", back_populates="preferences")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # "weather", "market", "advisory"
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    body_urdu = Column(Text, nullable=True)
    severity = Column(String(50), default="info", nullable=False)
    metadata_json = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now_utc, nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    source_attribution = Column(String(255), nullable=False)

    user = relationship("User", back_populates="notifications")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    endpoint = Column(String(255), nullable=False)
    status_code = Column(Integer, nullable=False)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now_utc, nullable=False, index=True)

    user = relationship("User", back_populates="audit_logs")


class MigrationMetadata(Base):
    __tablename__ = "migration_metadata"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    migration_name = Column(String(100), nullable=False)
    migrated_at = Column(DateTime(timezone=True), default=_now_utc, nullable=False)
    source_json_snapshot_hash = Column(String(64), nullable=False)
    row_counts = Column(JSON, default=dict, nullable=False)
    status = Column(String(50), default="success", nullable=False)
