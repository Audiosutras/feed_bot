FROM python:3.12-alpine

ARG POETRY_VERSION=1.7.1

ENV PYTHONFAULTHANDLER=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_DEFAULT_TIMEOUT=100

# System deps:
RUN apk add gcc musl-dev && \
pip install "poetry==$POETRY_VERSION"

# Copy only requirements to cache them in docker layer
WORKDIR /code
COPY poetry.lock pyproject.toml /code/


# No need to create a virtualenv for this isolated environment:
RUN poetry config virtualenvs.create false && \
poetry install --no-interaction --only=main

# Creating folders, and files for a project:
COPY . /code
