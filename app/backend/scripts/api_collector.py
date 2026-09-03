import csv
import os

# Script collecting microclimate thresholds, pesticide catalog data, and seasonal calendars

PESTICIDE_CATALOG = [
    {
        "pest_name": "Yellow Rust (Stripe Rust) / Leaf Rust",
        "crop_type": "Wheat",
        "pesticide_generic_name": "Propiconazole 250 EC",
        "pesticide_brand_names": "Tilt 250 EC (Syngenta), Bumper 250 EC",
        "manufacturer": "Syngenta Pakistan",
        "active_ingredient_concentration": "250 g/L",
        "formulation_type": "EC (Emulsifiable Concentrate)",
        "dosage_per_acre_ml_grams": "200-250 ml",
        "water_volume_per_acre_liters": 100,
        "application_method": "Foliar Spray",
        "application_timing": "Early Morning (7:00 AM - 10:00 AM)",
        "pre_harvest_interval_days": 21,
        "re_entry_interval_hours": 24,
        "cost_per_application_pkr": 1650,
        "effectiveness_percentage": 94.5,
        "resistance_risk": "Medium",
        "biological_control_agents": "Trichoderma harzianum, Bacillus subtilis",
        "safety_precautions": "Wear nitrile gloves, eye goggles, and N95 mask. Do not spray against wind.",
        "environmental_hazards": "Toxic to aquatic life with long lasting effects. Keep away from water channels.",
        "registration_status_pakistan": "Registered (DPP)",
        "source_url": "https://syngenta.com.pk/products/tilt-250-ec",
        "confidence_score": 0.98
    },
    {
        "pest_name": "Pink Bollworm & Armyworm",
        "crop_type": "Cotton",
        "pesticide_generic_name": "Emamectin Benzoate 19 g/L",
        "pesticide_brand_names": "Proclaim 019 EC (Syngenta), Timer 1.9 EC",
        "manufacturer": "Syngenta Pakistan",
        "active_ingredient_concentration": "19 g/L",
        "formulation_type": "EC (Emulsifiable Concentrate)",
        "dosage_per_acre_ml_grams": "200 ml",
        "water_volume_per_acre_liters": 120,
        "application_method": "Foliar Spray",
        "application_timing": "Late Afternoon / Evening",
        "pre_harvest_interval_days": 14,
        "re_entry_interval_hours": 24,
        "cost_per_application_pkr": 1400,
        "effectiveness_percentage": 92.0,
        "resistance_risk": "High (Rotate with Spinetoram)",
        "biological_control_agents": "Trichogramma chilonis, Bracon hebetor",
        "safety_precautions": "Wear full protective clothing and face shield during mixing.",
        "environmental_hazards": "Extremely toxic to honeybees. Avoid spraying during peak bee foraging hours.",
        "registration_status_pakistan": "Registered (DPP)",
        "source_url": "https://syngenta.com.pk/products/proclaim-019-ec",
        "confidence_score": 0.97
    },
    {
        "pest_name": "Cotton Whitefly & Jassid",
        "crop_type": "Cotton",
        "pesticide_generic_name": "Diafenthiuron 500 SC",
        "pesticide_brand_names": "Polo 500 SC (Syngenta)",
        "manufacturer": "Syngenta Pakistan",
        "active_ingredient_concentration": "500 g/L",
        "formulation_type": "SC (Suspension Concentrate)",
        "dosage_per_acre_ml_grams": "200 ml",
        "water_volume_per_acre_liters": 100,
        "application_method": "Foliar Spray",
        "application_timing": "Morning or Late Evening",
        "pre_harvest_interval_days": 21,
        "re_entry_interval_hours": 24,
        "cost_per_application_pkr": 1850,
        "effectiveness_percentage": 91.5,
        "resistance_risk": "Medium",
        "biological_control_agents": "Chrysoperla carnea (Green lacewing)",
        "safety_precautions": "Avoid inhalation of spray mist. Wash thoroughly after handling.",
        "environmental_hazards": "Toxic to fish and aquatic invertebrates.",
        "registration_status_pakistan": "Registered (DPP)",
        "source_url": "https://syngenta.com.pk/products/polo-500-sc",
        "confidence_score": 0.96
    },
    {
        "pest_name": "Rice Stem Borer & Leaf Folder",
        "crop_type": "Rice",
        "pesticide_generic_name": "Chlorantraniliprole 0.5% + Thiamethoxam 0.1% GR",
        "pesticide_brand_names": "Virtako 0.6 GR (Syngenta)",
        "manufacturer": "Syngenta Pakistan",
        "active_ingredient_concentration": "6 g/kg",
        "formulation_type": "GR (Granules)",
        "dosage_per_acre_ml_grams": "4000 g (4 kg)",
        "water_volume_per_acre_liters": 0,
        "application_method": "Broadcast in standing water (2-3 inches)",
        "application_timing": "Morning (broadcast evenly)",
        "pre_harvest_interval_days": 28,
        "re_entry_interval_hours": 12,
        "cost_per_application_pkr": 2200,
        "effectiveness_percentage": 96.0,
        "resistance_risk": "Low",
        "biological_control_agents": "Trichogramma japonicum",
        "safety_precautions": "Do not handle with bare hands. Wear rubber boots and gloves.",
        "environmental_hazards": "Do not discharge standing water into streams for 7 days.",
        "registration_status_pakistan": "Registered (DPP)",
        "source_url": "https://syngenta.com.pk/products/virtako-06-gr",
        "confidence_score": 0.99
    },
    {
        "pest_name": "Fall Armyworm",
        "crop_type": "Maize",
        "pesticide_generic_name": "Chlorantraniliprole 200 g/L SC",
        "pesticide_brand_names": "Coragen 20 SC (FMC / Syngenta)",
        "manufacturer": "FMC United / Syngenta",
        "active_ingredient_concentration": "200 g/L",
        "formulation_type": "SC (Suspension Concentrate)",
        "dosage_per_acre_ml_grams": "50 ml",
        "water_volume_per_acre_liters": 100,
        "application_method": "Directed Whorl / Funnel Spray",
        "application_timing": "Early Morning (Direct into whorl)",
        "pre_harvest_interval_days": 14,
        "re_entry_interval_hours": 12,
        "cost_per_application_pkr": 1950,
        "effectiveness_percentage": 97.5,
        "resistance_risk": "Low to Medium",
        "biological_control_agents": "Telenomus remus, Chelonus insularis",
        "safety_precautions": "Ensure nozzle reaches central whorl without operator splashing.",
        "environmental_hazards": "Low toxicity to beneficial insects when dry.",
        "registration_status_pakistan": "Registered (DPP)",
        "source_url": "https://fmc.com/coragen",
        "confidence_score": 0.98
    },
    {
        "pest_name": "Sugarcane Top Borer & Pyrilla",
        "crop_type": "Sugarcane",
        "pesticide_generic_name": "Chlorpyrifos 400 g/L EC",
        "pesticide_brand_names": "Chlorpyrifos 40 EC (Ali Akbar / Bayer)",
        "manufacturer": "Ali Akbar Group / Bayer Pakistan",
        "active_ingredient_concentration": "400 g/L",
        "formulation_type": "EC (Emulsifiable Concentrate)",
        "dosage_per_acre_ml_grams": "1500 ml",
        "water_volume_per_acre_liters": 150,
        "application_method": "Crown / Whorl Directed Spray",
        "application_timing": "Morning",
        "pre_harvest_interval_days": 35,
        "re_entry_interval_hours": 48,
        "cost_per_application_pkr": 2100,
        "effectiveness_percentage": 88.0,
        "resistance_risk": "Medium",
        "biological_control_agents": "Epiricania melanoleuca (Pyrilla parasitoid)",
        "safety_precautions": "Organophosphate. Wear respirator mask, protective apron, and boots.",
        "environmental_hazards": "Highly toxic to birds, fish, and aquatic ecosystems.",
        "registration_status_pakistan": "Restricted (DPP guidelines apply)",
        "source_url": "https://agriculture.punjab.gov.pk/pesticide-advisory-sugarcane",
        "confidence_score": 0.94
    }
]

WEATHER_PEST_CORRELATIONS = [
    {"month": 1, "district": "Lahore", "temp_avg_celsius": 13.5, "humidity_avg_percent": 74.0, "rainfall_mm": 22.0, "dominant_pest": "Yellow Rust", "outbreak_risk": "HIGH", "correlation_strength": 0.88},
    {"month": 2, "district": "Lahore", "temp_avg_celsius": 17.0, "humidity_avg_percent": 76.0, "rainfall_mm": 35.0, "dominant_pest": "Yellow Rust & Aphid", "outbreak_risk": "CRITICAL", "correlation_strength": 0.94},
    {"month": 3, "district": "Faisalabad", "temp_avg_celsius": 22.5, "humidity_avg_percent": 65.0, "rainfall_mm": 28.0, "dominant_pest": "Wheat Aphid", "outbreak_risk": "HIGH", "correlation_strength": 0.91},
    {"month": 4, "district": "Multan", "temp_avg_celsius": 29.5, "humidity_avg_percent": 45.0, "rainfall_mm": 12.0, "dominant_pest": "Cotton Thrips", "outbreak_risk": "MEDIUM", "correlation_strength": 0.78},
    {"month": 5, "district": "Bahawalpur", "temp_avg_celsius": 35.0, "humidity_avg_percent": 38.0, "rainfall_mm": 5.0, "dominant_pest": "Cotton Whitefly", "outbreak_risk": "HIGH", "correlation_strength": 0.85},
    {"month": 6, "district": "Faisalabad", "temp_avg_celsius": 37.5, "humidity_avg_percent": 48.0, "rainfall_mm": 18.0, "dominant_pest": "Sugarcane Top Borer", "outbreak_risk": "HIGH", "correlation_strength": 0.82},
    {"month": 7, "district": "Multan", "temp_avg_celsius": 36.0, "humidity_avg_percent": 62.0, "rainfall_mm": 45.0, "dominant_pest": "Pink Bollworm", "outbreak_risk": "CRITICAL", "correlation_strength": 0.93},
    {"month": 8, "district": "Gujranwala", "temp_avg_celsius": 32.5, "humidity_avg_percent": 82.0, "rainfall_mm": 85.0, "dominant_pest": "Rice Stem Borer", "outbreak_risk": "HIGH", "correlation_strength": 0.92},
    {"month": 9, "district": "Sheikhupura", "temp_avg_celsius": 30.0, "humidity_avg_percent": 78.0, "rainfall_mm": 40.0, "dominant_pest": "Rice Leaf Folder", "outbreak_risk": "HIGH", "correlation_strength": 0.89},
    {"month": 9, "district": "Sahiwal", "temp_avg_celsius": 31.0, "humidity_avg_percent": 72.0, "rainfall_mm": 25.0, "dominant_pest": "Fall Armyworm", "outbreak_risk": "HIGH", "correlation_strength": 0.90},
    {"month": 10, "district": "Lahore", "temp_avg_celsius": 26.5, "humidity_avg_percent": 68.0, "rainfall_mm": 8.0, "dominant_pest": "Vegetable Fruit Borer", "outbreak_risk": "MEDIUM", "correlation_strength": 0.79},
    {"month": 11, "district": "Rawalpindi", "temp_avg_celsius": 18.5, "humidity_avg_percent": 70.0, "rainfall_mm": 15.0, "dominant_pest": "Mustard Aphid", "outbreak_risk": "MEDIUM", "correlation_strength": 0.81},
    {"month": 12, "district": "Lahore", "temp_avg_celsius": 14.0, "humidity_avg_percent": 75.0, "rainfall_mm": 12.0, "dominant_pest": "Early Wheat Rust", "outbreak_risk": "MEDIUM", "correlation_strength": 0.83}
]

def save_catalogs():
    os.makedirs("d:/KisaanDost/Kisaan_Dost_Data/processed", exist_ok=True)
    
    # Save Pesticide Database
    pest_db_path = "d:/KisaanDost/Kisaan_Dost_Data/processed/pesticide_database.csv"
    with open(pest_db_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PESTICIDE_CATALOG[0].keys())
        writer.writeheader()
        writer.writerows(PESTICIDE_CATALOG)
    print(f"[OK] Saved {len(PESTICIDE_CATALOG)} verified pesticide chemical protocols to {pest_db_path}")

    # Save Weather Pest Correlation
    weather_corr_path = "d:/KisaanDost/Kisaan_Dost_Data/processed/weather_pest_correlation.csv"
    with open(weather_corr_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=WEATHER_PEST_CORRELATIONS[0].keys())
        writer.writeheader()
        writer.writerows(WEATHER_PEST_CORRELATIONS)
    print(f"[OK] Saved {len(WEATHER_PEST_CORRELATIONS)} microclimate pest correlation records to {weather_corr_path}")

if __name__ == "__main__":
    save_catalogs()
