from datetime import date

from fastapi import APIRouter, Body, Depends, Path, Query

from app import db
from app.auth.dependencies import get_user
from app.auth.types import User
from app.config import config
from app.recommendations import services
from app.recommendations.enums import RecommendationPageSortBy, RecommendationStatus
from app.recommendations.models import RejectRecommendationBody
from app.recommendations.responses import (
    RecommendationPage,
    RecommendationPageState,
    RecommendationResponse,
)

router = APIRouter(prefix=config.BASE_API_PATH, tags=["recommendations"])


@router.get(
    path="/list",
    response_model=RecommendationPage,
)
def get_recommendation_page(
    journey_id: int | None = Query(None),
    page_num: int = Query(1, ge=1, alias="page"),
    page_size: int = Query(20, ge=1, le=100),
    status: RecommendationStatus | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    sort_by: RecommendationPageSortBy = Query(RecommendationPageSortBy.status_date),
    user: User = Depends(get_user),
) -> RecommendationPage:
    account_id = user.company_id
    with db.connect():
        page = services.get_recommendation_page(
            account_id=account_id,
            journey_id=journey_id,
            page_num=page_num,
            page_size=page_size,
            status=status,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
        )

    return page


@router.get(
    path="/list/state",
    response_model=RecommendationPageState,
)
def get_recommendation_page_state(
    user: User = Depends(get_user),
    journey_id: int | None = Query(None),
) -> RecommendationPageState:

    account_id = user.company_id
    with db.connect():
        state = services.get_recommendation_page_state(
            account_id=account_id,
            journey_id=journey_id,
        )

    return state


@router.get(
    path="/{id}",
    response_model=RecommendationResponse,
)
def get_recommendation(
    id_: int = Path(..., alias="id"),
    user: User = Depends(get_user),
) -> RecommendationResponse:

    with db.begin():
        recommendation = services.get_user_recommendation(id_=id_, user=user)
        response = services.prepare_recommendation_response(recommendation)

    return response


@router.post(
    path="/{id}/accept",
    response_model=RecommendationResponse,
)
def accept_recommendation(
    id_: int = Path(..., alias="id"),
    user: User = Depends(get_user),
) -> RecommendationResponse:

    with db.begin():
        recommendation = services.accept_recommendation(id_=id_, user=user)
        response = services.prepare_recommendation_response(recommendation)

    return response


@router.post(
    path="/{id}/reject",
    response_model=RecommendationResponse,
)
def reject_recommendation(
    id_: int = Path(..., alias="id"),
    body: RejectRecommendationBody = Body(...),
    user: User = Depends(get_user),
) -> RecommendationResponse:

    with db.begin():
        recommendation = services.reject_recommendation(
            id_=id_,
            user=user,
            reason=body.reason,
        )
        response = services.prepare_recommendation_response(recommendation)

    return response
