from typing import Any

from kafka import KafkaProducer
from kafka.producer.future import FutureRecordMetadata

from app.config import config
from app.producer.exceptions import ProducerNotStarted
from app.producer.models import URLSchema
from app.producer.topics import Topics
from app.utils import to_json


class BaseProducerService:
    """
    Generic implementation of Kafka Producer service, that methods like
    .start or .stop to control lifecycle of the service.
    """

    def __init__(self) -> None:
        self.debug_name = f"recommendation_service-{config.ENVIRONMENT}"
        self._producer: KafkaProducer | None = None

    def start(self) -> None:
        self._producer = KafkaProducer(
            bootstrap_servers=config.KAFKA_SERVERS_LIST,
            client_id=self.debug_name,
        )

    def stop(self) -> None:
        if self._producer is None:
            return
        return self._producer.close()

    @property
    def producer(self) -> KafkaProducer:
        if self._producer is None:
            raise ProducerNotStarted(
                "Kafka producer is not started. " "Use function `producer.start()` to start producer"
            )
        return self._producer

    def send_message(self, topic: Topics, value: Any) -> FutureRecordMetadata:
        metadata = self.producer.send(
            topic=topic.value,
            value=to_json(value).encode(),
            # for easier investigation of author of message
            headers=[
                ("producer", self.debug_name.encode()),
            ],
        )
        return metadata


class Producer(BaseProducerService):
    """Business specific implementation of Kafka producer"""

    def send_url_schema(self, schema: URLSchema):
        metadata = self.send_message(topic=Topics.URL_SCHEMA, value=schema)
        metadata.get()


producer = Producer()
