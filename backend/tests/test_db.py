import pytest
from sqlalchemy import select
from backend.app.db.models import Conversation, Message

@pytest.mark.asyncio
async def test_create_conversation_and_message(db_session):
    # Create conversation
    conv = Conversation(user_id="test_user")
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)
    
    assert conv.id is not None
    assert conv.user_id == "test_user"
    
    # Create message
    msg = Message(conversation_id=conv.id, role="user", content="Hello RAG")
    db_session.add(msg)
    await db_session.commit()
    await db_session.refresh(msg)
    
    assert msg.id is not None
    assert msg.conversation_id == conv.id
    assert msg.role == "user"
    assert msg.content == "Hello RAG"
    
    # Retrieve
    result = await db_session.execute(select(Message).where(Message.conversation_id == conv.id))
    messages = result.scalars().all()
    assert len(messages) == 1
