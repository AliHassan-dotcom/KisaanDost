"""Weather sync + alert threshold evaluation (PRD.md F3, ERROR_HANDLING.md §4)."""

from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=2, retry_backoff=True)
def sync_weather(self) -> None:
    """Hourly: fetch district forecasts → Redis cache + evaluate alert thresholds."""
    raise NotImplementedError
