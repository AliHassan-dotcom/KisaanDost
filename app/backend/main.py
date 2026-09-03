"""Kisaan Dost MVP backend entrypoint."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.backend.routers import admin, agri_stats, auth, crop_health, dashboard, market, notifications, pest_alerts, profile, satellite, weather
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    description="Secure, modular farmer-facing MVP for Kisaan Dost.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_prefix = settings.api_prefix
app.include_router(auth.router, prefix=f"{api_prefix}")
app.include_router(profile.router, prefix=f"{api_prefix}")
app.include_router(dashboard.router, prefix=f"{api_prefix}")
app.include_router(weather.router, prefix=f"{api_prefix}")
app.include_router(satellite.router, prefix=f"{api_prefix}")
app.include_router(crop_health.router, prefix=f"{api_prefix}")
app.include_router(pest_alerts.router, prefix=f"{api_prefix}")
app.include_router(market.router, prefix=f"{api_prefix}")
app.include_router(agri_stats.router, prefix=f"{api_prefix}")
app.include_router(notifications.router, prefix=f"{api_prefix}")
app.include_router(admin.router, prefix=f"{api_prefix}")


@app.get("/health")
async def health():
    return {"status": "ok", "environment": settings.environment}


@app.get("/api/health")
async def api_health():
    return {"status": "ok", "environment": settings.environment}


@app.get("/api/v1/health/db")
async def health_db():
    from app.db.session import is_db_connected
    connected = is_db_connected()
    return {
        "status": "connected" if connected else "degraded",
        "database_connected": connected,
        "use_database": settings.use_database,
        "engine": "postgresql" if settings.database_url and "postgres" in settings.database_url else "sqlite_fallback",
    }



frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
frontend_dir.mkdir(parents=True, exist_ok=True)

# Provide a fallback index.html if the frontend build is missing.
_fallback_index = frontend_dir / "index.html"
if not _fallback_index.exists():
    _fallback_index.write_text(
        "<!DOCTYPE html><html><head><title>Kisaan Dost</title></head>"
        "<body><h1>Kisaan Dost MVP</h1><p>Frontend is not yet built.</p></body></html>",
        encoding="utf-8",
    )

app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"success": False, "error": {"message": str(exc)}},
    )
