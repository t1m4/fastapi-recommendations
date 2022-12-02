import logging
from datetime import date, datetime
from typing import DefaultDict

from app.auth.types import User
from app.errors import DoesNotExistsError
from app.recommendations import db
from app.recommendations.enums import RecommendationPageSortBy, RecommendationStatus
from app.recommendations.models import (
    GoalUpdate,
    GoalUpdateInput,
    PlatformStatus,
    PlatformStatusInput,
    Recommendation,
    RecommendationInput,
)
from app.recommendations.responses import (
    RecommendationPage,
    RecommendationPageState,
    RecommendationResponse,
)
from app.utils import count_total_pages, group_by

logger = logging.getLogger(__name__)


def get_recent_platform_status(
    recommendation_id: int,
    platform_name: str,
) -> PlatformStatus | None:
    """Get last status for given platform"""
    statuses = get_platform_statuses(
        recommendation_id=recommendation_id,
        platform_name=platform_name,
    )
    return statuses[0] if statuses else None


def get_platform_statuses(
    recommendation_id: int | None = None,
    recommendations_ids: list[int] | None = None,
    platform_name: str | None = None,
) -> list[PlatformStatus]:
    """
    Get list of platform statuses and then group by recommendation_i and platform
    """
    statuses = db.select_platform_statuses(
        recommendation_id=recommendation_id,
        recommendations_ids=recommendations_ids,
        platform_name=platform_name,
    )

    # sort statuses by id, the newest statuses will be on top of the list
    statuses = sorted(statuses, key=lambda s: s.id, reverse=True)
    return [status for status in statuses if not status.is_empty]


def prepare_recommendations_responses(
    recommendations: list[Recommendation],
) -> list[RecommendationResponse]:
    """Prepare a response to the recommendations by enriching recommendation by platform status"""

    recommendations_ids = [r.id for r in recommendations]

    statuses = get_platform_statuses(recommendations_ids=recommendations_ids)

    statuses_map: DefaultDict[int, list[PlatformStatus]]
    statuses_map = group_by(statuses, lambda s: s.recommendation_id)

    return [
        RecommendationResponse(
            **recommendation.dict(),
            platform_statuses=statuses_map[recommendation.id],
        )
        for recommendation in recommendations
    ]


def prepare_recommendation_response(
    recommendation: Recommendation,
) -> RecommendationResponse:
    responses = prepare_recommendations_responses(recommendations=[recommendation])
    return responses[0]


def get_recommendation_page(
    account_id: int,
    journey_id: int | None,
    page_num: int,
    page_size: int,
    status: RecommendationStatus | None,
    date_from: date | None,
    date_to: date | None,
    sort_by: RecommendationPageSortBy,
) -> RecommendationPage:
    """Get recommendations list with pagination"""
    offset = (page_num - 1) * page_size

    # get list of recommendations
    recommendations = db.select_recommendation_list(
        account_id=account_id,
        journey_id=journey_id,
        date_from=date_from,
        date_to=date_to,
        status=status,
        offset=offset,
        limit=page_size,
        sort_by=sort_by,
    )

    # get total count
    total_count = db.select_recommendation_count(
        account_id=account_id,
        journey_id=journey_id,
        date_from=date_from,
        date_to=date_to,
        status=status,
    )
    pages = count_total_pages(page_size=page_size, total_count=total_count)

    items = prepare_recommendations_responses(recommendations)
    return RecommendationPage(
        page=page_num,
        pages=pages,
        items=items,
    )


def get_recommendation_page_state(
    account_id: int,
    journey_id: int | None,
) -> RecommendationPageState:
    """Get recommendation state for account or journey"""
    active_exists = db.exists_active_recommendations(
        account_id=account_id,
        journey_id=journey_id,
    )
    return RecommendationPageState(active_exists=active_exists)


def get_user_recommendation(id_: int, user: User) -> Recommendation:
    """Get recommendation and check access"""

    recommendation = get_recommendation(id_=id_)

    if recommendation.account_id != user.company_id:
        raise DoesNotExistsError(
            message="Recommendation does not exist",
            extra={
                "recommendation_id": id_,
                "recommendation_account_id": recommendation.account_id,
                "user_company_id": user.company_id,
            },
        )

    return recommendation


def get_recommendation(id_: int) -> Recommendation:
    """Get user recommendation by id"""

    recommendation = db.select_recommendation(id_=id_)

    if recommendation is None:
        raise DoesNotExistsError(
            message="Recommendation does not exist",
            extra={"recommendation_id": id_},
        )

    return recommendation


def accept_recommendation(*, id_: int, user: User) -> Recommendation:

    recommendation = get_user_recommendation(id_=id_, user=user)

    # do nothing if status is already changed
    if recommendation.status not in (
        RecommendationStatus.ERROR,
        RecommendationStatus.ACTIVE,
        RecommendationStatus.EXPIRED,
    ):
        return recommendation

    recommendation = db.update_recommendation_decision(
        recommendation_id=id_,
        status=RecommendationStatus.ACCEPTING,
        user_id=user.id,
        decision_time=datetime.now(),
    )
    return recommendation


def reject_recommendation(
    *,
    id_: int,
    user: User,
    reason: str | None,
) -> Recommendation:

    recommendation = get_user_recommendation(id_=id_, user=user)

    # do nothing if status is already changed
    if recommendation.status not in (
        RecommendationStatus.ERROR,
        RecommendationStatus.ACTIVE,
    ):
        return recommendation

    recommendation = db.update_recommendation_decision(
        recommendation_id=id_,
        status=RecommendationStatus.REJECTED,
        user_id=user.id,
        decision_time=datetime.now(),
        reason=reason,
    )
    return recommendation


def consume_platform_status(status_input: PlatformStatusInput) -> None:
    """
    Save platform status and update recommendation status based
    on platform statuses
    """

    db.insert_platform_status(status_input)


def consume_goal_update(update: GoalUpdateInput) -> GoalUpdate:
    return db.insert_goal_update(update)


def update_goal_update(goal_id: int, journey_id: int) -> GoalUpdate | None:
    goal = db.update_goal_update(goal_id, journey_id)
    if not goal:
        raise DoesNotExistsError(message="Goal doesn't exist")
    return goal


def get_goal_update(goal_update_id: int) -> GoalUpdate | None:
    goal = db.select_goal_update(goal_update_id)
    if not goal:
        raise DoesNotExistsError(message="Goal doesn't exist")
    return goal


def delete_goal_update(goal_update_id: int) -> GoalUpdate:
    goal = db.delete_goal_update(goal_update_id)
    if not goal:
        raise DoesNotExistsError(message="Goal doesn't exist")
    return goal


def consume_recommendation(recommendation: RecommendationInput) -> None:
    """
    Save consumed recommendation into database.
    WARN: this function for kafka consumer only
    """

    # For duplicated item just do nothing
    _recommendation = db.select_recommendation_by_uuid(uuid=recommendation.uuid)
    if _recommendation:
        logger.info(f"Skip duplicated recommendation: {recommendation.uuid}")
        return None

    with db.begin():

        # expire all previous recommendations
        db.expire_recommendations(
            account_id=recommendation.account_id,
            journey_id=recommendation.journey_id,
        )

        # insert new recommendation
        _recommendation = db.insert_recommendation(recommendation=recommendation)
