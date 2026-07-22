import os
from fastapi import FastAPI, Depends, HTTPException, Security, Header
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from typing import List, Optional, Union, Any
from sentence_transformers import SentenceTransformer
from llama_cpp import Llama
import tiktoken

app = FastAPI(title="Local OpenAI-Compatible API")

API_KEY = os.environ.get("MODEL_API_KEY", "sk-local-dev-key")
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == f"Bearer {API_KEY}":
        return api_key_header
    raise HTTPException(status_code=401, detail="Invalid or missing API Key")

# Load models at startup
print("Loading embeddings model...")
embeddings_model = SentenceTransformer("BAAI/bge-small-en-v1.5", trust_remote_code=True)

print("Loading Llama model...")
llama_model = Llama(
    model_path="/models/llama/Llama-3.2-1B-Instruct-Q4_K_M.gguf",
    n_ctx=4096, # Context window
    verbose=False
)
print("Models loaded successfully.")

# Models definitions
class EmbeddingRequest(BaseModel):
    input: Union[str, List[str], List[int], List[List[int]]]
    model: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 512

@app.post("/v1/embeddings", dependencies=[Depends(get_api_key)])
async def create_embeddings(req: EmbeddingRequest, x_mock_request: Optional[str] = Header(None)):
    if x_mock_request == "true":
        # Return mock embeddings for load testing
        inputs_len = 1
        if isinstance(req.input, list):
            if len(req.input) > 0 and isinstance(req.input[0], list):
                inputs_len = len(req.input)
            elif len(req.input) > 0 and isinstance(req.input[0], str):
                inputs_len = len(req.input)
                
        data = []
        for i in range(inputs_len):
            embedding = [0.0] * 384
            embedding[0] = 1.0
            data.append({
                "object": "embedding",
                "embedding": embedding,
                "index": i
            })
        return {
            "object": "list",
            "data": data,
            "model": req.model,
            "usage": {"prompt_tokens": 0, "total_tokens": 0}
        }

    inputs = req.input
    
    # Handle single string
    if isinstance(inputs, str):
        inputs = [inputs]
    # Handle list of tokens (single document)
    elif isinstance(inputs, list) and len(inputs) > 0 and isinstance(inputs[0], int):
        enc = tiktoken.get_encoding("cl100k_base")
        inputs = [enc.decode(inputs)]
    # Handle list of lists of tokens (multiple documents)
    elif isinstance(inputs, list) and len(inputs) > 0 and isinstance(inputs[0], list):
        enc = tiktoken.get_encoding("cl100k_base")
        inputs = [enc.decode(t) for t in inputs]
        
    embeddings = embeddings_model.encode(inputs).tolist()
    
    data = []
    for i, emb in enumerate(embeddings):
        data.append({
            "object": "embedding",
            "embedding": emb,
            "index": i
        })
        
    return {
        "object": "list",
        "data": data,
        "model": req.model,
        "usage": {"prompt_tokens": 0, "total_tokens": 0}
    }

@app.post("/v1/chat/completions", dependencies=[Depends(get_api_key)])
async def create_chat_completion(req: ChatCompletionRequest, x_mock_request: Optional[str] = Header(None)):
    if x_mock_request == "true":
        return {
            "id": "mock-chatcmpl",
            "object": "chat.completion",
            "created": 1234567890,
            "model": req.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a mock answer for load testing."
                },
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }

    # Convert messages to llama-cpp format
    formatted_messages = [{"role": msg.role, "content": msg.content} for msg in req.messages]
    
    response = llama_model.create_chat_completion(
        messages=formatted_messages,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
    )
    
    return response

@app.get("/health")
async def health_check():
    return {"status": "ok"}
