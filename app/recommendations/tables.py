from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Identity,
    Index,
    Integer,
    Text,
    desc,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db import Base
from app.recommendations.enums import RecommendationStatus


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(BigInteger, Identity(), primary_key=True)
    uuid = Column(UUID, nullable=False, unique=True)
    creation_date = Column(DateTime, nullable=False)
    type = Column(Text, nullable=False)
    enabled = Column(Boolean, nullable=False)
    account_id = Column(BigInteger, nullable=False)
    status = Column(Text, nullable=False)

    __table_args__ = (
        # index primary for pagination
        Index(
            "ix_recommendations_account_id_order",
            account_id,
            desc(status == RecommendationStatus.ACTIVE.value),
            desc(creation_date),
            desc(id),
        ),
        # index primary for pagination
        Index(
            "ix_recommendations_account_id_date_order",
            account_id,
            desc(creation_date),
            desc(id),
        ),
        # index to expire previous active recommendations
        Index("ix_recommendations_account_id_status", account_id, status),
    )


class PlatformStatus(Base):
    """Table in which we store platform status"""

    __tablename__ = "platform_statuses"

    id = Column(BigInteger, Identity(), primary_key=True)
    recommendation_id = Column(BigInteger, nullable=False, index=True)
    platform = Column(Text, nullable=False)
    data = Column(JSONB, nullable=False)


class GoalUpdate(Base):
    """Table in which we store time when goals was updated"""

    __tablename__ = "goal_updates"

    id = Column(BigInteger, Identity(), primary_key=True)
    journey_id = Column(BigInteger, nullable=False)
    updated_at = Column(DateTime, nullable=False)
