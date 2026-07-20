import pytest
from unittest.mock import patch, MagicMock

@patch("backend.app.services.rag_chain.OpenAIEmbeddings")
@patch("backend.app.services.rag_chain.PGVector")
@patch("backend.app.services.rag_chain.ChatOpenAI")
def test_get_rag_chain(mock_chat, mock_pgvector, mock_embeddings):
    # Mocking these external dependencies ensures we don't hit the network or DB
    from backend.app.services.rag_chain import get_rag_chain
    
    mock_embeddings.return_value = MagicMock()
    mock_pgvector.return_value = MagicMock()
    mock_chat.return_value = MagicMock()
    
    chain = get_rag_chain()
    
    assert chain is not None
    mock_embeddings.assert_called_once()
    mock_pgvector.assert_called_once()
    mock_chat.assert_called_once()
