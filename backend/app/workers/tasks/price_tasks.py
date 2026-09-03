"""Mandi price ingestion — every row keeps its source as-of timestamp (PRD.md F6)."""

from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=2, retry_backoff=True)
def sync_prices(self) -> None:
    """3× daily: pull all active price sources, upsert rows with as_of timestamps."""
    raise NotImplementedError
