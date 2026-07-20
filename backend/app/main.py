from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from langchain_core.messages import HumanMessage, AIMessage

from backend.app.core.config import settings
from backend.app.db.models import Base, Conversation, Message
from backend.app.services.rag_chain import get_rag_chain

# Database Setup (SQLAlchemy Async)
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# FastAPI Initialization
app = FastAPI(title=settings.PROJECT_NAME)

# Pydantic Schemas for Requests/Responses
class ChatRequest(BaseModel):
    user_id: str
    conversation_id: Optional[str] = None
    query: str

class ChatResponse(BaseModel):
    conversation_id: str
    answer: str

@app.on_event("startup")
async def startup_event():
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Main RAG endpoint.
    1. Fetches or creates a conversation.
    2. Loads chat history.
    3. Queries LangChain.
    4. Saves the new interaction.
    """
    # 1. Handle Conversation ID
    conv_id = request.conversation_id
    if not conv_id:
        new_conv = Conversation(user_id=request.user_id)
        db.add(new_conv)
        await db.commit()
        await db.refresh(new_conv)
        conv_id = new_conv.id
    
    # 2. Retrieve Chat History from PostgreSQL
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.created_at)
    )
    db_messages = result.scalars().all()
    
    # Format history for LangChain
    chat_history = []
    for msg in db_messages:
        if msg.role == "user":
            chat_history.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            chat_history.append(AIMessage(content=msg.content))

    # 3. Call the RAG Chain
    rag_chain = get_rag_chain()
    try:
        response = rag_chain.invoke({
            "input": request.query,
            "chat_history": chat_history
        })
        answer_text = response["answer"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

    # 4. Save the new messages to the database
    user_msg = Message(conversation_id=conv_id, role="user", content=request.query)
    ai_msg = Message(conversation_id=conv_id, role="assistant", content=answer_text)
    
    db.add_all([user_msg, ai_msg])
    await db.commit()

    return ChatResponse(conversation_id=conv_id, answer=answer_text)

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}