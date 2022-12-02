from app.commands.__main__ import update_url_schema
from app.producer.models import URLSchema, URLSchemaEndpoint
from app.topics import Topics


def test_update_url_schema_command(producer_mock):
    update_url_schema()
    assert producer_mock.messages_count == 1
    message = producer_mock.last_message
    assert message["topic"] == Topics.URL_SCHEMA
    assert message["value"] == URLSchema(
        service="recommendation_service",
        endpoints=[
            URLSchemaEndpoint(
                path="^/api/recommendations/",
                features=["notifications_feature"],
                is_regex=True,
                post_for_read=False,
            )
        ],
    )
