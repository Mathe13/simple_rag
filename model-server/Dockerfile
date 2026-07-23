FROM python:3.11-slim

WORKDIR /app

# Install build dependencies for llama-cpp-python and sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    g++ \
    git \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*


COPY pyproject.toml .
COPY uv.lock .
RUN pip install --no-cache-dir uv && \
    uv sync --no-dev --no-cache

COPY main.py .

ENV PATH="/app/.venv/bin:$PATH"


RUN uv run python -c "import torch; print(torch.__version__)"

# Download models before starting so they are cached in the image
RUN uv run hf download bartowski/Llama-3.2-1B-Instruct-GGUF Llama-3.2-1B-Instruct-Q4_K_M.gguf --local-dir /models/llama
RUN uv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5', trust_remote_code=True)"

RUN uv run python - <<'PY' 
import torch 
print("Torch:", torch.__version__) 

from sentence_transformers import SentenceTransformer 
print("SentenceTransformers imported") 

SentenceTransformer(
    "BAAI/bge-small-en-v1.5",
    trust_remote_code=True,
)
print("Model loaded")
PY


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
