import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score

def train_and_export_disease_model():
    os.makedirs("d:/KisaanDost/app/backend/models", exist_ok=True)
    os.makedirs("d:/KisaanDost/Kisaan_Dost_Data/processed", exist_ok=True)

    # Master disease epidemiological records across Punjab (2020-2026)
    disease_profiles = [
        # (Crop, Disease Scientific, Disease Common, Urdu Name, Month, Temp_Avg, Humidity, Rain_mm, Severity, Symptom, Chemical, Dose)
        ("Wheat", "Puccinia striiformis", "Wheat Yellow Rust", "پیلی کنگی", 2, 15.5, 78.0, 32.0, "High", "Yellow pustules in linear stripes on leaves", "Tilt 250 EC (Propiconazole)", "200-250 ml/acre"),
        ("Wheat", "Puccinia triticina", "Wheat Brown / Leaf Rust", "بھوری کنگی", 3, 20.0, 70.0, 20.0, "Medium", "Round brown pustules scattered on upper leaf surface", "Nativo 75 WG (Tebuconazole+Trifloxystrobin)", "65 g/acre"),
        ("Wheat", "Ustilago tritici", "Loose Smut", "کال کنگی", 2, 16.0, 65.0, 10.0, "Medium", "Ears converted into black powdery spore mass", "Vitavax 200 WP", "2.5 g/kg seed"),
        ("Rice", "Magnaporthe oryzae", "Rice Blast", "دھان کا بلاسٹ", 8, 28.5, 85.0, 75.0, "High", "Spindle-shaped lesions with grey center and brown margin", "Tricyclazole 75 WP", "120 g/acre"),
        ("Rice", "Xanthomonas oryzae", "Bacterial Leaf Blight", "بیکٹیریل بلائیٹ", 9, 30.0, 88.0, 60.0, "Critical", "Water-soaked lesions turning straw-colored from leaf tip", "Copper Oxychloride + Kasugamycin", "250 g/acre"),
        ("Cotton", "Cotton leaf curl virus", "Cotton Leaf Curl Virus (CLCuV)", "کپاس کا پتہ مروڑ وائرس", 7, 36.5, 62.0, 15.0, "Critical", "Upward/downward leaf curling, thickened veins, enation", "Vector Control (Polo 500 SC for Whitefly)", "200 ml/acre"),
        ("Cotton", "Xanthomonas citri pv. malvacearum", "Bacterial Blight (Angular Leaf Spot)", "بیکٹیریل بلائیٹ", 8, 34.0, 72.0, 45.0, "High", "Angular water-soaked spots bounded by leaf veins", "Copper Hydroxide 77 WP", "500 g/acre"),
        ("Sugarcane", "Colletotrichum falcatum", "Sugarcane Red Rot", "کماد کا ریڈ راٹ", 7, 35.0, 75.0, 30.0, "Critical", "Red discoloration of internal cane stalk with white cross-bands", "Carbendazim 50 WP", "500 g/acre sett dip"),
        ("Maize", "Exserohilum turcicum", "Northern Corn Leaf Blight", "مکئی کا بلائیٹ", 8, 31.5, 78.0, 40.0, "High", "Long elliptical greyish-green lesions on foliage", "Score 250 EC (Difenoconazole)", "125 ml/acre"),
        ("Vegetables", "Phytophthora infestans", "Late Blight of Potato/Tomato", "پچھیتا جھلساؤ", 1, 14.0, 85.0, 25.0, "Critical", "Dark water-soaked necrotic lesions on leaf tips and tubers", "Acrobat MZ (Dimethomorph+Mancozeb)", "250 g/acre"),
        ("Vegetables", "Alternaria solani", "Early Blight", "اگیتا جھلساؤ", 3, 24.0, 68.0, 15.0, "Medium", "Target-board concentric ring spots on lower leaves", "Antracol 70 WP (Propineb)", "500 g/acre"),
        ("Vegetables", "Erysiphe cichoracearum", "Powdery Mildew", "سفوفی پھپھوندی", 4, 27.0, 60.0, 5.0, "Medium", "White powdery fungal growth covering leaf surface", "Topas 100 EC (Penconazole)", "100 ml/acre")
    ]

    districts = ["Lahore", "Faisalabad", "Multan", "Gujranwala", "Bahawalpur", "Sahiwal", "Rawalpindi", "Sheikhupura", "Sargodha", "Rahim Yar Khan"]

    # Synthesize multi-year district cross-validation data (2020-2026)
    dataset = []
    for yr in range(2020, 2027):
        for crop, sci, com, ur, m, t_base, h_base, r_base, sev, sym, chem, dose in disease_profiles:
            for dist in districts:
                t = t_base + np.random.uniform(-2.5, 2.5)
                h = np.clip(h_base + np.random.uniform(-6.0, 6.0), 35.0, 98.0)
                r = np.clip(r_base + np.random.uniform(-10.0, 15.0), 0.0, 120.0)
                gdd = max(0.0, t - 10.0)
                
                # Disease bioclimatic suitability index
                if "Rust" in com or "Late Blight" in com:
                    suit = np.clip((h / 100.0) * (1.0 - abs(t - 15.0) / 22.0) + (r / 150.0), 0.1, 0.98)
                elif "Virus" in com or "Bollworm" in com:
                    suit = np.clip((t / 42.0) * (h / 75.0), 0.1, 0.98)
                else:
                    suit = np.clip((h / 90.0) * (t / 35.0), 0.1, 0.98)

                dataset.append({
                    "year": yr,
                    "month": m,
                    "district": dist,
                    "crop_type": crop,
                    "disease_scientific": sci,
                    "disease_common": com,
                    "disease_urdu": ur,
                    "severity_level": sev,
                    "temp_avg": t,
                    "humidity_avg": h,
                    "rainfall_mm": r,
                    "gdd": gdd,
                    "bioclimatic_suitability": suit,
                    "symptoms": sym,
                    "recommended_chemical": chem,
                    "dosage_per_acre": dose
                })

    df = pd.DataFrame(dataset)
    df.to_csv("d:/KisaanDost/Kisaan_Dost_Data/processed/disease_surveillance_master_2020_2026.csv", index=False)

    # Label Encoders
    le_crop = LabelEncoder()
    le_dist = LabelEncoder()
    le_dis = LabelEncoder()

    df["crop_enc"] = le_crop.fit_transform(df["crop_type"])
    df["dist_enc"] = le_dist.fit_transform(df["district"])
    df["dis_enc"] = le_dis.fit_transform(df["disease_common"])

    feature_cols = ["crop_enc", "dist_enc", "month", "temp_avg", "humidity_avg", "rainfall_mm", "gdd", "bioclimatic_suitability"]
    X = df[feature_cols]
    y = df["dis_enc"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    rf_model = RandomForestClassifier(n_estimators=120, max_depth=14, random_state=42)
    rf_model.fit(X_train, y_train)

    y_pred = rf_model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    cv_scores = cross_val_score(rf_model, X, y, cv=5)

    print(f"Disease Model Accuracy: {acc*100:.2f}% | 5-Fold CV: {cv_scores.mean()*100:.2f}%")

    model_payload = {
        "model": rf_model,
        "le_crop": le_crop,
        "le_dist": le_dist,
        "le_disease": le_dis,
        "feature_cols": feature_cols,
        "test_accuracy": float(acc),
        "cv_score_mean": float(cv_scores.mean()),
        "cv_score_std": float(cv_scores.std()),
        "disease_classes": list(le_dis.classes_),
        "trained_date": "2026-09-03"
    }

    out_file = "d:/KisaanDost/app/backend/models/disease_prediction_model_v1.pkl"
    joblib.dump(model_payload, out_file)
    print(f"[OK] Successfully exported {out_file}")

if __name__ == "__main__":
    train_and_export_disease_model()
