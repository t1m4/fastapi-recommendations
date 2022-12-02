from datetime import datetime

import pytest

from app import db
from app.errors import DoesNotExistsError
from app.recommendations import services
from tests.conftest import MockGoalUpdate


def test_consume_goal_update():
    journey_id = 1
    goal_update = MockGoalUpdate.create(journey_id=journey_id, updated_at=datetime.now())
    assert goal_update.journey_id == journey_id


def test_update_goal_update():
    journey_id = 1
    created_goal = MockGoalUpdate.create(journey_id=journey_id, updated_at=datetime.now())
    with db.begin():
        updated_goal = services.update_goal_update(created_goal.id, journey_id)
        assert updated_goal.journey_id == journey_id  # type: ignore


def test_update_goal_update_with_error():
    journey_id = 1
    created_goal = MockGoalUpdate.create(journey_id=journey_id, updated_at=datetime.now())
    with db.begin(), pytest.raises(DoesNotExistsError):
        services.update_goal_update(created_goal.id + 1, journey_id)


def test_get_goal_update():
    journey_id = 1
    created_goal = MockGoalUpdate.create(journey_id=journey_id, updated_at=datetime.now())
    with db.connect():
        goal = services.get_goal_update(created_goal.id)
        assert goal.journey_id == journey_id  # type: ignore


def test_get_goal_update_with_error():
    with db.begin(), pytest.raises(DoesNotExistsError):
        services.get_goal_update(1)


def test_delete_goal_update():
    journey_id = 1
    created_goal = MockGoalUpdate.create(journey_id=journey_id, updated_at=datetime.now())
    with db.connect():
        goal = services.delete_goal_update(created_goal.id)
        assert goal.journey_id == journey_id  # type: ignore


def test_delete_goal_update_with_error():
    with db.begin(), pytest.raises(DoesNotExistsError):
        services.delete_goal_update(1)
