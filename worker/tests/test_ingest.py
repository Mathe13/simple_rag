import pytest
from unittest.mock import patch, MagicMock

from ingest import ingest_and_vectorize_documents

@patch("ingest.PGVector")
@patch("ingest.OpenAIEmbeddings")
@patch("ingest.RecursiveCharacterTextSplitter")
@patch("ingest.PyPDFDirectoryLoader")
def test_ingest_and_vectorize_documents(
    mock_pdf_loader_class, 
    mock_text_splitter_class,
    mock_embeddings_class,
    mock_pgvector_class
):
    # Setup mocks
    mock_loader_instance = MagicMock()
    mock_pdf_loader_class.return_value = mock_loader_instance
    mock_loader_instance.load.return_value = ["doc1", "doc2"]
    
    mock_splitter_instance = MagicMock()
    mock_text_splitter_class.return_value = mock_splitter_instance
    mock_splitter_instance.split_documents.return_value = ["chunk1", "chunk2", "chunk3"]
    
    mock_vector_store_instance = MagicMock()
    mock_pgvector_class.return_value = mock_vector_store_instance

    # Run the function
    ingest_and_vectorize_documents()

    # Assertions
    mock_pdf_loader_class.assert_called_once_with("/opt/data")
    mock_loader_instance.load.assert_called_once()
    
    mock_text_splitter_class.assert_called_once_with(
        chunk_size=800,
        chunk_overlap=150,
        length_function=len,
        add_start_index=True,
    )
    mock_splitter_instance.split_documents.assert_called_once_with(["doc1", "doc2"])
    
    mock_embeddings_class.assert_called_once()
    
    mock_pgvector_class.assert_called_once()
    mock_vector_store_instance.add_documents.assert_called_once_with(["chunk1", "chunk2", "chunk3"])

@patch("ingest.PyPDFDirectoryLoader")
def test_ingest_and_vectorize_no_docs(mock_pdf_loader_class):
    mock_loader_instance = MagicMock()
    mock_pdf_loader_class.return_value = mock_loader_instance
    # Simulate empty directory
    mock_loader_instance.load.return_value = []
    
    # Should return early and not error
    ingest_and_vectorize_documents()
    
    mock_loader_instance.load.assert_called_once()
