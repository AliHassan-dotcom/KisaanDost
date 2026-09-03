# Unified Manifest Cleanup Report

## Summary

| Metric | Value |
|--------|-------|
| Total rows before cleanup | 21674 |
| Total rows after cleanup | 21659 |
| Duplicate clusters found | 15 |
| Duplicate rows (audit table) | 30 |
| Rows removed from training manifest | 15 |
| Citrus crop override applied | 1036 rows |
| Canonical labels before cleanup | 20 |
| Canonical labels after cleanup | 20 |
| Ambiguous labels remaining | 0 |

## Citrus Crop Override

Applied to `Citrus Leaves`: crop forced to `citrus`, disease taken from source folder name, and canonical labels normalized to lowercase `citrus_<disease>` form.

## Duplicate Cluster Summary

- Duplicate hash clusters: 15
- Rows involved in duplicate clusters: 30
- Representative rows kept for training: 15
- Duplicate rows excluded from training manifest: 15

## Ambiguous or Unmatched Labels

- None detected.

## Output Files

- Clean manifest: `data\processed\unified_crop_disease_manifest_clean.csv`
- Duplicate audit table: `data\processed\duplicate_audit_table.csv`
- Clean label mapping: `data\processed\label_mapping_table_clean.csv`

## Notes

- Raw unified manifest was not modified.
- De-duplication keeps the first image_path (lexicographic) per hash cluster.
- Rows with empty `hash_md5` are treated as unique and retained.
