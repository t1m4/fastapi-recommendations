from __future__ import annotations

import copy
from decimal import Decimal

from pydantic import BaseModel, Field, root_validator, validators

from app.recommendations import models
from app.types import StrDict


class RecommendationResponse(models.Recommendation):
    platform_statuses: list[models.PlatformStatus]

    class Config:
        title = "Recommendation"


class RecommendationPage(BaseModel):
    page: int
    pages: int
    items: list[RecommendationResponse]


class RecommendationPageState(BaseModel):
    active_exists: bool
