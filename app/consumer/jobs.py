from __future__ import annotations

import logging

from kafka.consumer.fetcher import ConsumerRecord

from app import db
from app.recommendations import services as recommendations
from app.recommendations.models import (
    GoalUpdateInput,
    NotificationBase,
    PlatformStatusInput,
    RecommendationInput,
)

logger = logging.getLogger(__name__)


def consume_recommendation(record: ConsumerRecord) -> None:

    # Skip messages that are not recommendations (we are reading from
    # topic with different types of notifications)
    base = NotificationBase.parse_raw(record.value)
    if not base.is_recommendation:
        logger.info(f"Skip non-recommendation message: {base.type}")
        return

    recommendation = RecommendationInput.parse_raw(record.value)

    with db.connect():
        recommendations.consume_recommendation(recommendation)


def consume_platform_status(record: ConsumerRecord) -> None:
    status = PlatformStatusInput.parse_raw(record.value)
    if not status.id:
        logging.warning(
            msg="Ignore platform status - id is missing",
            extra={"status": status.dict()},
        )
        return

    with db.begin():
        recommendations.consume_platform_status(status)


def consume_goal_update(record: ConsumerRecord) -> None:
    update = GoalUpdateInput.parse_raw(record.value)

    with db.begin():
        recommendations.consume_goal_update(update)
