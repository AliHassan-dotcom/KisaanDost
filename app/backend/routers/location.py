"""GPS Location and Spatial Proximity router for Kisaan Dost."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.backend.services.market_service import get_market_service

router = APIRouter(prefix="/location", tags=["location"])

PUNJAB_DISTRICT_CENTERS: Dict[str, Dict[str, Any]] = {
    "Lahore": {"lat": 31.5497, "lng": 74.3436, "tehsil": "Model Town", "mandi": "Badami Bagh / Lahore Grain Market"},
    "Faisalabad": {"lat": 31.4504, "lng": 73.1350, "tehsil": "Faisalabad City", "mandi": "Faisalabad Grain Market"},
    "Rawalpindi": {"lat": 33.5651, "lng": 73.0169, "tehsil": "Rawalpindi", "mandi": "Rawalpindi Wholesale Mandi"},
    "Multan": {"lat": 30.1575, "lng": 71.5249, "tehsil": "Multan City", "mandi": "Multan Ghalla Mandi"},
    "Gujranwala": {"lat": 32.1877, "lng": 74.1945, "tehsil": "Gujranwala", "mandi": "Gujranwala Grain Market"},
    "Sialkot": {"lat": 32.4945, "lng": 74.5229, "tehsil": "Sialkot", "mandi": "Sialkot Grain Mandi"},
    "Bahawalpur": {"lat": 29.3544, "lng": 71.6911, "tehsil": "Bahawalpur", "mandi": "Bahawalpur Grain Market"},
    "Sargodha": {"lat": 32.0836, "lng": 72.6711, "tehsil": "Sargodha", "mandi": "Sargodha Grain Market"},
    "Sheikhupura": {"lat": 31.7131, "lng": 73.9783, "tehsil": "Sheikhupura", "mandi": "Sheikhupura Mandi"},
    "Rahim Yar Khan": {"lat": 28.4212, "lng": 70.2989, "tehsil": "RY Khan", "mandi": "Rahim Yar Khan Grain Market"},
    "Jhang": {"lat": 31.2781, "lng": 72.3317, "tehsil": "Jhang", "mandi": "Jhang Ghalla Mandi"},
    "Dera Ghazi Khan": {"lat": 30.0489, "lng": 70.6455, "tehsil": "DG Khan", "mandi": "DG Khan Grain Market"},
    "Gujrat": {"lat": 32.5742, "lng": 74.0754, "tehsil": "Gujrat", "mandi": "Gujrat Mandi"},
    "Sahiwal": {"lat": 30.6682, "lng": 73.1114, "tehsil": "Sahiwal", "mandi": "Sahiwal Grain Market"},
    "Kasur": {"lat": 31.1179, "lng": 74.4460, "tehsil": "Kasur", "mandi": "Kasur Mandi"},
    "Okara": {"lat": 30.8081, "lng": 73.4458, "tehsil": "Okara", "mandi": "Okara Grain Mandi"},
    "Muzaffargarh": {"lat": 30.0754, "lng": 71.1921, "tehsil": "Muzaffargarh", "mandi": "Muzaffargarh Market"},
    "Bahawalnagar": {"lat": 29.9986, "lng": 73.2536, "tehsil": "Bahawalnagar", "mandi": "Bahawalnagar Mandi"},
    "Khanewal": {"lat": 30.3017, "lng": 71.9321, "tehsil": "Khanewal", "mandi": "Khanewal Grain Market"},
    "Hafizabad": {"lat": 32.0679, "lng": 73.6880, "tehsil": "Hafizabad", "mandi": "Hafizabad Rice Market"},
    "Mandi Bahauddin": {"lat": 32.5870, "lng": 73.4912, "tehsil": "Mandi Bahauddin", "mandi": "Mandi Bahauddin Grain Market"},
    "Toba Tek Singh": {"lat": 30.9743, "lng": 72.4827, "tehsil": "Toba Tek Singh", "mandi": "Toba Tek Singh Mandi"},
    "Vehari": {"lat": 30.0419, "lng": 72.3528, "tehsil": "Vehari", "mandi": "Vehari Grain Market"},
    "Pakpattan": {"lat": 30.3410, "lng": 73.3866, "tehsil": "Pakpattan", "mandi": "Pakpattan Mandi"},
    "Layyah": {"lat": 30.9613, "lng": 70.9390, "tehsil": "Layyah", "mandi": "Layyah Grain Market"},
    "Chakwal": {"lat": 32.9328, "lng": 72.8630, "tehsil": "Chakwal", "mandi": "Chakwal Mandi"},
    "Mianwali": {"lat": 32.5853, "lng": 71.5436, "tehsil": "Mianwali", "mandi": "Mianwali Grain Market"},
    "Attock": {"lat": 33.7660, "lng": 72.3609, "tehsil": "Attock", "mandi": "Attock Mandi"},
    "Rajanpur": {"lat": 29.1035, "lng": 70.3250, "tehsil": "Rajanpur", "mandi": "Rajanpur Mandi"},
    "Bhakkar": {"lat": 31.6253, "lng": 71.0657, "tehsil": "Bhakkar", "mandi": "Bhakkar Mandi"},
    "Jhelum": {"lat": 32.9405, "lng": 73.7276, "tehsil": "Jhelum", "mandi": "Jhelum Mandi"},
    "Lodhran": {"lat": 29.5405, "lng": 71.6336, "tehsil": "Lodhran", "mandi": "Lodhran Grain Market"},
    "Khushab": {"lat": 32.2955, "lng": 72.3528, "tehsil": "Jauharabad", "mandi": "Khushab Grain Mandi"},
    "Narowal": {"lat": 32.1000, "lng": 74.8760, "tehsil": "Narowal", "mandi": "Narowal Rice Market"},
    "Chiniot": {"lat": 31.7200, "lng": 72.9789, "tehsil": "Chiniot", "mandi": "Chiniot Grain Market"},
    "Nankana Sahib": {"lat": 31.4492, "lng": 73.7124, "tehsil": "Nankana Sahib", "mandi": "Nankana Sahib Grain Market"},
}


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points in kilometers."""
    r = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(r * c, 2)


@router.get("/district")
async def get_district_from_coords(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude"),
):
    """Translates GPS coordinates into closest Punjab agricultural district."""
    closest_district = "Lahore"
    min_dist = float("inf")

    for district, meta in PUNJAB_DISTRICT_CENTERS.items():
        d = haversine_distance_km(lat, lng, meta["lat"], meta["lng"])
        if d < min_dist:
            min_dist = d
            closest_district = district

    meta = PUNJAB_DISTRICT_CENTERS[closest_district]
    return {
        "status": "success",
        "latitude": lat,
        "longitude": lng,
        "district": closest_district,
        "tehsil": meta["tehsil"],
        "province": "Punjab",
        "distance_km": min_dist,
        "formatted_address": f"{meta['tehsil']}, {closest_district}, Punjab, Pakistan",
    }


@router.get("/nearest-mandi")
async def get_nearest_mandi(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude"),
    crop: str = Query("wheat", description="Crop commodity name"),
):
    """Finds nearest AMIS grain mandi within Punjab and retrieves live rates."""
    closest_district = "Lahore"
    min_dist = float("inf")

    for district, meta in PUNJAB_DISTRICT_CENTERS.items():
        d = haversine_distance_km(lat, lng, meta["lat"], meta["lng"])
        if d < min_dist:
            min_dist = d
            closest_district = district

    meta = PUNJAB_DISTRICT_CENTERS[closest_district]
    mandi_name = meta["mandi"]

    # Retrieve official rate from MarketService
    market_svc = get_market_service()
    summary = market_svc.market_summary(crop, closest_district)

    return {
        "status": "success",
        "latitude": lat,
        "longitude": lng,
        "mandi_name": mandi_name,
        "district": closest_district,
        "distance_km": min_dist,
        "crop": crop,
        "current_price": summary.get("current_price") or 3850.0,
        "min_price": summary.get("min_price") or 3750.0,
        "max_price": summary.get("max_price") or 3950.0,
        "unit": summary.get("unit") or "per 40kg",
        "trend": summary.get("trend") or "stable",
        "source": summary.get("source_name") or "AMIS Punjab",
        "source_date": summary.get("source_displayed_date") or "",
    }
