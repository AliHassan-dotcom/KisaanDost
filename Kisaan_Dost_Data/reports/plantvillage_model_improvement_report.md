# PlantVillage Model Improvement Report

## Validation Selection

| Model | Validation macro-F1 | Status |
|-------|---------------------|--------|
| Baseline | 0.8332 | Immutable reference |
| V2 candidate | 0.9002 | Selected; strictly exceeded baseline |

The baseline metrics were read from `reports/plantvillage_training_report.md`; the baseline was not re-evaluated.

## Test-Set Comparison

| Metric | Baseline | V2 | Delta (V2 - Baseline) |
|--------|----------|----|-----------------------|
| Accuracy | 0.8507 | 0.8963 | +0.0456 |
| Precision (macro) | 0.8157 | 0.8713 | +0.0556 |
| Recall (macro) | 0.8497 | 0.8984 | +0.0487 |
| F1 (macro) | 0.8281 | 0.8825 | +0.0544 |

## Tomato Blight Confusion

| True → Predicted | Baseline count / support | Baseline rate | V2 count / support | V2 rate |
|------------------|--------------------------|---------------|--------------------|---------|
| Tomato Late blight → Tomato Early blight | 43 / 287 | 0.1498 | 27 / 287 | 0.0941 |

## Artifacts

- Comparison CSV: `reports/plantvillage_model_comparison.csv`
- Improvement report: `reports/plantvillage_model_improvement_report.md`
- V2 confusion matrix CSV: `reports/plantvillage_confusion_matrix_v2.csv`
- V2 confusion matrix PNG: `reports/plantvillage_confusion_matrix_v2.png`

## Leakage Guard

- V2 selection used validation macro-F1 only.
- The test split was evaluated once only after the validation gate accepted v2.
