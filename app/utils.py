import decimal
import json
import uuid
from collections import defaultdict
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import date, datetime
from enum import Enum
from typing import Any, Callable, DefaultDict, Iterator

from pydantic import BaseModel

AnyCallable = Callable[..., Any]


def json_serializer(obj: Any) -> Any:
    """JSON serializer for objects not serializable by standard library."""
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, (decimal.Decimal, uuid.UUID)):
        return str(obj)
    if isinstance(obj, set):
        return list(obj)
    if isinstance(obj, BaseModel):
        return obj.dict()
    raise TypeError(f"Object of type {obj} is not serializable")


def to_json(data: Any) -> str:
    return json.dumps(data, default=json_serializer)


def from_json(raw: str) -> Any:
    return json.loads(raw)


@contextmanager
def set_context_var(var: ContextVar, value) -> Iterator[None]:
    token = var.set(value)
    try:
        yield
    finally:
        var.reset(token)


def count_total_pages(*, page_size: int, total_count: int) -> int:
    return ((total_count - 1) // page_size) + 1 or 1


def group_by(items: list, key: Callable) -> DefaultDict:
    """Group item by key func"""

    mapping: DefaultDict
    mapping = defaultdict(list)
    for item in items:
        mapping[key(item)].append(item)
    return mapping


def generate_uuid() -> str:
    return str(uuid.uuid4())
