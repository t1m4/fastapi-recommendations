from contextlib import contextmanager
from datetime import date, datetime, timedelta
from typing import Any, Iterator

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from app import db
from app.recommendations import models as models
from app.recommendations.enums import RecommendationPageSortBy, RecommendationStatus
from app.recommendations.tables import GoalUpdate, PlatformStatus, Recommendation
from app.types import StrDict


@contextmanager
def begin() -> Iterator[Connection]:
    with db.begin() as connection:
        yield connection


def select_recommendation(id_: int) -> models.Recommendation | None:
    query = sa.select(Recommendation).where(Recommendation.id == id_)
    row = db.select_one(query)
    return models.Recommendation.from_orm(row) if row else None


def select_last_recommendation_id(journey_id: int) -> int | None:
    row = db.select_one(
        sa.select(Recommendation.id).where(Recommendation.journey_id == journey_id).order_by(Recommendation.id.desc())
    )
    return row["id"] if row else None


def select_recommendation_by_uuid(uuid: str) -> models.Recommendation | None:
    query = sa.select(Recommendation).where(Recommendation.uuid == uuid)
    row = db.select_one(query)
    return models.Recommendation.from_orm(row) if row else None


def select_platform_statuses(
    recommendation_id: int | None = None,
    recommendations_ids: list[int] | None = None,
    platform_name: str | None = None,
) -> list[models.PlatformStatus]:
    filters = []
    if recommendation_id is not None:
        filters.append(PlatformStatus.recommendation_id == recommendation_id)
    if recommendations_ids is not None:
        filters.append(PlatformStatus.recommendation_id.in_(recommendations_ids))
    if platform_name is not None:
        filters.append(PlatformStatus.platform == platform_name)
    if not filters:
        raise ValueError("Provide at least one filter")

    rows = db.select_all(sa.select(PlatformStatus).select_from(PlatformStatus).where(*filters))
    return [models.PlatformStatus.from_orm(row) for row in rows]


def _get_recommendation_list_query(
    account_id: int,
    journey_id: int | None,
    date_from: date | None,
    date_to: date | None,
    status: RecommendationStatus | None,
) -> Any:
    filters = [Recommendation.account_id == account_id]
    if date_from is not None:
        filters.append(Recommendation.creation_date >= date_from)
    if date_to is not None:
        filters.append(Recommendation.creation_date < date_to + timedelta(days=1))
    if status is not None:
        filters.append(Recommendation.status == status)
    if journey_id is not None:
        filters.append(Recommendation.journey_id == journey_id)

    query = sa.select(Recommendation).where(sa.and_(*filters))
    return query


def _get_recommendation_list_order_by(sort_by: RecommendationPageSortBy) -> list[Any]:
    """Get list of column for ordering recommendation list page"""

    if sort_by == RecommendationPageSortBy.status_date:
        return [
            # recommendation with status active will be on top
            sa.desc(Recommendation.status == RecommendationStatus.ACTIVE),
            sa.desc(Recommendation.creation_date),
            sa.desc(Recommendation.id),
        ]

    elif sort_by == RecommendationPageSortBy.date:
        return [
            sa.desc(Recommendation.creation_date),
            sa.desc(Recommendation.id),
        ]

    else:
        return []


def select_recommendation_list(
    account_id: int,
    journey_id: int | None,
    date_from: date | None,
    date_to: date | None,
    status: RecommendationStatus | None,
    limit: int,
    offset: int,
    sort_by: RecommendationPageSortBy,
) -> list[models.Recommendation]:
    query = _get_recommendation_list_query(
        account_id=account_id,
        journey_id=journey_id,
        date_from=date_from,
        date_to=date_to,
        status=status,
    )

    order_by = _get_recommendation_list_order_by(sort_by)
    query = query.limit(limit).offset(offset).order_by(*order_by)
    rows = db.select_all(query)
    return [models.Recommendation.from_orm(row) for row in rows]


def exists_active_recommendations(account_id: int, journey_id: int | None) -> bool:
    """Check if active recommendations exists in database"""
    filters = [Recommendation.account_id == account_id, Recommendation.status == RecommendationStatus.ACTIVE]
    if journey_id is not None:
        filters.append(Recommendation.journey_id == journey_id)

    query = sa.select(sa.exists().where(*filters))
    return db.select_scalar(query)


def select_recommendation_count(
    account_id: int,
    journey_id: int | None,
    date_from: date | None,
    date_to: date | None,
    status: RecommendationStatus | None,
) -> int:
    query = _get_recommendation_list_query(
        account_id=account_id,
        journey_id=journey_id,
        date_from=date_from,
        date_to=date_to,
        status=status,
    )
    count_query = query.with_only_columns(sa.func.count(Recommendation.id))
    return db.select_scalar(count_query)


def insert_recommendation(
    recommendation: models.RecommendationInput,
) -> models.Recommendation:
    row = db.select_one(
        sa.insert(Recommendation)
        .values(
            uuid=recommendation.uuid,
            creation_date=recommendation.creation_date,
            type=recommendation.type,
            enabled=True,
            account_id=recommendation.account_id,
            journey_id=recommendation.journey_id,
            media_plan_id=recommendation.media_plan_id,
            journey_name=recommendation.journey_name,
            version=recommendation.version,
            taxonomy=recommendation.taxonomy.dict(),
            user_id=None,
            currency=recommendation.budget_info.currency,
            status=RecommendationStatus.ACTIVE.value,
            decision_time=None,
            reason=None,
        )
        .returning(Recommendation)
    )
    return models.Recommendation.from_orm(row)


def insert_platform_status(status: models.PlatformStatusInput) -> models.PlatformStatus:
    row = db.select_one(
        sa.insert(PlatformStatus)
        .values(
            recommendation_id=status.id,
            platform=status.platform,
            data=status.data,
        )
        .returning(PlatformStatus)
    )
    return models.PlatformStatus.from_orm(row)


def insert_goal_update(update: models.GoalUpdateInput) -> models.GoalUpdate:
    row = db.select_one(
        sa.insert(GoalUpdate)
        .values(
            updated_at=update.updated_at,
            journey_id=update.journey_id,
        )
        .returning(GoalUpdate)
    )
    return models.GoalUpdate.from_orm(row)


def select_goal_update(id_: int) -> models.GoalUpdate | None:
    query = sa.select(GoalUpdate).where(GoalUpdate.id == id_)
    row = db.select_one(query)
    return models.GoalUpdate.from_orm(row) if row else None


def update_goal_update(goal_id: int, journey_id: int) -> models.GoalUpdate | None:
    row = db.select_one(
        sa.update(GoalUpdate).values(journey_id=journey_id).where(GoalUpdate.id == goal_id).returning(GoalUpdate)
    )
    return models.GoalUpdate.from_orm(row) if row else None


def delete_goal_update(goal_id: int):
    row = db.select_one(sa.delete(GoalUpdate).where(GoalUpdate.id == goal_id).returning(GoalUpdate))
    return models.GoalUpdate.from_orm(row) if row else None


def update_recommendation(recommendation_id: int, data: StrDict) -> models.Recommendation:
    row = db.select_one(
        sa.update(Recommendation).values(data).where(Recommendation.id == recommendation_id).returning(Recommendation)
    )
    return models.Recommendation.from_orm(row)


def update_recommendation_decision(
    recommendation_id: int,
    user_id: int,
    decision_time: datetime,
    status: RecommendationStatus,
    reason: str | None = None,
) -> models.Recommendation:

    update = {
        "status": status.value,
        "user_id": user_id,
        "decision_time": decision_time,
    }
    if reason:
        update["reason"] = reason

    return update_recommendation(recommendation_id=recommendation_id, data=update)


def update_recommendation_status(
    recommendation_id: int,
    status: RecommendationStatus,
) -> models.Recommendation:

    update = {"status": status.value}
    return update_recommendation(recommendation_id=recommendation_id, data=update)


def expire_recommendations(account_id: int, journey_id: int) -> None:
    db.execute(
        sa.update(Recommendation)
        .values(status=RecommendationStatus.EXPIRED)
        .where(
            Recommendation.account_id == account_id,
            Recommendation.journey_id == journey_id,
            Recommendation.status.in_([RecommendationStatus.ACTIVE, RecommendationStatus.ACCEPTING]),
        )
    )
