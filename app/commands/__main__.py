import typer

from app import setup
from app.config import config
from app.producer.models import URLSchema, URLSchemaEndpoint
from app.producer.services import producer

typer_app = typer.Typer()


@typer_app.command(name="update-url-schema")
def update_url_schema() -> None:

    schema = URLSchema(
        service="recommendation_service",
        endpoints=[
            URLSchemaEndpoint(
                # one rule for all requests
                path=f"^{config.BASE_API_PATH}/",
                features=["notifications_feature"],
            ),
        ],
    )

    try:
        producer.start()
        producer.send_url_schema(schema=schema)
    finally:
        producer.stop()

    typer.echo("URL scheme was published")


@typer_app.command(name="hello")
def hello(name: str) -> None:
    typer.echo(f"Hello world {name}")


if __name__ == "__main__":
    setup.setup_logging()
    typer_app()
