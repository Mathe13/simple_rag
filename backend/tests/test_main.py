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
        "query": "Fail me"
    }
    response = await async_client.post("/api/chat", json=payload)
    
    assert response.status_code == 500
    assert "LLM Error" in response.json()["detail"]

@pytest.mark.asyncio
@patch("backend.app.main.get_rag_chain")
async def test_get_conversations(mock_get_rag_chain, async_client):
    # Mock the RAG chain
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {"answer": "Mocked"}
    mock_get_rag_chain.return_value = mock_chain
    
    # Create a conversation by chatting
    res1 = await async_client.post("/api/chat", json={"query": "Test msg 1"})
    conv_id1 = res1.json()["conversation_id"]
    
    res2 = await async_client.post("/api/chat", json={"query": "Test msg 2"})
    conv_id2 = res2.json()["conversation_id"]

    # Fetch conversations
    response = await async_client.get("/api/conversations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    conv_ids = [c["id"] for c in data]
    assert conv_id1 in conv_ids
    assert conv_id2 in conv_ids

@pytest.mark.asyncio
@patch("backend.app.main.get_rag_chain")
async def test_get_messages(mock_get_rag_chain, async_client):
    # Mock the RAG chain
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {"answer": "Mocked"}
    mock_get_rag_chain.return_value = mock_chain
    
    # Create a conversation by chatting
    res1 = await async_client.post("/api/chat", json={"query": "Q1"})
    conv_id = res1.json()["conversation_id"]
    
    await async_client.post("/api/chat", json={"query": "Q2", "conversation_id": conv_id})

    # Fetch messages
    response = await async_client.get(f"/api/conversations/{conv_id}/messages")
    assert response.status_code == 200
    messages = response.json()
    assert len(messages) == 4 # Q1, Mocked, Q2, Mocked
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Q1"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Mocked"

@pytest.mark.asyncio
async def test_get_messages_not_found(async_client):
    response = await async_client.get(f"/api/conversations/invalid-id-123/messages")
    assert response.status_code == 404

@pytest.mark.asyncio
@patch("backend.app.main.get_rag_chain")
async def test_get_messages_unauthorized(mock_get_rag_chain, async_client):
    from backend.app.main import app
    # Mock the RAG chain
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {"answer": "Mocked"}
    mock_get_rag_chain.return_value = mock_chain
    
    # Create a conversation with default mock user "test_user123"
    res1 = await async_client.post("/api/chat", json={"query": "Q1"})
    conv_id = res1.json()["conversation_id"]
    
    # Override auth to a different user
    from backend.app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: "another_user"
    
    response = await async_client.get(f"/api/conversations/{conv_id}/messages")
    assert response.status_code == 403
    
    # Reset override
    app.dependency_overrides[get_current_user] = lambda: "test_user123"
