# Model Version Label Verification Report

- **Task:** Model-Version Metadata Inspection & Truthful Label Verification
- **Timestamp (UTC):** `2026-09-01T20:25:00+00:00`
- **Project Root:** `D:\KisaanDost`
- **Status:** **VERIFIED & RESOLVED**

---

## 1. Initial State & Investigation

### Root Cause of Legacy Label
During initial inspection of `app/backend/services/disease_service.py`, the `_model_version` string was computed as:
```python
checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
head_architecture = checkpoint.get("head_architecture") or "baseline"
...
_model_version = f"plantvillage_v2_{head_architecture}"
```

In the fine-tuned v2 model checkpoint (`Kisaan_Dost_Data/models/best_plantvillage_model_v2.pt`), `checkpoint.get("head_architecture")` is `None` because the fine-tuning script (`05_finetune_plantvillage_model.py`) fine-tuned the `layer4` and `fc` layers while retaining the baseline classification head structure. As a result, the code generated:
`plantvillage_v2_baseline`

This label was confusing because:
1. The active checkpoint is the **fine-tuned v2 model** (which achieved **89.63% test accuracy** and **0.8825 macro-F1** vs baseline's 85.07% / 0.8281).
2. Suffixing `_baseline` suggested it might be running the un-fine-tuned baseline model.

---

## 2. Integrity & Zero Weight Modification Guarantee

- The model checkpoint file `Kisaan_Dost_Data/models/best_plantvillage_model_v2.pt` (44,815,115 bytes) was **NOT modified, overwritten, retrained, or altered in any way**.
- Model weights, tensor definitions, normalization constants, and inference calculations remain 100% identical.

---

## 3. Implemented Safe Service Correction

In [`app/backend/services/disease_service.py`](file:///d:/KisaanDost/app/backend/services/disease_service.py), the version string formatting logic was updated to output a clean, truthful identifier:

```python
_model = model
_id_to_class = id_to_class
if head_architecture and head_architecture not in ("baseline", "default"):
    _model_version = f"plantvillage_v2_{head_architecture}"
else:
    _model_version = "plantvillage_v2"
```

### Resulting API Output
When `/api/v1/crop-health/scan` executes inference, the returned response now states:
```json
{
  "predicted_class": "Tomato_Septoria_leaf_spot",
  "confidence": 0.6249,
  "class_id": 9,
  "model_version": "plantvillage_v2",
  "uncertain": true,
  "warning": "Low confidence prediction. Please consult an extension worker for confirmation."
}
```

---

## 4. Automated Verification & Tests

1. **Targeted Unit Test:** [`tests/test_disease_model_inference.py`](file:///d:/KisaanDost/tests/test_disease_model_inference.py) explicitly asserts:
   ```python
   assert model_version == "plantvillage_v2"
   assert result["model_version"] == "plantvillage_v2"
   ```
2. **Flutter Model Contract Test:** [`mobile_app/test/unit/disease_prediction_test.dart`](file:///d:/KisaanDost/mobile_app/test/unit/disease_prediction_test.dart) tests that `DiseasePrediction.fromJson` parses `modelVersion: "plantvillage_v2"` and binds cleanly.
3. **End-to-End Live Flow Test:** [`tests/test_live_farmer_flow_e2e.py`](file:///d:/KisaanDost/tests/test_live_farmer_flow_e2e.py) asserts `scan_data["model_version"] == "plantvillage_v2"` in live integration.

---

## 5. Conclusion
The model version label is now **truthful, concise, and unambiguously identified as `plantvillage_v2`** across both FastAPI and Flutter layers without modifying any model weights or binary artifacts.
