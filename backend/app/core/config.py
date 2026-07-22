import os
import httpx
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "HP RAG Chatbot API"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://admin:admin@postgres:5432/hp_rag_db")
    # For LangChain PGVector, we need the sync psycopg driver
    VECTOR_DB_URL: str = os.getenv("VECTOR_DB_URL", "postgresql+psycopg://admin:admin@postgres:5432/hp_rag_db")
    MOCK_VAULT_URL: str = os.getenv("MOCK_VAULT_URL", "http://enterprise-mocks:8001/vault/secrets")
    MOCK_SSO_URL: str = os.getenv("MOCK_SSO_URL", "http://enterprise-mocks:8001/sso")
    
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    CHAT_MODEL: str = "gpt-3.5-turbo"
    
    SEMANTIC_CACHE_TTL_HOURS: int = 1
    SEMANTIC_CACHE_MAX_SIZE: int = 1000
    
    JWT_SECRET: str = "super-secret-mock-key-for-local-testing"
    JWT_ALGORITHM: str = "HS256"
    SSO_TOKEN_URL: str = "http://enterprise-mocks:8001/sso/token"
    
    def load_secrets_from_vault(self):
        """Fetches the OpenAI key from the Mock Vault on startup"""
        if self.OPENAI_BASE_URL and self.OPENAI_API_KEY:
            print("Local override detected, skipping Mock Vault for LLM credentials.")
            return
        try:
            # We use a sync request here just for the initial startup
            response = httpx.get(f"{self.MOCK_VAULT_URL}/llm-credentials", timeout=5.0)
            if response.status_code == 200:
                data = response.json().get("data", {})
                self.OPENAI_API_KEY = data.get("OPENAI_API_KEY", "")
                self.EMBEDDING_MODEL = data.get("EMBEDDING_MODEL", self.EMBEDDING_MODEL)
                print("Secrets successfully loaded from Mock Vault.")
            else:
                print(f"Warning: Mock Vault returned {response.status_code}")
        except Exception as e:
            print(f"Failed to connect to Mock Vault: {e}")

settings = Settings()
settings.load_secrets_from_vault()

# Set the environment variables so Langchain can find them natively
os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
if settings.OPENAI_BASE_URL:
    os.environ["OPENAI_BASE_URL"] = settings.OPENAI_BASE_URL