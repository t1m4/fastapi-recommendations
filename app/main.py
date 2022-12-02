from fastapi import FastAPI

from app import setup
from app.config import config


def create_app() -> FastAPI:
    app = FastAPI(
        title=config.APP_TITLE,
        openapi_url=f"{config.BASE_API_PATH}/docs/openapi.json",
        docs_url=f"{config.BASE_API_PATH}/docs/ui",
    )

    setup.setup_logging()
    setup.setup_error_handler(app)
    setup.setup_routes(app)
    setup.setup_openapi(app)
    setup.setup_events(app)
    return app
