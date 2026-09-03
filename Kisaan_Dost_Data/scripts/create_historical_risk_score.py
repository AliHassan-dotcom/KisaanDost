#!/usr/bin/env python3
"""Create processed/Punjab_Monthly_Risk_Score_2022_2026.csv and
reports/risk_trends_2022_2026.png.

Reads processed/Punjab_Monthly_Features_2022_2026.csv and computes a
transparent, rule-based Punjab-wide crop-stress risk score (0-1). This is NOT a
machine-learning model and NOT a disease-detection model.

Weights and thresholds (approved 2026-08-29):
  NDVI 0.25 | NDWI 0.15 | soil moisture 0.25 | rainfall 0.20 | temperature 0.15
Component severities are clamped to [0, 1]; the score is the weighted mean.
Baselines and expected month-over-month changes are derived from 2022-2025.
For 2026-08 (suspicious zero rainfall) the rainfall component is excluded and
the remaining weights renormalized (sum / 0.80).
"""

from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FEATURES_FILE = BASE_DIR / "processed" / "Punjab_Monthly_Features_2022_2026.csv"
OUT_FILE = BASE_DIR / "processed" / "Punjab_Monthly_Risk_Score_2022_2026.csv"
CHART_FILE = BASE_DIR / "reports" / "risk_trends_2022_2026.png"

WEIGHTS = {"ndvi": 0.25, "ndwi": 0.15, "soil": 0.25, "rain": 0.20, "temp": 0.15}
SUSPICIOUS_MONTH = (2026, 8)

# Full-stress denominators (severity = 1 when reached)
NDVI_BELOW_DEN = 0.20    # NDVI at <= 80% of baseline
NDVI_DECLINE_DEN = 0.10  # decline 0.10 worse than the seasonal norm
NDWI_BELOW_DEN = 0.10    # NDWI 0.10 more negative than baseline
NDWI_DECLINE_DEN = 0.08
SM_BELOW_DEN = 0.05      # soil moisture 0.05 m3/m3 below baseline
RAIN_BELOW_DEN = 0.60    # rainfall at <= 40% of normal
TEMP_ABOVE_DEN = 3.0     # monthly mean +3 C above baseline

SUSPICIOUS_ACTION = "verify rainfall source before using this month for drought conclusions"

LOW_ACTION = ("No immediate action; conditions near seasonal normal - "
              "continue routine monitoring.")

MEDIUM_ACTIONS = {
    "ndvi": "Monitor crop vigor; inspect fields for stress symptoms.",
    "ndwi": "Monitor surface-water availability; check irrigation supplies.",
    "soil": "Check soil moisture in the field; plan irrigation and conserve water.",
    "rain": "Monitor water reserves; schedule supplemental irrigation if dryness persists.",
    "temp": "Watch for heat stress; adjust irrigation timing to cooler hours.",
}

HIGH_ACTIONS = {
    "ndvi": "Alert: vegetation-stress indicators high - assess crop condition in the field.",
    "ndwi": "Alert: drought-stress indicators high - issue farmer advisory; prioritize irrigation and water conservation.",
    "soil": "Alert: drought-stress indicators high - issue farmer advisory; prioritize irrigation and water conservation.",
    "rain": "Alert: drought-stress indicators high - issue farmer advisory; prioritize irrigation and water conservation.",
    "temp": "Alert: heat-stress indicators high - issue heat advisory; protect crops and livestock.",
}

RISK_COLS = ["risk_score", "risk_level", "main_risk_reason", "recommended_action"]


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def load_features():
    with open(FEATURES_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        rows = list(reader)
    data = {(int(r["year"]), int(r["month"])): r for r in rows}
    return header, rows, data


def main() -> int:
    header, rows, data = load_features()

    BASELINE_YEARS = (2022, 2023, 2024, 2025)

    def baseline(col: str, month: int) -> float:
        vals = [float(data[(y, month)][col]) for y in BASELINE_YEARS
                if (y, month) in data]
        return sum(vals) / len(vals)

    b_ndvi = {m: baseline("NDVI_mean", m) for m in range(1, 13)}
    b_ndwi = {m: baseline("NDWI_mean", m) for m in range(1, 13)}
    b_rain = {m: baseline("rainfall_total_mm", m) for m in range(1, 13)}
    b_temp = {m: baseline("temp_mean_c", m) for m in range(1, 13)}
    b_sm1 = {m: baseline("soil_moisture_0_7cm", m) for m in range(1, 13)}
    b_sm2 = {m: baseline("soil_moisture_7_28cm", m) for m in range(1, 13)}

    def expected_change(bmap: dict, m: int) -> float:
        return bmap[m] - bmap[m - 1 if m > 1 else 12]

    out_rows = []
    level_counts = {"Low": 0, "Medium": 0, "High": 0}

    for r in rows:
        y, m = int(r["year"]), int(r["month"])
        suspicious = (y, m) == SUSPICIOUS_MONTH

        ndvi = float(r["NDVI_mean"])
        ndwi = float(r["NDWI_mean"])
        rain = float(r["rainfall_total_mm"])
        temp = float(r["temp_mean_c"])
        sm1 = float(r["soil_moisture_0_7cm"])
        sm2 = float(r["soil_moisture_7_28cm"])

        subs = {}

        s_below = clamp01((1.0 - ndvi / b_ndvi[m]) / NDVI_BELOW_DEN)
        sub_below = ("ndvi", s_below,
                     f"NDVI below baseline ({ndvi / b_ndvi[m] * 100:.0f}% of normal)")
        s_ndvi, reason_ndvi = s_below, sub_below[2]
        if r["ndvi_change_monthly"] != "":
            abn = expected_change(b_ndvi, m) - float(r["ndvi_change_monthly"])
            s_dec = clamp01(abn / NDVI_DECLINE_DEN)
            if s_dec > s_ndvi:
                s_ndvi, reason_ndvi = s_dec, "NDVI decline vs seasonal norm"
        subs["ndvi"] = (s_ndvi, reason_ndvi)

        s_below = clamp01((b_ndwi[m] - ndwi) / NDWI_BELOW_DEN)
        s_ndwi, reason_ndwi = s_below, "NDWI below baseline"
        if r["ndwi_change_monthly"] != "":
            abn = expected_change(b_ndwi, m) - float(r["ndwi_change_monthly"])
            s_dec = clamp01(abn / NDWI_DECLINE_DEN)
            if s_dec > s_ndwi:
                s_ndwi, reason_ndwi = s_dec, "NDWI decline vs seasonal norm"
        subs["ndwi"] = (s_ndwi, reason_ndwi)

        s1 = clamp01((b_sm1[m] - sm1) / SM_BELOW_DEN)
        s2 = clamp01((b_sm2[m] - sm2) / SM_BELOW_DEN)
        if s1 >= s2:
            subs["soil"] = (s1, f"soil moisture below baseline (0-7 cm, {sm1:.3f} vs {b_sm1[m]:.3f} m3/m3)")
        else:
            subs["soil"] = (s2, f"soil moisture below baseline (7-28 cm, {sm2:.3f} vs {b_sm2[m]:.3f} m3/m3)")

        if suspicious:
            subs["rain"] = (None, None)
        else:
            s_rain = clamp01((1.0 - rain / b_rain[m]) / RAIN_BELOW_DEN)
            subs["rain"] = (s_rain, f"rainfall {rain / b_rain[m] * 100:.0f}% of normal")

        s_temp = clamp01((temp - b_temp[m]) / TEMP_ABOVE_DEN)
        subs["temp"] = (s_temp, f"temperature {temp - b_temp[m]:+.1f} C vs normal")

        parts = {k: WEIGHTS[k] * v for k, (v, _) in subs.items() if v is not None}
        weight_sum = 0.80 if suspicious else 1.00
        score = round(min(1.0, sum(parts.values()) / weight_sum), 2)
        level = ("Low" if score <= 0.33 else
                 "Medium" if score <= 0.66 else "High")
        level_counts[level] += 1

        active = {k: v for k, v in parts.items() if v > 0}
        if active:
            main_driver = max(active, key=active.get)
            reason = subs[main_driver][1]
        else:
            main_driver = None
            reason = "no stress signals above baseline"
        if suspicious:
            reason += "; rainfall component excluded (suspicious zero value)"

        if suspicious:
            action = SUSPICIOUS_ACTION
        elif main_driver is None:
            action = LOW_ACTION
        elif level == "High":
            action = HIGH_ACTIONS[main_driver]
        elif level == "Medium":
            action = MEDIUM_ACTIONS[main_driver]
        else:
            action = LOW_ACTION

        out = dict(r)
        out["risk_score"] = f"{score:.2f}"
        out["risk_level"] = level
        out["main_risk_reason"] = reason
        out["recommended_action"] = action
        out_rows.append(out)

    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header + RISK_COLS)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"wrote {OUT_FILE.name}: {len(out_rows)} rows x {len(header) + len(RISK_COLS)} columns")
    print(f"risk levels: {level_counts}")
    for o in out_rows:
        if o["risk_level"] != "Low" or o["data_quality_flag"] != "":
            print(f"  {o['date']}  score={o['risk_score']}  {o['risk_level']:<6} "
                  f"[{o['data_quality_flag']}] {o['main_risk_reason']}")

    if not make_chart(out_rows):
        print("ERROR: chart generation failed", file=sys.stderr)
        return 1
    print(f"wrote {CHART_FILE}")
    return 0


def make_chart(rows: list) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.dates as mdates
        import matplotlib.pyplot as plt
        from matplotlib.patches import Patch
    except ImportError:
        print("matplotlib not available", file=sys.stderr)
        return False

    dates = [date(int(r["year"]), int(r["month"]), 1) for r in rows]
    scores = [float(r["risk_score"]) for r in rows]

    fig, ax = plt.subplots(figsize=(12, 5.5))
    ax.axhspan(0.0, 0.335, color="#2e7d32", alpha=0.10)
    ax.axhspan(0.335, 0.665, color="#f9a825", alpha=0.14)
    ax.axhspan(0.665, 1.0, color="#c62828", alpha=0.10)
    ax.axhline(0.335, color="gray", lw=0.7, ls=":")
    ax.axhline(0.665, color="gray", lw=0.7, ls=":")

    ax.plot(dates, scores, color="#1a56a0", lw=1.8, marker="o", ms=4,
            label="risk_score")

    aug26 = date(2026, 8, 1)
    ax.plot([aug26], [scores[-1]], marker="o", ms=9, mfc="none", mec="red",
            mew=1.6, ls="none", label="2026-08 (suspect rainfall)")
    ax.annotate("rainfall component excluded\n(suspicious zero value)",
                xy=(aug26, scores[-1]), xytext=(date(2025, 8, 1), 0.78),
                fontsize=8, color="red",
                arrowprops=dict(arrowstyle="->", color="red", lw=0.9))

    # Mark poor-coverage months
    poor_dates = [date(int(r["year"]), int(r["month"]), 1)
                  for r in rows if r["coverage_quality"] == "poor"]
    for pd in poor_dates:
        ax.axvline(pd, color="orange", lw=0.8, ls="-.", alpha=0.6)

    ax.set_ylim(-0.02, 1.02)
    ax.set_ylabel("crop-stress risk score (0-1)")
    ax.set_title("Punjab-wide crop-stress risk (indicative), monthly 2022-01 to 2026-08\n"
                 "transparent rule-based score - not a disease or ML model",
                 fontsize=11)
    ax.grid(alpha=0.3)
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)

    legend_items = [Patch(facecolor="#2e7d32", alpha=0.25, label="Low (0.00-0.33)"),
                    Patch(facecolor="#f9a825", alpha=0.30, label="Medium (0.34-0.66)"),
                    Patch(facecolor="#c62828", alpha=0.25, label="High (0.67-1.00)")]
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles=handles + legend_items, loc="upper left", fontsize=8,
              ncol=2)

    fig.text(0.99, 0.005,
             "2026 is partial (Jan-Aug); baselines from 2022-2025 monthly data; orange dash-dot marks poor land-cover coverage",
             ha="right", fontsize=7.5, color="gray")
    fig.tight_layout(rect=(0, 0.015, 1, 1))
    fig.savefig(CHART_FILE, dpi=150)
    plt.close(fig)
    return True


if __name__ == "__main__":
    sys.exit(main())
