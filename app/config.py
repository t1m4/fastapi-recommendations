from pydantic import BaseSettings, Field


class Config(BaseSettings):
    # NOTE: Remove for public
    ENVIRONMENT: str = Field(...)
    SENTRY_DSN: str | None = Field(None)
    APP_TITLE: str = Field("recommendation_service")
    POSTGRES_HOST: str = Field(...)
    POSTGRES_PORT: str = Field(...)
    POSTGRES_USER: str = Field(...)
    POSTGRES_PASSWORD: str = Field(...)
    POSTGRES_DB: str = Field(...)
    KAFKA_SERVERS: str = Field(...)
    KAFKA_CONSUMER_GROUP_ID: str = Field("recommendations_consumer")
    BASE_API_PATH: str = "/api/recommendations"
    REDIS_HOST: str = Field(...)
    REDIS_PORT: int = Field(...)
    REDIS_DB: int = Field(13)
    JWT_SECRET_KEY: str = Field(...)

    # Kafka topics
    # Please, use `KAFKA_{}_TOPIC` format for consistency
    KAFKA_URL_SCHEMA_TOPIC: str = Field(
        default="url-schema",
        env="KAFKA_TOPIC_URL_SCHEMA",
    )
    
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def KAFKA_SERVERS_LIST(self) -> list[str]:
        return [item.strip() for item in self.KAFKA_SERVERS.split(",")]

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}"
            f"/{self.POSTGRES_DB}"
        )


config = Config(_env_file=".env", _env_file_encoding="utf-8")  # type: ignore
