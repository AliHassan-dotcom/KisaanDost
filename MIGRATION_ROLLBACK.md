# Database Migration Rollback & Recovery Guide

This document outlines the zero-data-loss rollback procedure for reverting from PostgreSQL back to the JSON MVP store.

---

## 1. Automated Rollback Verification Script

Run the automated rollback tool to snapshot the current state and verify JSON files:

```bash
python Kisaan_Dost_Data/scripts/26_rollback_to_json.py
```

This script:
1. Verifies that all original JSON stores (`users.json`, `user_preferences.json`, `notifications.json`) are intact.
2. Creates an immutable timestamped backup directory under `data/processed/backup_snapshot_<TIMESTAMP>/`.
3. Validates that record counts match between database and file representations.

---

## 2. Reverting Backend to JSON Store

To revert the running backend application to JSON store mode:
1. Open `.env` (or environment configuration).
2. Set:
   ```env
   USE_DATABASE=false
   # Or comment out DATABASE_URL
   # DATABASE_URL=
   ```
3. Restart the FastAPI service:
   ```bash
   uvicorn app.backend.main:app --host 0.0.0.0 --port 8000
   ```

---

## 3. Data Integrity & Retention Invariant

- Original JSON and CSV files remain untouched and operational.
- Database records remain safely in PostgreSQL for subsequent re-migration or debugging.
- No schema drops or destructive mutations are executed during rollback.
