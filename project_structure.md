*   **`simple_rag/`**
    *   **`.github/workflows/`** - CI Pipelines (Lint, Pytest, Coverage)
    *   **`docker-compose.yml`** - Orchestration of all services
    *   **`Makefile`** - Useful shortcuts: `make start`, `make stop`, `make build`, `make test`
    *   **`.env.example`** - Environment variables template
    *   **`README.md`** - Deployment and architecture instructions
    *   **`enterprise-mocks/`** - Corporate infrastructure mock services
        *   `app.py` - Lightweight FastAPI with `/sso/token` and `/vault/secrets` routes
        *   `Dockerfile`
        *   `requirements.txt`
    *   **`airflow/`** - Data pipeline (Ingestion)
        *   **`dags/`**
            *   `ingest_docs.py` - DAG: Extraction -> Chunking -> Upsert into PGVector
        *   `requirements.txt` - Specific dependencies (Langchain, PyPDF, psycopg2)
        *   `Dockerfile` - Custom image based on apache/airflow
    *   **`backend/`** - API core (Inference)
        *   **`app/`**
            *   **`core/`**
                *   `auth.py` - Auth dependencies (validate JWT/SSO tokens)
                *   `config.py` - Fetches credentials from Mock Vault on startup
            *   **`db/`**
                *   `models.py` - SQLAlchemy models (Conversation, Message)
            *   **`services/`**
                *   `rag_chain.py` - LangChain RAG pipeline logic
            *   `main.py` - FastAPI initialization, endpoints (`/chat`, `/conversations`, `/messages`), and semantic cache
        *   **`tests/`** - Test suite with mocked external integrations (Pytest)
            *   `conftest.py` - Pytest fixtures (client, db engines)
            *   `test_auth.py` - Authentication tests
            *   `test_config.py` - Configuration loading tests
            *   `test_db.py` - Database session and setup tests
            *   `test_main.py` - Chat endpoints & semantic caching tests
            *   `test_rag_chain.py` - RAG chain retrieval and generation tests
        *   `Dockerfile`
        *   `pyproject.toml` - uv package configuration
    *   **`frontend/`** - User Interface
        *   `app.py` - Streamlit application (Chat UI with history and erasure)
        *   `Dockerfile`
        *   `pyproject.toml`
    *   **`worker/`** - Manual ingestion worker
        *   `ingest.py` - Local Python script for document loading & embedding
        *   `pyproject.toml`
    *   **`data/`** - Source PDF documents
        *   `envy_user_guide.pdf`
        *   `omen_service_guide.pdf`
    *   **`evaluation/`** - Stress and accuracy quality testing
        *   `locustfile.py` - Load testing script simulating concurrent users
        *   `benchmark_ragas.py` - Ragas-based generation & retrieval quality evaluation
        *   `qa_dataset.json` - Evaluative dataset containing questions, contexts, and ground truths