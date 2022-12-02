import sqlalchemy as sa
from fastapi import APIRouter
from kafka import KafkaAdminClient
from redis.client import Redis

from app import db
from app.config import config
from app.types import StrDict

router = APIRouter(tags=["system"])


@router.get(path="/health/")
def health() -> StrDict:

    # check database
    with db.connect() as conn:
        conn.execute(sa.text("SELECT 1 = 1;"))

    # check redis
    redis = Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_DB,
        socket_timeout=5,
    )
    redis.ping()
    redis.close()

    # check kafka
    consumer = KafkaAdminClient(bootstrap_servers=config.KAFKA_SERVERS_LIST)
    consumer.list_topics()
    consumer.close()

    return {"status": "alive"}
