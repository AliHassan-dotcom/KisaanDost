"""Celery application — all external I/O lives in workers, never in the request path.

Schedules follow docs/architecture/02-data-flow-gee.md (cache & refresh strategy).
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "kisaan_dost",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.tasks.gee_tasks",
        "app.workers.tasks.weather_tasks",
        "app.workers.tasks.price_tasks",
        "app.workers.tasks.alert_tasks",
    ],
)

celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_soft_time_limit=300,
    broker_connection_retry_on_startup=True,
    timezone="Asia/Karachi",
    beat_schedule={
        "sync-weather": {
            "task": "app.workers.tasks.weather_tasks.sync_weather",
            "schedule": crontab(minute=0),  # hourly
        },
        "sync-prices": {
            "task": "app.workers.tasks.price_tasks.sync_prices",
            "schedule": crontab(minute=0, hour="6,12,18"),  # 3× daily
        },
        "refresh-satellite": {
            "task": "app.workers.tasks.gee_tasks.refresh_due_farms",
            "schedule": crontab(minute=0, hour=3),  # nightly batch
        },
    },
)
