import logging
from contextlib import contextmanager, suppress
from typing import Iterator

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse, Response

from app.auth.services import authentication
from app.errors import BaseError
from app.health import handlers as health
from app.producer.services import producer
from app.recommendations import handlers as recommendations


def setup_logging() -> None:
    logging.basicConfig(level=logging.DEBUG)

    kafka = logging.getLogger("kafka")
    kafka.setLevel(logging.WARNING)


def setup_error_handler(app: FastAPI) -> None:
    @app.exception_handler(BaseError)
    # async def exception_handler(_: Request, exc: BaseError) -> Response:
    def exception_handler(_: Request, exc: BaseError) -> Response:
        return JSONResponse(
            status_code=exc.http_status,
            content={"message": exc.message},
        )


def setup_routes(app: FastAPI) -> None:
    app.include_router(health.router)
    app.include_router(recommendations.router)


def setup_openapi(app: FastAPI) -> None:
    # NOTE: Remove for public
    schema = app.openapi()


def start_services() -> None:
    producer.start()
    authentication.start()


def stop_services() -> None:
    with suppress(BaseException):
        producer.stop()

    with suppress(BaseException):
        authentication.stop()


@contextmanager
def with_services() -> Iterator[None]:
    try:
        start_services()
        yield
    finally:
        stop_services()


def setup_events(app: FastAPI) -> None:

    # startup events
    app.add_event_handler("startup", start_services)

    # shutdown events
    app.add_event_handler("shutdown", stop_services)
