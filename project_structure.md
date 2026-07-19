*   **`simple_rag/`**
    *   **`.github/workflows/`** - CI Pipelines (Lint, Pytest, Coverage)
    *   **`docker-compose.yml`** - Orchestration of all services
    *   **`Makefile`** - (Optional) Useful shortcuts: `make up`, `make test`
    *   **`.env.example`** - Environment variables template
    *   **`README.md`** - required doc (deployment and architecture instructions)
    *   **`enterprise-mocks/`** - Corporate infrastructure mock services
        *   `app.py` - Lightweight FastAPI with `/sso/login` and `/vault/secrets` routes
        *   `secrets.json` - Static file consumed by Mock Vault
        *   `Dockerfile`
        *   `requirements.txt`
    *   **`airflow/`** - Data pipeline (Ingestion)
        *   **`dags/`**
            *   `ingest_docs.py` - DAG: Extraction -> Chunking -> Upsert into PGVector
        *   `requirements.txt` - Specific dependencies (Langchain, PyPDF, psycopg2)
        *   `Dockerfile` - Custom image based on apache/airflow
    *   **`backend/`** - API core (Inference)
        *   **`app/`**
            *   **`api/`**
                *   `dependencies.py` - Dependency injection (e.g., validate JWT, connect DB)
                *   **`routers/`** - Endpoints (`/chat`, `/history`)
            *   **`core/`**
                *   `config.py` - Fetches credentials from Mock Vault on startup
            *   **`db/`**
                *   `models.py` - SQLAlchemy (Tables: User, Session, Message)
                *   `vector_store.py` - PGVector interface via Langchain
            *   **`services/`**
                *   `rag_chain.py` - LangChain logic (Retriever, Prompt, LLM)
            *   `main.py` - FastAPI initialization
        *   **`tests/`** - Coverage >90% (Pytest + Mocks)
            *   `conftest.py` - Pytest fixtures
            *   `test_api.py`
            *   `test_rag.py`
        *   `Dockerfile`
        *   `requirements.txt`
    *   **`frontend/`** - User Interface
        *   `app.py` - Streamlit or Chainlit code
        *   `Dockerfile`
        *   `requirements.txt`
    *   **`data/`** - Source files
        *   `envy_user_guide.pdf` - Provided
        *   `omen_service_guide.pdf` - Provided
    *   **`evaluation/`** - Stress and quality tests (Differentiators)
        *   `locustfile.py` - Load test (Requests per minute)
        *   `benchmark_ragas.py` - Script to test response quality (Faithfulness)
        *   `evaluation_dataset.json` - Expected questions and answers for benchmark