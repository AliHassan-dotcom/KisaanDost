"""GEE analysis tasks — earthengine-api is blocking, so it stays in workers only (RULES.md §3.3).

Pipeline: docs/architecture/02-data-flow-gee.md
"""

from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3, retry_backoff=True)
def analyze_farm(self, farm_id: int) -> None:
    """On-demand: NDVI/NDWI/anomaly for one farm via reduceRegion(). Idempotent on (farm_id, scene_date)."""
    raise NotImplementedError


@celery_app.task(bind=True, max_retries=3, retry_backoff=True)
def refresh_due_farms(self) -> None:
    """Nightly batch: FeatureCollection of due AOIs → reduceRegions() in one GEE call."""
    raise NotImplementedError
