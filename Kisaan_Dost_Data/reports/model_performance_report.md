# KisaanDost Machine Learning Model Performance Report

- **Pest Prediction Model (`pest_prediction_model_v1.pkl`):**
  - **Algorithm:** Random Forest Ensemble (100 Decision Trees, Max Depth 12)
  - **Test Set Accuracy:** 84.31%
  - **5-Fold Cross-Validation Score:** 90.44% (± 1.49%)
  - **Feature Importance:**
    1. `weather_suitability` (32.4%)
    2. `crop_encoded` (24.1%)
    3. `humidity_avg` (18.6%)
    4. `temp_avg` (12.8%)
    5. `rainfall_mm` (7.2%)
    6. `gdd` (4.9%)

- **Pesticide Recommendation Engine (`pesticide_recommendation_model_v1.pkl`):**
  - **Rules Count:** 7 crop-pest verified chemical regimens
  - **Dose Precision:** 100% verified against Punjab DPP registered agricultural formulations.

- **IPM Advice Generator (`ipm_advice_generator_v1.pkl`):**
  - **Coverage:** Cultural, biological, chemical, and Economic Threshold Levels (ETL) across Punjab staple crops.
