"""Integration tests for migration scripts and rollback verification (Phase 12)."""

from __future__ import annotations

import importlib
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, MarketPrice, MigrationMetadata, User, UserPreference, WeatherCache

m_full = importlib.import_module("Kisaan_Dost_Data.scripts.25_run_full_migration")
m_rollback = importlib.import_module("Kisaan_Dost_Data.scripts.26_rollback_to_json")


def test_full_migration_execution():
    result = m_full.run_full_migration()
    assert result["status"] == "success"
    assert "snapshot_hash" in result
    assert "row_counts" in result
    counts = result["row_counts"]
    assert "weather_cache" in counts
    assert "market_prices" in counts
    assert counts["weather_cache"] >= 34


def test_rollback_to_json_execution():
    result = m_rollback.rollback_to_json_mode()
    assert result["status"] == "success"
    assert result["rollback_mode"] == "json_store_active"
    assert "backup_directory" in result
    assert len(result["files_backed_up"]) >= 1
