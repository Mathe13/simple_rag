from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from backend.app.core.config import settings

def get_rag_chain(mock_request: bool = False):
    """
    Constructs the LangChain retrieval pipeline.
    It includes a history-aware retriever to contextualize follow-up questions.
    """
    default_headers = {"x-mock-request": "true"} if mock_request else None
    
    # 1. Initialize Vector Store
    embeddings = OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        base_url=settings.OPENAI_BASE_URL if settings.OPENAI_BASE_URL else None,
        default_headers=default_headers
    )
    
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name="hp_manuals_collection",
        connection=settings.VECTOR_DB_URL,
        use_jsonb=True,
    )
    
    # Use cosine similarity, returning top 4 chunks
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})
    
    # 2. Initialize LLM
    llm = ChatOpenAI(
        model=settings.CHAT_MODEL,
        temperature=0,
        base_url=settings.OPENAI_BASE_URL if settings.OPENAI_BASE_URL else None,
        default_headers=default_headers
    )

    # 3. Contextualize Question Prompt (Handles Chat History)
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    # 4. Answer Generation Prompt
    system_prompt = (
        "You are an expert technical support agent for HP products. "
        "Use the following pieces of retrieved context to answer the question. "
        "If the answer is not in the context, explicitly say that you do not know "
        "and do not try to make up an answer. "
        "Keep the answer concise and professional.\n\n"
        "Context: {context}"
    )
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    
    return rag_chain