# PlantVillage Dataset Report

**Source:** Kaggle `emmarex/plantdisease`
**Local root:** `C:\Users\R Y Z E N\.cache\kagglehub\datasets\emmarex\plantdisease\versions\1\PlantVillage`
**Source dataset tag:** `PlantVillage`

## Summary

| Metric | Value |
|--------|-------|
| Total images scanned | 20638 |
| Valid (clean) images | 20638 |
| Corrupt / unreadable | 0 |
| Classes | 15 |
| Crops | 3 |
| Grayscale (flagged) | 0 |

## Class Distribution

| Class | Count |
|-------|-------|
| Pepper__bell___Bacterial_spot | 997 |
| Pepper__bell___healthy | 1478 |
| Potato___Early_blight | 1000 |
| Potato___Late_blight | 1000 |
| Potato___healthy | 152 |
| Tomato_Bacterial_spot | 2127 |
| Tomato_Early_blight | 1000 |
| Tomato_Late_blight | 1909 |
| Tomato_Leaf_Mold | 952 |
| Tomato_Septoria_leaf_spot | 1771 |
| Tomato_Spider_mites_Two_spotted_spider_mite | 1676 |
| Tomato__Target_Spot | 1404 |
| Tomato__Tomato_YellowLeaf__Curl_Virus | 3208 |
| Tomato__Tomato_mosaic_virus | 373 |
| Tomato_healthy | 1591 |

## Crop Distribution

| Crop | Count |
|------|-------|
| Pepper bell | 2475 |
| Potato | 2152 |
| Tomato | 16011 |

## Top 10 Largest Classes

| Rank | Class | Count |
|------|-------|-------|
| 1 | Tomato__Tomato_YellowLeaf__Curl_Virus | 3208 |
| 2 | Tomato_Bacterial_spot | 2127 |
| 3 | Tomato_Late_blight | 1909 |
| 4 | Tomato_Septoria_leaf_spot | 1771 |
| 5 | Tomato_Spider_mites_Two_spotted_spider_mite | 1676 |
| 6 | Tomato_healthy | 1591 |
| 7 | Pepper__bell___healthy | 1478 |
| 8 | Tomato__Target_Spot | 1404 |
| 9 | Potato___Early_blight | 1000 |
| 10 | Potato___Late_blight | 1000 |

## Image Size Distribution

- Width range: 256 - 256
- Height range: 256 - 256

| Size (WxH) | Count |
|-------------|-------|
| 256x256 | 20638 |

## Channel Distribution

| Channels | Count |
|----------|-------|
| 3 | 20638 |

## Folder Structure

Image root: `C:\Users\R Y Z E N\.cache\kagglehub\datasets\emmarex\plantdisease\versions\1\PlantVillage`

- `Pepper__bell___Bacterial_spot/` (997 images)
- `Pepper__bell___healthy/` (1478 images)
- `Potato___Early_blight/` (1000 images)
- `Potato___Late_blight/` (1000 images)
- `Potato___healthy/` (152 images)
- `Tomato_Bacterial_spot/` (2127 images)
- `Tomato_Early_blight/` (1000 images)
- `Tomato_Late_blight/` (1909 images)
- `Tomato_Leaf_Mold/` (952 images)
- `Tomato_Septoria_leaf_spot/` (1771 images)
- `Tomato_Spider_mites_Two_spotted_spider_mite/` (1676 images)
- `Tomato__Target_Spot/` (1404 images)
- `Tomato__Tomato_YellowLeaf__Curl_Virus/` (3208 images)
- `Tomato__Tomato_mosaic_virus/` (373 images)
- `Tomato_healthy/` (1591 images)

## Notes

- Class names preserved verbatim from source folder names.
- `crop` and `disease` fields parsed from folder name using `___` / `__` separators.
- `is_healthy = True` when disease field equals 'healthy' (case-insensitive).
- Grayscale images flagged but NOT excluded from clean manifest (channels=1).
- Train/val/test split column left empty for downstream assignment.
- Nested duplicate `PlantVillage/PlantVillage/` folder detected and skipped.
