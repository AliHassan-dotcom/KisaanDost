"""Unit tests for Phase 9 Agricultural GDP and Trade Data Pipeline."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent

p16_path = ROOT / "scripts" / "16_process_agri_gdp.py"
p16_spec = importlib.util.spec_from_file_location("p16", p16_path)
p16 = importlib.util.module_from_spec(p16_spec)
p16_spec.loader.exec_module(p16)

p17_path = ROOT / "scripts" / "17_process_agri_trade.py"
p17_spec = importlib.util.spec_from_file_location("p17", p17_path)
p17 = importlib.util.module_from_spec(p17_spec)
p17_spec.loader.exec_module(p17)

p18_path = ROOT / "scripts" / "18_validate_agri_trade.py"
p18_spec = importlib.util.spec_from_file_location("p18", p18_path)
p18 = importlib.util.module_from_spec(p18_spec)
p18_spec.loader.exec_module(p18)


def test_agri_gdp_processing():
    rows = p16.process_agri_gdp()
    assert len(rows) >= 6
    years = [r["fiscal_year"] for r in rows]
    assert "2023-24" in years
    assert "2024-25" in years

    y23 = next(r for r in rows if r["fiscal_year"] == "2023-24" and r["region"] == "Pakistan")
    assert y23["agri_gdp_share_pct"] == 24.0
    assert y23["livestock_subsector_share_pct"] > 50.0


def test_agri_trade_processing():
    res = p17.process_agri_trade()
    exports = res["exports"]
    imports = res["imports"]
    summaries = res["summary"]

    assert len(exports) >= 5
    assert len(imports) >= 5
    assert len(summaries) >= 1

    # Rice check
    rice = next(r for r in exports if "Rice" in r["commodity_name"])
    assert rice["value_million_usd"] > 0

    # Palm oil check
    palm = next(r for r in imports if "Palm Oil" in r["commodity_name"])
    assert palm["value_million_usd"] > 1000.0


def test_agri_trade_validation():
    assert p18.run_full_validation() is True
