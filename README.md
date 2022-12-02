# Recommendation service

## Run project

There are two ways to run service using docker-compose (recommended):

```shell
docker-compose up app
```

or running using poetry:

1.  Update poetry to 1.2.0 version (once)

```shell
poetry self update --preview
```

2.  Create file with env variables (once):

```shell
cp .env.example .env
```

3.  Run docker related services:

```shell
docker-compose up db kafka
```

4.  Run service:

```shell
poetry run docker/start.sh
```

## Prepare database

To have some test data on the developer environment,
you can recreate the database from backups of the database on staging.

1.  Login to aws:

```shell
aws sso login --profile profile_name
```

2.  Download backups

```shell
./docker/dumps-download.sh
```

3.  Remove database volumes

```shell
docker-compose down --volumes
```


### Run tests

```shell
docker-compose run --rm test
```


### Database migration

*   autogenerate migration

```shell
docker-compose run --rm alembic-autogenerate "Migration message"
```

*   upgrade to latest version

```shell
docker-compose run --rm alembic upgrade heads
```

*   upgrade to previous version

```shell
docker-compose run --rm alembic downgrade -1
```
