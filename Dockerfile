FROM python:3.12.1

# System deps:
RUN pip install "poetry==$POETRY_VERSION"

# Copy only requirements to cache them in docker layer
WORKDIR /code
COPY poetry.lock pyproject.toml /code/


# Project initialization:
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi --only main

# Creating folders, and files for a project:
COPY . /code
