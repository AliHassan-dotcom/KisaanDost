"""Unit tests for SQLAlchemy models, relationships, and constraints in Phase 12."""

from __future__ import annotations

from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import (
    Base,
    CropScan,
    MarketPrice,
    MigrationMetadata,
    Notification,
    User,
    UserPreference,
    WeatherCache,
)


@pytest.fixture
def db_session():
    # Use in-memory SQLite for isolated model testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_user_and_preferences_cascade(db_session):
    user = User(
        id="test_u1",
        email="test_u1@example.com",
        password_hash="hashed_pw",
        full_name="Test Farmer",
        phone_number="+923001234567",
        district="Lahore District",
    )
    db_session.add(user)
    db_session.commit()

    pref = UserPreference(
        id="test_pref1",
        user_id=user.id,
        selected_crops=["Wheat", "Cotton"],
        primary_district="Lahore District",
        primary_market="Lahore",
        alert_types=["weather", "market"],
        notification_channels=["in_app", "local"],
        threshold_settings={"heatwave": 40.0},
        fcm_config_status="not_configured",
    )
    db_session.add(pref)
    db_session.commit()

    assert user.preferences is not None
    assert user.preferences.selected_crops == ["Wheat", "Cotton"]

    # Delete user and verify cascade
    db_session.delete(user)
    db_session.commit()

    assert db_session.query(UserPreference).filter(UserPreference.user_id == "test_u1").first() is None


def test_market_price_and_weather_cache_models(db_session):
    now = datetime.now(timezone.utc)
    mp = MarketPrice(
        id="mp_test_1",
        price_date="01-Sep-2026",
        province="Punjab",
        district="Lahore District",
        market_name="Lahore",
        commodity_name="Potato Fresh",
        min_price_pkr=4000.0,
        max_price_pkr=4400.0,
        fqp_price_pkr=4200.0,
        quantity=150.0,
        unit="100 Kg",
        source_name="AMIS Punjab",
        retrieved_at=now,
    )
    db_session.add(mp)

    wc = WeatherCache(
        id="wc_test_1",
        district="Lahore District",
        temperature_2m=32.5,
        relative_humidity_2m=45.0,
        precipitation=0.0,
        wind_speed_10m=11.2,
        status="live",
        retrieved_at=now,
    )
    db_session.add(wc)
    db_session.commit()

    fetched_mp = db_session.query(MarketPrice).filter(MarketPrice.id == "mp_test_1").first()
    assert fetched_mp is not None
    assert fetched_mp.fqp_price_pkr == 4200.0

    fetched_wc = db_session.query(WeatherCache).filter(WeatherCache.id == "wc_test_1").first()
    assert fetched_wc is not None
    assert fetched_wc.temperature_2m == 32.5


def test_migration_metadata_model(db_session):
    now = datetime.now(timezone.utc)
    meta = MigrationMetadata(
        id="meta_001",
        migration_name="001_initial_json_to_db_migration",
        migrated_at=now,
        source_json_snapshot_hash="abcd1234efgh5678",
        row_counts={"users": 2, "crop_scans": 5},
        status="success",
    )
    db_session.add(meta)
    db_session.commit()

    fetched = db_session.query(MigrationMetadata).filter(MigrationMetadata.id == "meta_001").first()
    assert fetched is not None
    assert fetched.source_json_snapshot_hash == "abcd1234efgh5678"
    assert fetched.row_counts["users"] == 2
