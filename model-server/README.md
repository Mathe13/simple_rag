# Model Server

This folder contains the FastAPI-based AI Model Server that provides OpenAI-compatible REST API endpoints for both text embeddings and chat completions.

## Architecture

The server acts as a unified backend for the AI capabilities of our Simple RAG system, serving models entirely locally. 
Because it implements the `v1/embeddings` and `v1/chat/completions` routes, it acts as a drop-in replacement for OpenAI in standard frameworks like LangChain.

### Models Served

1. **Embeddings Model**: `BAAI/bge-small-en-v1.5`
   - Served via `sentence-transformers` for creating vector representations of text.
   - Robustly handles inputs as strings, lists of strings, or tokenized representations (using `tiktoken`).

2. **Chat Completions Model**: `Llama-3.2-1B-Instruct`
   - Served via `llama-cpp-python` (`llama_cpp`) using the quantized GGUF format for CPU-efficient inference.
   - Model location in container: `/models/llama/Llama-3.2-1B-Instruct-Q4_K_M.gguf`.

## Configuration & Security

The server is protected by a Bearer token API key mechanism to mirror standard AI API structures. 
The key is passed via the `Authorization` header.

- **Environment Variable**: `MODEL_API_KEY` (defaults to `sk-local-dev-key` if not provided).
- **Internal Port**: 8080 (Mapped to 9000 on the host via `docker-compose`).

## Endpoints

- `POST /v1/embeddings`: Generates vector embeddings for input documents.
- `POST /v1/chat/completions`: Generates chat-based conversational responses using the Llama model.
- `GET /health`: Healthcheck endpoint returning `{"status": "ok"}`.

## Building & Running

The service is configured in the main `docker-compose.yaml` under the `model-server` service name. It maps the host's `/models/llama` folder into the container to prevent downloading large GGUF files every time.

To view its logs during operation:
```bash
docker compose logs -f model-server
```
