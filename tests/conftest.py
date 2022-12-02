from collections import defaultdict
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path
from typing import Any, List
from unittest import mock
from unittest.mock import Mock
from uuid import uuid4

import celery
import pytest
import sqlalchemy as sa
from fastapi import FastAPI
from kafka.consumer.fetcher import ConsumerRecord
from starlette.testclient import TestClient

from app import db
from app.auth import services as auth
from app.main import create_app
from app.producer.services import producer
from app.recommendations import models, tables
from app.recommendations.enums import RecommendationStatus
from app.topics import Topics
from app.utils import from_json, to_json


@pytest.fixture(scope="session", autouse=True)
def app():
    with ExitStack() as stack:

        # do not start producer on start
        stack.enter_context(mock.patch.object(producer, "start", Mock()))
        stack.enter_context(mock.patch.object(producer, "stop", Mock()))
        yield create_app()


@pytest.fixture(scope="session")
def client(app: FastAPI):
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session", autouse=True)
def auth_service_start():
    try:
        auth.authentication.start()
        yield
    finally:
        auth.authentication.stop()


@pytest.fixture(autouse=True)
def db_cleanup():
    """Automatically cleanup database after every tests"""
    try:
        yield
    finally:
        with db.begin() as connection:
            tables = ", ".join(db.Base.metadata.tables)
            connection.execute(sa.text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE;"))


def _reset_table_sequence(table: str, column: str) -> None:
    with db.begin():
        query = sa.text(
            f"""
            SELECT setval(
                pg_get_serial_sequence('{table}', '{column}'),
                coalesce(MAX({column}), 10)
            )
            FROM {table};
            """
        )
        db.execute(query)


class MockConsumerRecord(ConsumerRecord):
    @classmethod
    def from_path(cls, path: Path) -> "MockConsumerRecord":
        value = path.read_bytes()
        return cls.build(value=value)

    @classmethod
    def from_dict(cls, value: dict) -> "MockConsumerRecord":
        return cls.build(value=to_json(value).encode())

    @classmethod
    def build(
        cls,
        topic="test_topic",
        partition: int = 1,
        offset: int = 4065,
        timestamp: int = 1646841794656,
        timestamp_type: int = 0,
        key: int | None = None,
        value: bytes = b"",
        headers: list[Any] | None = None,
        checksum: str | None = None,
        serialized_key_size: int = -1,
        serialized_value_size: int = 3136,
        serialized_header_size: int = -1,
    ) -> "MockConsumerRecord":
        return MockConsumerRecord(
            topic=topic,
            checksum=checksum,
            value=value,
            key=key,
            headers=headers or [],
            offset=offset,
            partition=partition,
            serialized_key_size=serialized_key_size,
            serialized_value_size=serialized_value_size,
            serialized_header_size=serialized_header_size,
            timestamp=timestamp,
            timestamp_type=timestamp_type,
        )


class MockRecommendation(models.Recommendation):
    @classmethod
    def get(cls, id_: int):
        with db.connect():
            query = sa.select(tables.Recommendation).where(tables.Recommendation.id == id_)
            row = db.select_one(query)
            return MockRecommendation.from_orm(row) if row else None

    @classmethod
    def get_by_uuid(cls, uuid: str):
        with db.connect():
            query = sa.select(tables.Recommendation).where(tables.Recommendation.uuid == uuid)
            row = db.select_one(query)
            return MockRecommendation.from_orm(row) if row else None

    @classmethod
    def get_all(cls):
        with db.connect():
            rows = db.select_all(sa.select(tables.Recommendation))
            return (MockRecommendation.from_orm(row) for row in rows)

    @classmethod
    def create(
        cls,
        id: int = 1,
        status: RecommendationStatus = RecommendationStatus.ACTIVE,
        account_id: int = 261,
        creation_date: datetime = datetime(2022, 3, 1, 16, 34, 26),
        journey_id: int = 8110,
        uuid: str | None = None,
        **kwargs,
    ) -> "MockRecommendation":
        with db.begin():
            data = {
                **kwargs,
                "id": id,
                "status": status.value,
                "account_id": account_id,
                "creation_date": creation_date,
                "journey_id": journey_id,
                "uuid": uuid or str(uuid4()),
            }

            row = db.select_one(sa.insert(tables.Recommendation).values(data).returning(tables.Recommendation))

        return MockRecommendation.from_orm(row)

    @staticmethod
    def reset_id() -> None:
        _reset_table_sequence(table="recommendations", column="id")


class MockPlatformStatus(models.PlatformStatus):
    @classmethod
    def create(
        cls,
        recommendation_id: int,
        id: int | None = None,
        platform: str = "facebook",
        platform_data: list[models.PlatformStatusData] | None = None,
    ):
        with db.begin():
            data = dict(
                recommendation_id=recommendation_id,
                platform=platform,
                data=platform_data or [],
            )
            if id is not None:
                data["id"] = id

            status = db.select_one(
                sa.insert(tables.PlatformStatus).values(**platform_data).returning(tables.PlatformStatus)
            )

            return MockPlatformStatus.from_orm(status)

    @classmethod
    def get_all(cls):
        with db.connect():
            rows = db.select_all(sa.select(tables.PlatformStatus))
            return (MockPlatformStatus.from_orm(row) for row in rows)


class MockGoalUpdate(models.GoalUpdate):
    @classmethod
    def create(cls, *, id_: int | None = None, journey_id: int, updated_at: datetime):
        with db.begin():
            data = {"journey_id": journey_id, "updated_at": updated_at}
            if id_:
                data["id"] = id_
            row = db.select_one(sa.insert(tables.GoalUpdate).values(data).returning(tables.GoalUpdate))
            return MockGoalUpdate.from_orm(row)

    @classmethod
    def get_updates(cls, journey_id: int):
        with db.connect():
            query = sa.select(tables.GoalUpdate).where(tables.GoalUpdate.journey_id == journey_id)
            rows = db.select_all(query)
            return (MockGoalUpdate.from_orm(row) for row in rows)


class MockedMessageBox:
    def __init__(self):
        self.messages = []

    @property
    def messages_count(self):
        return len(self.messages)

    @property
    def last_message(self):
        return self.messages[-1]


class ProducerMessageBox(MockedMessageBox):
    def add_message(self, topic: Topics, value: Any) -> None:
        _value = from_json(to_json(value))
        self.messages.append({"topic": topic, "value": _value})

    def get_by_topic(self, topic: Topics) -> List[Any]:
        messages = []
        for message in self.messages:
            if message["topic"] == topic:
                messages.append(message)
        return messages

    @property
    def messages_map(self) -> dict[str, list[dict[str, Any]]]:
        mapping = defaultdict(list)
        for message in self.messages:
            mapping[message["topic"]].append(message["value"])
        return mapping


@pytest.fixture(autouse=True)
def producer_mock(monkeypatch):

    _box = ProducerMessageBox()

    def send_message(topic, value):
        _box.add_message(topic=topic, value=value)
        return Mock()

    monkeypatch.setattr(producer, "send_message", send_message)

    yield _box


class CeleryMessageBox(MockedMessageBox):
    def add_message(self, name: str, args: Any, **kwargs: Any) -> None:
        message = {"name": name, "args": args, "kwargs": kwargs}
        self.messages.append(message)


@pytest.fixture(autouse=True)
def celery_mock(monkeypatch):
    box = CeleryMessageBox()

    def delay(self, *args, **kwargs):
        box.add_message(
            name=self.name,
            args=args,
            kwargs=kwargs,
        )

    monkeypatch.setattr(celery.Task, "delay", delay)

    yield box


@pytest.fixture(autouse=True)
def auth_get_company():
    yield
    # To have independent tests, clear cache of function `get_company` after every test
    auth.get_company.cache_clear()
