# PlantVillage Training Report

## Setup

| Parameter | Value |
|-----------|-------|
| Model | ResNet-18 (ImageNet pretrained) |
| Approach | Feature extraction (frozen backbone + linear head) |
| Device | cpu |
| Optimizer | AdamW |
| Learning rate | 1e-4 |
| Weight decay | 1e-2 |
| Scheduler | CosineAnnealingLR |
| Loss | CrossEntropyLoss (class-weighted) |
| Epochs | 10 |
| Batch size | 32 |
| Image size | 224×224 |
| Seed | 42 |

## Dataset Splits

| Split | Count |
|-------|-------|
| Train | 14447 |
| Val | 3097 |
| Test | 3094 |
| Total | 20638 |
| Classes | 15 |

## Best Epoch

| Metric | Value |
|--------|-------|
| Best epoch | 10 |
| Train loss | 0.7650 |
| Train accuracy | 0.8074 |
| Val loss | 0.6724 |
| Val accuracy | 0.8534 |
| Val F1 (macro) | 0.8332 |

## Test Set Results

| Metric | Value |
|--------|-------|
| Accuracy | 0.8507 |
| Precision (macro) | 0.8157 |
| Recall (macro) | 0.8497 |
| F1 (macro) | 0.8281 |
| Samples evaluated | 3094 |

## Training History

| Epoch | Train Loss | Train Acc | Val Loss | Val Acc | Val F1 | LR | Time (s) |
|-------|-----------|-----------|----------|---------|--------|-----|----------|
| 1 | 2.2420 | 0.3199 | 1.6462 | 0.6810 | 0.6165 | 0.000100 | 1.3 |
| 2 | 1.5341 | 0.6230 | 1.1814 | 0.7862 | 0.7535 | 0.000098 | 1.1 |
| 3 | 1.1952 | 0.7184 | 0.9746 | 0.8105 | 0.7839 | 0.000091 | 1.1 |
| 4 | 1.0180 | 0.7559 | 0.8470 | 0.8292 | 0.8118 | 0.000080 | 1.1 |
| 5 | 0.9166 | 0.7774 | 0.7675 | 0.8421 | 0.8244 | 0.000066 | 1.1 |
| 6 | 0.8536 | 0.7890 | 0.7292 | 0.8457 | 0.8240 | 0.000051 | 1.1 |
| 7 | 0.8089 | 0.7982 | 0.6984 | 0.8479 | 0.8285 | 0.000035 | 1.0 |
| 8 | 0.7815 | 0.8052 | 0.6810 | 0.8521 | 0.8331 | 0.000021 | 1.1 |
| 9 | 0.7716 | 0.8045 | 0.6759 | 0.8531 | 0.8319 | 0.000010 | 1.0 |
| 10 | 0.7650 | 0.8074 | 0.6724 | 0.8534 | 0.8332 | 0.000003 | 1.1 |

## Per-Class Test Metrics

| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|-----|---------|
| Pepper__bell___Bacterial_spot | 0.9091 | 0.9396 | 0.9241 | 149 |
| Pepper__bell___healthy | 0.9386 | 0.9683 | 0.9532 | 221 |
| Potato___Early_blight | 0.9000 | 0.9600 | 0.9290 | 150 |
| Potato___Late_blight | 0.8750 | 0.8867 | 0.8808 | 150 |
| Potato___healthy | 0.6364 | 0.9130 | 0.7500 | 23 |
| Tomato_Bacterial_spot | 0.8501 | 0.9248 | 0.8859 | 319 |
| Tomato_Early_blight | 0.5723 | 0.6067 | 0.5890 | 150 |
| Tomato_Late_blight | 0.8684 | 0.6899 | 0.7689 | 287 |
| Tomato_Leaf_Mold | 0.8214 | 0.8042 | 0.8127 | 143 |
| Tomato_Septoria_leaf_spot | 0.8143 | 0.7283 | 0.7689 | 265 |
| Tomato_Spider_mites_Two_spotted_spider_mite | 0.8359 | 0.8492 | 0.8425 | 252 |
| Tomato__Target_Spot | 0.7571 | 0.7571 | 0.7571 | 210 |
| Tomato__Tomato_YellowLeaf__Curl_Virus | 0.9595 | 0.9356 | 0.9474 | 481 |
| Tomato__Tomato_mosaic_virus | 0.5904 | 0.8750 | 0.7050 | 56 |
| Tomato_healthy | 0.9076 | 0.9076 | 0.9076 | 238 |

## Top Misclassified Pairs

| True Class | Predicted Class | Count |
|------------|-----------------|-------|
| Tomato_Late_blight | Tomato_Early_blight | 43 |
| Tomato__Target_Spot | Tomato_Spider_mites_Two_spotted_spider_mite | 19 |
| Tomato_Septoria_leaf_spot | Tomato_Bacterial_spot | 17 |
| Tomato_Early_blight | Tomato_Septoria_leaf_spot | 13 |
| Tomato__Target_Spot | Tomato_healthy | 13 |

## Confusion Matrix

- PNG: `reports/plantvillage_confusion_matrix.png`
- CSV: `reports/plantvillage_confusion_matrix.csv`
- Dimensions: 15×15

## Saved Artifacts

- Model weights: `D:\KisaanDost\Kisaan_Dost_Data\models\best_plantvillage_model.pt`
- Training history: `D:\KisaanDost\Kisaan_Dost_Data\models\training_history.csv`
- This report: `reports/plantvillage_training_report.md`

## Notes

- Feature-extraction approach: ResNet-18 backbone frozen, features pre-computed once.
- Classification head (Dropout(0.3) + Linear) trained on cached 512-dim features.
- Class weights computed as inverse frequency to handle imbalance.
- Best checkpoint selected by validation macro-F1.
- Test set never used for training or model selection.
- Feature extraction time: 561.5s.
- Classification-head training time: 11.0s.
- Total end-to-end training time: 573.0s.
