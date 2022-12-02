#!/bin/bash

if [[ $ENVIRONMENT == "local" ]]; then

    # wait for Kafka
    SERVICE_NAME=Kafka SERVICE_HOST=${KAFKA_HOST} SERVICE_PORT=${KAFKA_PORT} ./docker/wait_for_service.sh

    # wait for database migration
    bash docker/init.sh

    # start consumer with auto-reloading
    watchfiles app.consumer.__main__.main
else
    python -m app.consumer
fi
