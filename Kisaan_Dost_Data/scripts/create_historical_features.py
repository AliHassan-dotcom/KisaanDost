#!/usr/bin/env python3
"""Create processed/Punjab_Monthly_Features_2022_2026.csv and
reports/monthly_trends_2022_2026.png.

Reads processed/Punjab_Monthly_Clean_2022_2026.csv (never touches raw exports),
adds month-of-year baselines computed from 2022-2025, anomalies, and month-over-
month changes. 2026 never contributes to its own baseline. 2026-08 rainfall stays
exactly as exported (0.0 mm) and is flagged suspicious, never filled or corrected.
"""

from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CLEAN_FILE = BASE_DIR / "processed" / "Punjab_Monthly_Clean_2022_2026.csv"
OUT_FILE = BASE_DIR / "processed" / "Punjab_Monthly_Features_2022_2026.csv"
CHART_FILE = BASE_DIR / "reports" / "monthly_trends_2022_2026.png"

BASELINE_YEARS = (2022, 2023, 2024, 2025)
SUSPICIOUS_MONTH = (2026, 8)

NEW_COLS = [
    "ndvi_baseline", "ndwi_baseline", "rainfall_baseline_mm", "temperature_baseline_c",
    "soil_moisture_0_7cm_baseline", "soil_moisture_7_28cm_baseline",
    "ndvi_anomaly", "ndwi_anomaly",
    "ndvi_change_monthly", "ndwi_change_monthly",
    "rainfall_anomaly_mm", "temperature_anomaly_c",
    "soil_moisture_0_7cm_anomaly", "soil_moisture_7_28cm_anomaly",
    "soil_moisture_change",
]


def load_clean():
    with open(CLEAN_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        rows = list(reader)
    data = {(int(r["year"]), int(r["month"])): r for r in rows}
    return header, rows, data


def baseline(data: dict, col: str, month: int) -> float:
    vals = [float(data[(y, month)][col]) for y in BASELINE_YEARS if (y, month) in data]
    return sum(vals) / len(vals)


def main() -> int:
    header, rows, data = load_clean()
    out_rows = []
    coverage_counts = {"good": 0, "moderate": 0, "poor": 0}

    for r in rows:
        y, m = int(r["year"]), int(r["month"])
        key = (y, m)
        prev = (y, m - 1) if m > 1 else (y - 1, 12)
        out = dict(r)

        ndvi_b = baseline(data, "NDVI_mean", m)
        ndwi_b = baseline(data, "NDWI_mean", m)
        rain_b = baseline(data, "rainfall_total_mm", m)
        temp_b = baseline(data, "temp_mean_c", m)
        sm0_b = baseline(data, "soil_moisture_0_7cm", m)
        sm7_b = baseline(data, "soil_moisture_7_28cm", m)

        out["ndvi_baseline"] = f"{ndvi_b:.6f}"
        out["ndwi_baseline"] = f"{ndwi_b:.6f}"
        out["rainfall_baseline_mm"] = f"{rain_b:.3f}"
        out["temperature_baseline_c"] = f"{temp_b:.3f}"
        out["soil_moisture_0_7cm_baseline"] = f"{sm0_b:.6f}"
        out["soil_moisture_7_28cm_baseline"] = f"{sm7_b:.6f}"

        out["ndvi_anomaly"] = f"{float(r['NDVI_mean']) - ndvi_b:.6f}"
        out["ndwi_anomaly"] = f"{float(r['NDWI_mean']) - ndwi_b:.6f}"
        out["rainfall_anomaly_mm"] = f"{float(r['rainfall_total_mm']) - rain_b:.3f}"
        out["temperature_anomaly_c"] = f"{float(r['temp_mean_c']) - temp_b:.3f}"
        out["soil_moisture_0_7cm_anomaly"] = f"{float(r['soil_moisture_0_7cm']) - sm0_b:.6f}"
        out["soil_moisture_7_28cm_anomaly"] = f"{float(r['soil_moisture_7_28cm']) - sm7_b:.6f}"

        if prev in data:
            out["ndvi_change_monthly"] = f"{float(r['NDVI_mean']) - float(data[prev]['NDVI_mean']):.6f}"
            out["ndwi_change_monthly"] = f"{float(r['NDWI_mean']) - float(data[prev]['NDWI_mean']):.6f}"
            out["soil_moisture_change"] = f"{float(r['soil_moisture_0_7cm']) - float(data[prev]['soil_moisture_0_7cm']):.6f}"
        else:
            out["ndvi_change_monthly"] = ""
            out["ndwi_change_monthly"] = ""
            out["soil_moisture_change"] = ""

        coverage_counts[out["coverage_quality"]] += 1

        if key == SUSPICIOUS_MONTH:
            out["data_quality_flag"] = "suspicious_rainfall"

        out_rows.append(out)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header + NEW_COLS)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"wrote {OUT_FILE.name}: {len(out_rows)} rows x {len(header) + len(NEW_COLS)} columns")
    print(f"coverage_quality: {coverage_counts}")
    print(f"suspicious rows: {sum(1 for o in out_rows if o['data_quality_flag'] != '')}")

    if not make_chart(rows, data):
        print("ERROR: chart generation failed", file=sys.stderr)
        return 1
    print(f"wrote {CHART_FILE}")
    return 0


def make_chart(rows: list, data: dict) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.dates as mdates
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available", file=sys.stderr)
        return False

    dates = [date(int(r["year"]), int(r["month"]), 1) for r in rows]

    def series(col: str):
        return [float(r[col]) for r in rows]

    def baseline_series(col: str):
        return [baseline(data, col, int(r["month"])) for r in rows]

    fig, axes = plt.subplots(5, 1, figsize=(12, 14), sharex=True)
    fig.suptitle("Punjab-wide monthly conditions, 2022-01 to 2026-08 (Kisaan Dost)",
                 fontsize=13, fontweight="bold")

    panels = [
        ("NDVI_mean", "NDVI (unitless)", "#2e7d32"),
        ("NDWI_mean", "NDWI (unitless)", "#1565c0"),
        ("rainfall_total_mm", "Rainfall (mm/month)", "#6a1b9a"),
        ("temp_mean_c", "Mean temperature (°C)", "#c62828"),
        ("soil_moisture_0_7cm", "Soil moisture 0-7 cm (m3/m3)", "#e65100"),
    ]

    for ax, (col, label, color) in zip(axes, panels):
        if col == "rainfall_total_mm":
            ax.bar(dates, series(col), width=22, color=color, alpha=0.75, label=label)
        else:
            ax.plot(dates, series(col), color=color, marker="o", ms=3.5, lw=1.6, label=label)
        ax.plot(dates, baseline_series(col), color="gray", lw=1.1, ls="--",
                alpha=0.85, label="2022-25 baseline")
        ax.set_ylabel(label, fontsize=9)
        ax.grid(alpha=0.3)
        ax.legend(loc="best", fontsize=8)

    ax5 = axes[4]
    ax5.plot(dates, series("soil_moisture_7_28cm"), color="#00838f", marker="s",
             ms=3, lw=1.4, label="soil moisture 7-28 cm (m3/m3)")
    ax5.plot(dates, baseline_series("soil_moisture_7_28cm"), color="gray",
             lw=1.1, ls="--", alpha=0.85)
    ax5.legend(loc="best", fontsize=8)

    aug26 = date(2026, 8, 1)
    for ax in axes:
        ax.axvline(aug26, color="red", lw=1, ls=":", alpha=0.9)
        ax.axvspan(date(2026, 1, 1), aug26, color="gray", alpha=0.06)
    axes[2].annotate("0.0 mm (suspect)", xy=(aug26, 1.0), xytext=(date(2025, 10, 1), 90),
                     fontsize=8, color="red",
                     arrowprops=dict(arrowstyle="->", color="red", lw=0.9))

    # Mark poor-coverage months
    poor_dates = [date(int(r["year"]), int(r["month"]), 1)
                  for r in rows if r["coverage_quality"] == "poor"]
    for ax in axes:
        for pd in poor_dates:
            ax.axvline(pd, color="orange", lw=0.8, ls="-.", alpha=0.6)

    axes[-1].xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.setp(axes[-1].get_xticklabels(), rotation=45, ha="right", fontsize=8)
    fig.text(0.99, 0.005,
             "2026 is partial (Jan-Aug); red line marks 2026-08 (suspect rainfall); orange dash-dot marks poor land-cover coverage",
             ha="right", fontsize=7.5, color="gray")
    fig.tight_layout(rect=(0, 0.01, 1, 0.985))
    fig.savefig(CHART_FILE, dpi=150)
    plt.close(fig)
    return True


if __name__ == "__main__":
    sys.exit(main())
