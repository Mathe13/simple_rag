import os
import logging
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

# Configuration variables
DATA_DIRECTORY = "/opt/data" 
COLLECTION_NAME = "hp_manuals_collection"

# Using psycopg driver as recommended by SQLAlchemy 2.0 and langchain-postgres
DATABASE_URL = "postgresql+psycopg://admin:admin@postgres:5432/hp_rag_db"

def ingest_and_vectorize_documents():
    """
    Extracts text from PDFs, splits them into manageable chunks, 
    generates embeddings, and upserts them into the PGVector database.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("worker.ingest")
    
    # 1. Fetch API Key and Base URL
    openai_api_key = os.getenv("OPENAI_API_KEY", "sk-local-dev-key")
    openai_base_url = os.getenv("OPENAI_BASE_URL", "http://model-server:8080/v1")
    embedding_model_name = os.getenv("EMBEDDING_MODEL", "jinaai/jina-embeddings-v2-small-en")
    
    logger.info(f"Scanning directory: {DATA_DIRECTORY} for PDF documents.")
    
    # 2. Document Extraction
    loader = PyPDFDirectoryLoader(DATA_DIRECTORY)
    documents = loader.load()
    
    if not documents:
        logger.warning("No PDF documents found in the specified directory.")
        return
        
    logger.info(f"Successfully loaded {len(documents)} pages across all PDFs.")

    # 3. Chunking Strategy
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        length_function=len,
        add_start_index=True,
    )
    
    chunks = text_splitter.split_documents(documents)
    logger.info(f"Split documents into {len(chunks)} text chunks.")

    # 4. Embedding and Vector Database Insertion
    embeddings_model = OpenAIEmbeddings(
        model=embedding_model_name, 
        api_key=openai_api_key,
        base_url=openai_base_url,
    )
    
    logger.info("Connecting to PostgreSQL and initializing PGVector store...")
    
    # Initialize the vector store connection
    vector_store = PGVector(
        embeddings=embeddings_model,
        collection_name=COLLECTION_NAME,
        connection=DATABASE_URL,
        use_jsonb=True,
    )
    
    # Perform the upsert operation
    logger.info("Inserting document embeddings into the vector database. This may take a moment.")
    vector_store.add_documents(chunks)
    
    logger.info("Successfully ingested all chunks into PGVector.")

if __name__ == "__main__":
    ingest_and_vectorize_documents()
