FROM python:3.11-slim

WORKDIR /app

ENV HF_HOME="/app/.cache/huggingface"

COPY pyproject.toml .
COPY uv.lock .

RUN pip install --no-cache-dir uv && \
    uv sync --no-dev --no-cache --no-install-package opencv-python

ENV PATH="/app/.venv/bin:$PATH"



COPY app/ .

CMD ["python", "processor.py"]