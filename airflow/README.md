# Airflow Ingestion Pipeline

This folder contains the Apache Airflow configuration and DAGs responsible for extracting, chunking, and embedding documents into our PGVector database.

## Architecture

The ingestion pipeline uses the **DockerOperator** to spin up isolated worker containers (`simple_rag_worker:latest`) for each task. This ensures that heavy processing (like PDF parsing and embedding) doesn't run directly on the Airflow scheduler, keeping the system stable and scalable.

### Key Components

- **DAG (`dags/ingest_docs.py`)**: Defines the workflow `ingest_hp_manuals_to_pgvector`. It mounts the host's `data/` directory and points the worker to the local `model-server` to fetch embeddings.
- **Worker Image (`worker/`)**: The DockerOperator uses the `simple_rag_worker:latest` image to execute the LangChain ingestion script.
- **Docker Socket**: The Airflow containers are granted access to the host's Docker socket by inheriting the host's `docker` group ID (`995`) in `docker-compose.yaml`. This allows the Airflow scheduler to orchestrate new containers on the host engine.

## Troubleshooting & Gotchas

### 1. Rebuilding the Worker Image
Because the `worker-image` service in `docker-compose.yaml` is assigned the `donotstart` profile, running `docker compose up --build` **will not** rebuild the worker image automatically.

If you modify the python code in the `worker/` directory (like `ingest.py`), you **must** manually rebuild the worker image before triggering the DAG:

```bash
docker build -t simple_rag_worker:latest ./worker
```

### 2. Airflow UI Logs (403 Forbidden)
When running Airflow locally via Docker Compose, you might encounter a `403 FORBIDDEN` error when clicking on task logs in the Airflow Web UI. This is a known issue caused by a `secret_key` mismatch between the webserver and the worker node. 

**This does not mean your task failed.** If the DAG state is marked as `success`, the ingestion worked perfectly!

If you need to debug a failing ingestion task, it is much easier to run the worker container manually from your terminal to see the raw python traceback:

```bash
docker run --rm -v $(pwd)/data:/opt/data \
  -e OPENAI_API_KEY=sk-local-dev-key \
  -e OPENAI_BASE_URL=http://model-server:8080/v1 \
  -e EMBEDDING_MODEL=BAAI/bge-small-en-v1.5 \
  --network simple_rag_default \
  simple_rag_worker:latest
```
