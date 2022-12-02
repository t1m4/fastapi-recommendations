from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterator, Tuple

from pydantic import BaseModel as _BaseModel
from pydantic import Extra, Field, root_validator, validator

from app.recommendations.enums import (
    PlatformStatusType,
    RecommendationStatus,
    RecommendationType,
)
from app.types import StrDict
from app.utils import to_json

TaxonomyID = int | float | str


class BaseModel(_BaseModel):
    class Config:
        # By default, value is `ignore`, which indicates to ignore extra fields,
        # unknown fields will be discarded. Here I'm setting to `allow` value to
        # preserve new fields, that can be introduced by AIRE at any moment of time.
        # For example, AIRE sent recommendations with new fields, that we do not expect.
        # Instead of discarding that fields, we will save that field not validated to
        # the database, and then we can add validation to that field without losing
        # data.
        extra = Extra.allow
        json_dumps = to_json


class BudgetInfo(BaseModel):
    currency: str


class RecommendationBase(BaseModel):
    """Base class for recommendations"""

    uuid: str
    account_id: int
    type: str
    version: int


class NotificationBase(BaseModel):
    """Validator filtering recommendation from notification kafka messages"""

    type: str

    @property
    def is_recommendation(self) -> bool:
        return self.type in (RecommendationType.budget, RecommendationType.new_platform)


class RecommendationInput(RecommendationBase):
    timestamp: int
    budget_info: BudgetInfo

    @property
    def creation_date(self) -> datetime:
        return datetime.utcfromtimestamp(self.timestamp)


class Recommendation(RecommendationBase):
    """Recommendation that represent object in database with id."""

    id: int
    creation_date: datetime
    enabled: bool
    journey_id: int
    media_plan_id: int | None
    journey_name: str
    user_id: int | None
    currency: str
    status: RecommendationStatus
    decision_time: datetime | None
    reason: str | None

    class Config:
        orm_mode = True


    @property
    def timestamp(self) -> int:
        return int(self.creation_date.timestamp())


class PlatformStatusData(BaseModel):
    object_id: str
    object_type: str
    status: PlatformStatusType
    details: str | None = None

    @property
    def is_error(self) -> bool:
        return self.status == PlatformStatusType.error

    @property
    def is_pending(self) -> bool:
        return self.status == PlatformStatusType.pending

    @property
    def is_success(self) -> bool:
        return self.status == "success"


class PlatformStatusInput(BaseModel):
    id: int | None = Field(None)
    platform: str = Field(...)
    data: list[PlatformStatusData] = Field(...)


class PlatformStatus(BaseModel):
    """Platform status that represent object in database with id."""

    id: int
    recommendation_id: int
    platform: str
    data: list[PlatformStatusData] = Field(default_factory=list)

    class Config:
        orm_mode = True

    @property
    def is_empty(self) -> bool:
        return len(self.data) == 0

    @property
    def is_pending(self) -> bool:
        """
        Whole platform status is in pending state when all items have
        pending status
        """
        return all(item.is_pending for item in self.data)

    @property
    def has_error(self) -> bool:
        return any(item.is_error for item in self.data)

    @property
    def has_success(self) -> bool:
        return any(item.is_success for item in self.data)


class GoalUpdateInput(BaseModel):
    journey_id: int = Field(..., alias="campaign_collection_id")
    updated_at: datetime = Field(...)


class GoalUpdate(BaseModel):
    id: int
    journey_id: int
    updated_at: datetime

    class Config:
        orm_mode = True


class RejectRecommendationBody(BaseModel):
    reason: str | None

    @validator("reason", pre=True)
    def reason_to_none(cls, reason: str | None) -> str | None:
        return None if reason == "" else reason
