from enum import Enum

from app.config import config


class Topics(str, Enum):
    # NOTE: Remove for public
    # Schema for publishing URL schema changes
    URL_SCHEMA = config.KAFKA_URL_SCHEMA_TOPIC
