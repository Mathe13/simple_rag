import pytest
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_health_check(async_client):
    response = await async_client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
@patch("backend.app.main.get_rag_chain")
async def test_chat_endpoint(mock_get_rag_chain, async_client):
    # Mock the RAG chain
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {"answer": "Mocked RAG response"}
    mock_get_rag_chain.return_value = mock_chain
    
    # Make request
    payload = {
        "user_id": "user123",
        "query": "How do I print a test page?"
    }
    response = await async_client.post("/api/chat", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert data["answer"] == "Mocked RAG response"
    
    # Verify chain was called
    mock_chain.invoke.assert_called_once()
    
    # Second request with conversation_id
    payload_2 = {
        "user_id": "user123",
        "conversation_id": data["conversation_id"],
        "query": "Follow up question?"
    }
    response_2 = await async_client.post("/api/chat", json=payload_2)
    assert response_2.status_code == 200
    assert response_2.json()["conversation_id"] == data["conversation_id"]

@pytest.mark.asyncio
@patch("backend.app.main.get_rag_chain")
async def test_chat_endpoint_exception(mock_get_rag_chain, async_client):
    # Mock chain to raise exception
    mock_chain = MagicMock()
    mock_chain.invoke.side_effect = Exception("LLM Error")
    mock_get_rag_chain.return_value = mock_chain
    
    payload = {
        "user_id": "user123",
        "query": "Fail me"
    }
    response = await async_client.post("/api/chat", json=payload)
    
    assert response.status_code == 500
    assert "LLM Error" in response.json()["detail"]
