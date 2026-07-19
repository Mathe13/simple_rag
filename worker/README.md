# Simple RAG Worker

This folder contains the Python code and Docker configuration for the ingestion worker. The worker's job is to read documents (like PDFs), split them into manageable chunks, generate embeddings via the `model-server`, and store the results in the `pgvector` database.

## Architecture

The worker is designed to be a standalone, ephemeral container. It executes its ingestion script (`ingest.py`) and immediately exits upon completion or failure.

### Key Components

- **`ingest.py`**: The main execution script. It uses LangChain's `PyPDFDirectoryLoader` to read manuals from the mounted `/opt/data` directory, splits them, and uses `OpenAIEmbeddings` to fetch vector embeddings from our local OpenAI-compatible `model-server`. Finally, it uses `PGVector` to store these embeddings.
- **`Dockerfile`**: Defines the `simple_rag_worker:latest` image, built on top of `python:3.11-slim`. It installs system dependencies (like `libpq-dev` and `gcc` for `psycopg2`) and python requirements.
- **`requirements.txt`**: Lists all the necessary python packages including `langchain`, `langchain-openai`, `langchain-postgres`, and `psycopg2-binary`.

## Configuration

The worker expects the following environment variables (which are automatically injected by the Airflow `DockerOperator` in the production pipeline):

- `OPENAI_BASE_URL`: URL to the embedding model server (e.g., `http://model-server:8080/v1`).
- `OPENAI_API_KEY`: API key for the model server.
- `EMBEDDING_MODEL`: The specific model to use (e.g., `BAAI/bge-small-en-v1.5`).

## Development & Testing

Since this worker runs in isolation, you can easily test any changes to the ingestion logic by running the container manually:

1. **Rebuild the image** (required after any change to `ingest.py`):
   ```bash
   docker build -t simple_rag_worker:latest ./worker
   ```

2. **Run the container manually**:
   ```bash
   docker run --rm -v $(pwd)/data:/opt/data \
     -e OPENAI_API_KEY=sk-local-dev-key \
     -e OPENAI_BASE_URL=http://model-server:8080/v1 \
     -e EMBEDDING_MODEL=BAAI/bge-small-en-v1.5 \
     --network simple_rag_default \
     simple_rag_worker:latest
   ```

Note: Because this worker is orchestrated by Airflow dynamically, it is marked with the `donotstart` profile in `docker-compose.yaml` to prevent it from spinning up automatically alongside persistent services like the database or web servers.
