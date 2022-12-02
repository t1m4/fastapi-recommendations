from typing import Callable

from kafka.consumer.fetcher import ConsumerRecord

TaskHandler = Callable[[ConsumerRecord], None]
