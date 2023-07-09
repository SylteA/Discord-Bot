FROM python:3.10-slim

STOPSIGNAL SIGQUIT

ENV POETRY_VIRTUALENVS_CREATE=false \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1

WORKDIR /app

# Install dependencies
RUN pip install -U poetry

COPY pyproject.toml poetry.lock /app/
RUN poetry install --only main

ADD . /app

CMD python3 cli.py
