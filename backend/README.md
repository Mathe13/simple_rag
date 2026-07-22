# Backend API

This folder contains the FastAPI-based backend for the Simple RAG application. It manages the main user-facing REST API, orchestrates the Retrieval-Augmented Generation (RAG) pipeline, and interacts with the database.

## Architecture

The backend serves as the core orchestrator. It receives user queries, fetches relevant documents from the vector database, queries the local language model (served by `model-server`), and caches results for performance.

### Key Components

1. **FastAPI**: The web framework providing the asynchronous REST API.
2. **LangChain & PGVector**: Used for building the RAG pipeline and connecting to the PostgreSQL database with the pgvector extension for semantic search and caching.
3. **SQLAlchemy**: The ORM used for storing and retrieving relational chat history (conversations and messages).

## Configuration & Security

The backend requires several environment variables to function correctly, many of which are managed via an external Vault in local development.

- **`DATABASE_URL`**: Connection string for the async PostgreSQL database (relational data).
- **`VECTOR_DB_URL`**: Connection string for the sync psycopg PostgreSQL driver (vector embeddings).
- **`OPENAI_BASE_URL`** & **`OPENAI_API_KEY`**: Pointing to the local `model-server` instead of OpenAI.

## Endpoints

- `GET /api/health`: Healthcheck endpoint returning `{"status": "healthy"}`.
- `POST /api/chat`: Main RAG endpoint for processing user queries. Includes Semantic Caching to speed up frequent questions.
- `GET /api/conversations`: Retrieves a list of user conversations.
- `GET /api/conversations/{id}/messages`: Retrieves the message history for a specific conversation.

## Building & Running

The service is configured in the main `docker-compose.yaml` under the `backend` service name. It runs internally on port 8000 and depends on `postgres` and `model-server`.

To view its logs during operation:
```bash
docker compose logs -f backend
```
