FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for psycopg/pgvector
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY uv.lock .
RUN pip install --no-cache-dir uv && \
    uv sync --no-dev --no-cache

# Copy the entire backend source code
COPY ./app ./backend/app

# Ensure Python can find the 'backend' module
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]