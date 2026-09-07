# PostgreSQL Database Setup Guide — Kisaan Dost

This guide explains how to set up, configure, and connect a PostgreSQL 14+ database for the Kisaan Dost backend.

---

## 1. Local Setup with Docker Compose (Recommended)

To start a managed PostgreSQL 16 instance with automated schema initialization:

```bash
docker compose up -d postgres
```

The database will initialize automatically using [`init.sql`](file:///d:/KisaanDost/init.sql).

### Connection Parameters:
- **Host:** `localhost`
- **Port:** `5432`
- **Database:** `kisaan_dost`
- **User:** `kisaan_user`
- **Password:** `<YOUR_POSTGRES_PASSWORD>`
- **Connection URL:** `postgresql://kisaan_user:<YOUR_POSTGRES_PASSWORD>@localhost:5432/kisaan_dost`

---

## 2. Running Data Migration

Once PostgreSQL is accessible, run the master migration script to migrate all users, crop scans, weather cache, market prices, and notifications:

```bash
python Kisaan_Dost_Data/scripts/25_run_full_migration.py
```

### Migration Verification:
Check migration health via the API endpoint:
```http
GET /api/v1/health/db
GET /api/v1/admin/migration-status
```

---

## 3. Backward Compatibility & Fallback Mode

If `DATABASE_URL` is omitted in `.env` or the database is temporarily unreachable:
1. The backend automatically logs a notice and activates the **JSON fallback store**.
2. All existing API endpoints remain 100% operational.
3. No data loss occurs.
