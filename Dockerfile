FROM python:3.10-slim-bullseye as base

ENV PYTHONUNBUFFERED 1

RUN apt-get update  \
    && apt-get install --no-install-recommends -y git=1:2.30.2-1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry==1.1.13

WORKDIR /code

COPY pyproject.toml poetry.lock /code/

# Such as we don't need virtual environment in docker
# we can install requirements directly by pip
RUN poetry export --without-hashes --dev --output=requirements.txt
RUN pip install -r requirements.txt

COPY . /code

ENTRYPOINT ["docker/start.sh"]
