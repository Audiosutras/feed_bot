FROM python:3.12-slim

WORKDIR /code

RUN python3 -m pip install pipx && pipx ensurepath

RUN python3 -m pipx install poetry && python3 -m pipx upgrade poetry

COPY . /code

RUN poetry install
