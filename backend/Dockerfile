FROM python:3.14-slim

WORKDIR /app

# system deps for psycopg2 build; optional if using psycopg2-binary
RUN apt-get update && apt-get install -y build-essential gcc libpq-dev --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# copy pyproject first to leverage layer caching
COPY pyproject.toml .
# If you have a lock (poetry/pip-tools) copy it too. If not, pip will build wheels.
RUN pip install --no-cache-dir pip --upgrade \
    && pip install --no-cache-dir .

# copy rest of the backend code
COPY . .

# uvicorn: use app.main:app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]