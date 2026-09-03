"""Kisaan Dost API — FastAPI application entry point.

Contract docs: docs/RULES.md (API conventions), docs/ERROR_HANDLING.md (error envelope).
"""
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import AppError, error_envelope
from app.core.logging import setup_logging

setup_logging()
logger = structlog.get_logger()


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assigns a request_id and returns it in the X-Request-ID header (ERROR_HANDLING.md §6)."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", environment=settings.environment)
    yield
    logger.info("shutdown")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.warning("app_error", code=exc.code, path=str(request.url.path))
    return JSONResponse(
        status_code=exc.status_code,
        content=error_envelope(exc, request.headers.get("X-Request-ID")),
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_error", path=str(request.url.path))
    return JSONResponse(
        status_code=500,
        content=error_envelope(AppError(), request.headers.get("X-Request-ID")),
    )


app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health", tags=["ops"])
async def health() -> dict:
    return {"status": "ok", "environment": settings.environment}
