import os
import logging
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

# Import the modularized components
from parsers.cleaner_parser import CleanerParser
from parsers.layout_parser import LayoutParser
from readers.docling_pdf_reader import Reader
from splitters.recursive_splitter import RecursiveSplitter

# Configuration variables
DATA_DIRECTORY = "/opt/data" 
COLLECTION_NAME = "hp_manuals_collection"
DATABASE_URL = "postgresql+psycopg://admin:admin@postgres:5432/hp_rag_db"

def run_ingestion_pipeline():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("worker.ingest.processor")
    
    openai_api_key = os.getenv("OPENAI_API_KEY", "sk-local-dev-key")
    openai_base_url = os.getenv("OPENAI_BASE_URL", "http://model-server:8080/v1")
    embedding_model_name = os.getenv("EMBEDDING_MODEL", "jinaai/jina-embeddings-v2-small-en")

    # Initialize pipeline components
    reader = Reader()
    layout_parser = LayoutParser()
    cleaner = CleanerParser()
    splitter = RecursiveSplitter(chunk_size=800, chunk_overlap=150)

    # 1. Process files through the pipeline
    logger.info(f"Scanning directory: {DATA_DIRECTORY} for PDF documents.")
    pdf_files = list(Path(DATA_DIRECTORY).glob("*.pdf"))
    
    if not pdf_files:
        logger.warning("No PDF documents found in the specified directory.")
        return

    all_chunks = []
    
    for pdf_path in pdf_files:
        file_str = str(pdf_path)
        logger.info(f"Processing: {pdf_path.name}")
        
        # Pipeline execution
        docling_doc = reader.extract_elements(file_str)
        structured_data = layout_parser.group_elements(docling_doc)
        cleaned_data = cleaner.clean(structured_data)
        file_chunks = splitter.split(cleaned_data, source_file=pdf_path.name)
        
        all_chunks.extend(file_chunks)

    logger.info(f"Successfully processed documents into {len(all_chunks)} text chunks.")

    # 2. Embedding and Vector Database Insertion
    embeddings_model = OpenAIEmbeddings(
        model=embedding_model_name, 
        api_key=openai_api_key,
        base_url=openai_base_url,
    )
    
    logger.info("Connecting to PostgreSQL and initializing PGVector store...")
    
    vector_store = PGVector(
        embeddings=embeddings_model,
        collection_name=COLLECTION_NAME,
        connection=DATABASE_URL,
        use_jsonb=True,
    )
    
    logger.info("Inserting document embeddings into the vector database. This may take a moment.")
    vector_store.add_documents(all_chunks)
    
    logger.info("Successfully ingested all chunks into PGVector.")

if __name__ == "__main__":
    run_ingestion_pipeline()