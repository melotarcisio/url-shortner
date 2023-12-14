FROM python:3.10

WORKDIR /app/

# Install ffmpeg and flac
RUN apt-get update && \
    apt-get install -y ffmpeg flac



# Install Poetry
RUN curl -sSL https://install.python-poetry.org | \
    POETRY_HOME=/opt/poetry python3 && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Install dependencies
COPY ./pyproject.toml ./poetry.lock /app/
RUN poetry install --no-root