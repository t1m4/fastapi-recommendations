#!/bin/bash

bash docker/upgrade_db.sh

SERVICE_NAME=Kafka SERVICE_HOST=${KAFKA_HOST} SERVICE_PORT=${KAFKA_PORT} ./docker/wait_for_service.sh
python -m app.commands update-url-schema
