FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY uv.lock .
RUN pip install --no-cache-dir uv && \
    uv sync --no-dev --no-cache

COPY app.py .

EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--browser.gatherUsageStats=false"]