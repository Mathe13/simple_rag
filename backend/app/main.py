from fastapi import FastAPI, Depends, HTTPException, Header, BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

from backend.app.core.config import settings
from backend.app.db.models import Base, Conversation, Message
from backend.app.services.rag_chain import get_rag_chain
from backend.app.core.auth import get_current_user

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
    conversation_id: Optional[str] = None
    query: str

class ChatResponse(BaseModel):
    conversation_id: str
    answer: str

class ConversationResponse(BaseModel):
    id: str
    created_at: datetime

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime

@app.on_event("startup")
async def startup_event():
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def prune_semantic_cache(db: AsyncSession):
    try:
        # Delete Expired Entries
        expired_sql = text(
            f"""
            DELETE FROM langchain_pg_embedding 
            WHERE collection_id = (SELECT uuid FROM langchain_pg_collection WHERE name = 'semantic_cache') 
            AND (cmetadata->>'created_at')::timestamptz < NOW() - INTERVAL '{settings.SEMANTIC_CACHE_TTL_HOURS} hours'
            """
        )
        await db.execute(expired_sql)
        
        # Enforce Max Size
        size_sql = text(
            f"""
            DELETE FROM langchain_pg_embedding
            WHERE collection_id = (SELECT uuid FROM langchain_pg_collection WHERE name = 'semantic_cache') 
            AND id NOT IN (
                SELECT id FROM langchain_pg_embedding 
                WHERE collection_id = (SELECT uuid FROM langchain_pg_collection WHERE name = 'semantic_cache')
                ORDER BY cmetadata->>'created_at' DESC 
                LIMIT {settings.SEMANTIC_CACHE_MAX_SIZE}
            )
            """
        )
        await db.execute(size_sql)
        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"Error pruning semantic cache: {e}")

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest, 
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_mock_request: Optional[str] = Header(None)
):
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
        new_conv = Conversation(user_id=current_user)
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

    # Initialize Semantic Cache
    embeddings = OpenAIEmbeddings(model=settings.EMBEDDING_MODEL)
    semantic_cache = PGVector(
        embeddings=embeddings,
        collection_name="semantic_cache",
        connection=settings.VECTOR_DB_URL,
        use_jsonb=True
    )

    # 3. Cache Hit Logic (Pre-LLM)
    try:
        docs_with_scores = await run_in_threadpool(
            semantic_cache.similarity_search_with_score,
            request.query,
            k=1
        )
        if docs_with_scores and docs_with_scores[0][1] < 0.05:
            matched_doc, distance = docs_with_scores[0]
            cached_answer = matched_doc.metadata.get("answer")
            created_at_str = matched_doc.metadata.get("created_at")
            
            # TTL Validation (e.g., 24 hours)
            is_valid_cache = True
            if created_at_str:
                created_at = datetime.fromisoformat(created_at_str)
                time_diff = datetime.now(timezone.utc) - created_at
                if time_diff.total_seconds() > (settings.SEMANTIC_CACHE_TTL_HOURS * 3600):
                    is_valid_cache = False
            
            if cached_answer and is_valid_cache:
                # Save to history without the [CACHED] tag to keep DB clean
                user_msg = Message(conversation_id=conv_id, role="user", content=request.query)
                ai_msg = Message(conversation_id=conv_id, role="assistant", content=cached_answer)
                db.add_all([user_msg, ai_msg])
                await db.commit()
                
                # Return with [CACHED] tag for frontend visibility
                return ChatResponse(conversation_id=conv_id, answer=f"[CACHED] {cached_answer}")
    except Exception as e:
        await db.rollback()
        pass

    # 4. Cache Miss Logic: Call the RAG Chain
    rag_chain = get_rag_chain(mock_request=(x_mock_request == "true"))
    try:
        response = rag_chain.invoke({
            "input": request.query,
            "chat_history": chat_history
        })
        answer_text = response["answer"]

        # Cache Insertion
        await run_in_threadpool(
            semantic_cache.add_documents,
            [Document(page_content=request.query, metadata={"answer": answer_text, "created_at": datetime.now(timezone.utc).isoformat()})]
        )
        
        background_tasks.add_task(prune_semantic_cache, db)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

    # 5. Save the new messages to the database
    user_msg = Message(conversation_id=conv_id, role="user", content=request.query)
    ai_msg = Message(conversation_id=conv_id, role="assistant", content=answer_text)
    
    db.add_all([user_msg, ai_msg])
    await db.commit()

    return ChatResponse(conversation_id=conv_id, answer=answer_text)

@app.get("/api/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user)
        .order_by(Conversation.created_at.desc())
    )
    return result.scalars().all()

@app.get("/api/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def list_messages(
    conversation_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify ownership
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = result.scalars().first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.user_id != current_user:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")
        
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    return result.scalars().all()

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}