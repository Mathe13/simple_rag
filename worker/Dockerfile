FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir uv && \
    uv sync --no-dev --no-cache

COPY ingest.py .

ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "ingest.py"]
