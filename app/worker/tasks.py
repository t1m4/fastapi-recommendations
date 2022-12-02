import logging

from app.auth.clients import HTTPError
from app.worker.worker import celery_app as app

logger = logging.getLogger(__name__)


@app.task(autoretry_for=(HTTPError,), retry_kwargs={"max_retries": 5})
def test_task(recommendation_id: int) -> None:
    logger.info(f"Send recommendation {recommendation_id}")
