# KisaanDost Pattern Discovery & Feature Engineering Report

## 1. Temporal & Climatic Thresholds Discovered:
- **Wheat Yellow Rust (*Puccinia striiformis*):** Highly active in Jan–March when mean temperature is 12°C–18°C and relative humidity exceeds 70%. Infection risk doubles after 25mm+ rainfall.
- **Cotton Pink Bollworm (*Pectinophora gossypiella*):** Peak infestation occurs July–September during boll formation under temperatures of 32°C–42°C.
- **Rice Yellow Stem Borer (*Scirpophaga incertulas*):** Peak adult emergence and dead-heart symptoms in August–September with humidity >80% and standing water.
- **Maize Fall Armyworm (*Spodoptera frugiperda*):** Active throughout Autumn maize vegetative stage (Aug–October) defoliating central whorls.

## 2. Engineered Predictive Features:
- `gdd`: Growing Degree Days baseline (T_base = 10°C).
- `weather_suitability`: Crop-specific non-linear bioclimatic suitability index (0.0 to 1.0).
- `temp_avg`, `temp_min`, `temp_max`, `humidity_avg`, `rainfall_mm`.
- Categorical features: `crop_type`, `location`, `growth_stage`, `soil_type`.
