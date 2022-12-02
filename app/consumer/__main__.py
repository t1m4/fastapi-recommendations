import logging

from kafka import KafkaConsumer
from kafka.consumer.fetcher import ConsumerRecord

from app import setup
from app.config import config
from app.consumer.setup import TASKS, TASKS_TOPICS
from app.consumer.types import TaskHandler
from app.errors import BaseError

setup.setup_logging()

logger = logging.getLogger(__name__)

consumer = KafkaConsumer(
    bootstrap_servers=config.KAFKA_SERVERS_LIST,
    group_id=config.KAFKA_CONSUMER_GROUP_ID,
    # autocommit is disabled for preventing data loss, every job have to handle duplicated message
    enable_auto_commit=False,
    max_poll_records=1,
)


def get_topic_handler(record: ConsumerRecord) -> TaskHandler:
    """Get handler for processing consumer record"""

    handler: TaskHandler | None = TASKS.get(record.topic)

    # Unexpected situation
    if handler is None:
        extra = {
            "record_topic": record.topic,
            "record_value": record.value,
        }
        raise BaseError("No task handler for topic", extra=extra)

    return handler


def start_consuming() -> None:

    consumer.subscribe(TASKS_TOPICS)

    logger.info(
        msg="Started consuming Kafka topics",
        extra={"kafka_servers": config.KAFKA_SERVERS_LIST},
    )

    record: ConsumerRecord
    for record in consumer:
        logger.error(record)

        handler = get_topic_handler(record=record)

        debug_context = {
            "topic": record.topic,
            "offset": record.offset,
            "partition": record.partition,
            "handler": handler.__name__,
            "timestamp": record.timestamp,
        }
        logging.info(
            msg=f"Handling consumer message: {record.topic}",
            extra={"record": debug_context},
        )

        try:
            handler(record)
        except BaseException:
            continue  # do not commit in case of error

        # manually commit consumer offset, because autocommit is disabled
        consumer.commit()


def main() -> None:
    try:
        with setup.with_services():
            start_consuming()
    # watchfiles raises `KeyboardInterrupt` on file changes
    except KeyboardInterrupt:
        exit(1)


if __name__ == "__main__":
    main()
