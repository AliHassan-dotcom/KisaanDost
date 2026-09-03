# PlantVillage Clean Manifest Report

## Summary

| Metric | Value |
|--------|-------|
| Raw manifest rows | 20638 |
| Clean manifest rows | 20638 |
| Row count match | True |
| Duplicate paths | 0 |
| Classes | 15 |
| Crops | 3 |
| Healthy classes | 3 |
| Source dataset consistent | True |
| Split seed consistent | True |
| Split seed | 42 |

## Split Distribution

| Split | Count | Percentage |
|-------|-------|------------|
| train | 14447 | 70.0% |
| val | 3097 | 15.0% |
| test | 3094 | 15.0% |

## Per-Class Split Distribution

| Class | Total | Train | Val | Test |
|-------|-------|-------|-----|------|
| Pepper__bell___Bacterial_spot | 997 | 698 | 150 | 149 |
| Pepper__bell___healthy | 1478 | 1035 | 222 | 221 |
| Potato___Early_blight | 1000 | 700 | 150 | 150 |
| Potato___Late_blight | 1000 | 700 | 150 | 150 |
| Potato___healthy | 152 | 106 | 23 | 23 |
| Tomato_Bacterial_spot | 2127 | 1489 | 319 | 319 |
| Tomato_Early_blight | 1000 | 700 | 150 | 150 |
| Tomato_Late_blight | 1909 | 1336 | 286 | 287 |
| Tomato_Leaf_Mold | 952 | 666 | 143 | 143 |
| Tomato_Septoria_leaf_spot | 1771 | 1240 | 266 | 265 |
| Tomato_Spider_mites_Two_spotted_spider_mite | 1676 | 1173 | 251 | 252 |
| Tomato__Target_Spot | 1404 | 983 | 211 | 210 |
| Tomato__Tomato_YellowLeaf__Curl_Virus | 3208 | 2246 | 481 | 481 |
| Tomato__Tomato_mosaic_virus | 373 | 261 | 56 | 56 |
| Tomato_healthy | 1591 | 1114 | 239 | 238 |

## Class Balance: Raw vs Clean

| Class | Raw Count | Clean Count | Match |
|-------|-----------|-------------|-------|
| Pepper__bell___Bacterial_spot | 997 | 997 | True |
| Pepper__bell___healthy | 1478 | 1478 | True |
| Potato___Early_blight | 1000 | 1000 | True |
| Potato___Late_blight | 1000 | 1000 | True |
| Potato___healthy | 152 | 152 | True |
| Tomato_Bacterial_spot | 2127 | 2127 | True |
| Tomato_Early_blight | 1000 | 1000 | True |
| Tomato_Late_blight | 1909 | 1909 | True |
| Tomato_Leaf_Mold | 952 | 952 | True |
| Tomato_Septoria_leaf_spot | 1771 | 1771 | True |
| Tomato_Spider_mites_Two_spotted_spider_mite | 1676 | 1676 | True |
| Tomato__Target_Spot | 1404 | 1404 | True |
| Tomato__Tomato_YellowLeaf__Curl_Virus | 3208 | 3208 | True |
| Tomato__Tomato_mosaic_virus | 373 | 373 | True |
| Tomato_healthy | 1591 | 1591 | True |

## Class Mapping Table

| ID | Class Name | Crop | Disease | Healthy | Images |
|----|-----------|------|---------|---------|--------|
| 0 | Pepper__bell___Bacterial_spot | Pepper bell | Bacterial spot | False | 997 |
| 1 | Pepper__bell___healthy | Pepper bell | healthy | True | 1478 |
| 2 | Potato___Early_blight | Potato | Early blight | False | 1000 |
| 3 | Potato___Late_blight | Potato | Late blight | False | 1000 |
| 4 | Potato___healthy | Potato | healthy | True | 152 |
| 5 | Tomato_Bacterial_spot | Tomato | Bacterial spot | False | 2127 |
| 6 | Tomato_Early_blight | Tomato | Early blight | False | 1000 |
| 7 | Tomato_Late_blight | Tomato | Late blight | False | 1909 |
| 8 | Tomato_Leaf_Mold | Tomato | Leaf Mold | False | 952 |
| 9 | Tomato_Septoria_leaf_spot | Tomato | Septoria leaf spot | False | 1771 |
| 10 | Tomato_Spider_mites_Two_spotted_spider_mite | Tomato | Spider mites Two spotted spider mite | False | 1676 |
| 11 | Tomato__Target_Spot | Tomato | Target Spot | False | 1404 |
| 12 | Tomato__Tomato_YellowLeaf__Curl_Virus | Tomato | Tomato YellowLeaf Curl Virus | False | 3208 |
| 13 | Tomato__Tomato_mosaic_virus | Tomato | Tomato mosaic virus | False | 373 |
| 14 | Tomato_healthy | Tomato | healthy | True | 1591 |

## Missing Values

None — all required columns populated.

## Notes

- Stratified split: 70% train / 15% val / remainder test.
- Random seed: 42 (deterministic, reproducible).
- No rows dropped, no duplicates introduced, no image paths modified.
- `source_dataset` preserved as `PlantVillage` on every row.
- Raw manifest (`data/raw/plantvillage_manifest.csv`) not modified.
