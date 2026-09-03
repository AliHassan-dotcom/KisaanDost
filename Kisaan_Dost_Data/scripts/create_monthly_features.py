#!/usr/bin/env python3
"""Create processed/Punjab_Monthly_Features.csv and reports/monthly_trends.png.

Reads processed/Punjab_Monthly_Clean.csv (never touches raw exports), adds the
approved feature columns, and renders the monthly trends chart.

Baselines are month-of-year means over the two complete years (2024, 2025).
2026 never contributes to its own baseline. 2026-08 rainfall stays exactly as
exported (0.0 mm) and is flagged suspicious, never filled or corrected.
"""

from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CLEAN_FILE = BASE_DIR / "processed" / "Punjab_Monthly_Clean.csv"
OUT_FILE = BASE_DIR / "processed" / "Punjab_Monthly_Features.csv"
CHART_FILE = BASE_DIR / "reports" / "monthly_trends.png"

PUNJAB_AREA_KM2 = 205_344.0
GOOD_THRESHOLD = 0.98   # class total >= 98% of Punjab area
MODERATE_THRESHOLD = 0.90
SUSPICIOUS_MONTH = (2026, 8)
BASELINE_YEARS = (2024, 2025)

LC_COLS = ["bare_km2", "built_km2", "crops_km2", "flooded_vegetation_km2",
           "grass_km2", "shrub_and_scrub_km2", "snow_and_ice_km2", "trees_km2",
           "water_km2"]

NEW_COLS = ["ndvi_change_monthly", "ndwi_change_monthly", "soil_moisture_change",
            "rainfall_anomaly", "temperature_anomaly", "landcover_total_km2",
            "coverage_quality", "data_quality_flag", "year_to_date"]


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

        if prev in data:
            out["ndvi_change_monthly"] = f"{float(r['NDVI_mean']) - float(data[prev]['NDVI_mean']):.6f}"
            out["ndwi_change_monthly"] = f"{float(r['NDWI_mean']) - float(data[prev]['NDWI_mean']):.6f}"
            out["soil_moisture_change"] = f"{float(r['soil_moisture_0_7cm']) - float(data[prev]['soil_moisture_0_7cm']):.6f}"
        else:
            out["ndvi_change_monthly"] = ""
            out["ndwi_change_monthly"] = ""
            out["soil_moisture_change"] = ""

        rain_b = baseline(data, "rainfall_total_mm", m)
        temp_b = baseline(data, "temp_mean_c", m)
        out["rainfall_anomaly"] = f"{float(r['rainfall_total_mm']) - rain_b:.3f}"
        out["temperature_anomaly"] = f"{float(r['temp_mean_c']) - temp_b:.3f}"

        lc_total = sum(float(r[c]) for c in LC_COLS)
        out["landcover_total_km2"] = f"{lc_total:.1f}"
        ratio = lc_total / PUNJAB_AREA_KM2
        quality = ("good" if ratio >= GOOD_THRESHOLD
                   else "moderate" if ratio >= MODERATE_THRESHOLD
                   else "poor")
        out["coverage_quality"] = quality
        coverage_counts[quality] += 1

        out["data_quality_flag"] = ("suspicious_rainfall" if key == SUSPICIOUS_MONTH
                                    else "ok")
        out["year_to_date"] = "year_to_date" if y == 2026 else "complete"

        out_rows.append(out)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header + NEW_COLS)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"wrote {OUT_FILE.name}: {len(out_rows)} rows x {len(header) + len(NEW_COLS)} columns")
    print(f"coverage_quality: {coverage_counts}")
    print(f"suspicious rows: {sum(1 for o in out_rows if o['data_quality_flag'] != 'ok')}")

    print("\nJan-Aug year-over-year comparison (like-for-like window):")
    print(f"{'year':>5} {'rain_mm':>8} {'NDVI':>6} {'temp_C':>6} {'sm0_7':>6} {'sm7_28':>6}")
    for y in (2024, 2025, 2026):
        sub = [data[(y, m)] for m in range(1, 9) if (y, m) in data]
        n = len(sub)
        print(f"{y:>5} "
              f"{sum(float(r['rainfall_total_mm']) for r in sub):>8.1f} "
              f"{sum(float(r['NDVI_mean']) for r in sub) / n:>6.3f} "
              f"{sum(float(r['temp_mean_c']) for r in sub) / n:>6.2f} "
              f"{sum(float(r['soil_moisture_0_7cm']) for r in sub) / n:>6.3f} "
              f"{sum(float(r['soil_moisture_7_28cm']) for r in sub) / n:>6.3f}")

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

    fig, axes = plt.subplots(5, 1, figsize=(10, 13), sharex=True)
    fig.suptitle("Punjab-wide monthly conditions, 2024-01 to 2026-08 (Kisaan Dost)",
                 fontsize=13, fontweight="bold")

    panels = [
        ("NDVI_mean", "NDVI (unitless)", "#2e7d32"),
        ("NDWI_mean", "NDWI (unitless)", "#1565c0"),
        ("rainfall_total_mm", "Rainfall (mm/month)", "#6a1b9a"),
        ("temp_mean_c", "Mean temperature (\N{DEGREE SIGN}C)", "#c62828"),
        ("soil_moisture_0_7cm", "Soil moisture (m3/m3)", "#e65100"),
    ]

    for ax, (col, label, color) in zip(axes, panels):
        if col == "rainfall_total_mm":
            ax.bar(dates, series(col), width=22, color=color, alpha=0.75, label=label)
        else:
            ax.plot(dates, series(col), color=color, marker="o", ms=3.5, lw=1.6, label=label)
        ax.plot(dates, baseline_series(col), color="gray", lw=1.1, ls="--",
                alpha=0.85, label="2024-25 baseline")
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

    axes[-1].xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.setp(axes[-1].get_xticklabels(), rotation=45, ha="right", fontsize=8)
    fig.text(0.99, 0.005, "2026 is partial (Jan-Aug); red line marks 2026-08 (suspect rainfall)",
             ha="right", fontsize=7.5, color="gray")
    fig.tight_layout(rect=(0, 0.01, 1, 0.985))
    fig.savefig(CHART_FILE, dpi=150)
    plt.close(fig)
    return True


if __name__ == "__main__":
    sys.exit(main())
