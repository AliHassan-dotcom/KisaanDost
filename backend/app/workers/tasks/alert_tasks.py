"""Alert dispatch — FCM push + in-app alert rows (PRD.md F7)."""

from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=2, retry_backoff=True)
def dispatch_alert(self, alert_id: int) -> None:
    """Send push; on FCM 4xx mark token stale — in-app alert row is already written."""
    raise NotImplementedError
