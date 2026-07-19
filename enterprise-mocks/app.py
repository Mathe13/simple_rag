import jwt
import json
import os
from pydantic import BaseModel
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, status

# Initialize FastAPI app
app = FastAPI(
    title="Enterprise Mocks API", 
    description="Mock services for SSO Authentication and Vault Secrets"
)

# ==========================================
# SSO Mock (Single Sign-On)
# ==========================================
MOCK_JWT_SECRET = "super-secret-mock-key-for-local-testing"

class LoginCredentials(BaseModel):
    username: str
    password: str

@app.post("/sso/token", status_code=status.HTTP_200_OK)
async def generate_mock_jwt(credentials: LoginCredentials):
    """
    Simulates an SSO login. 
    It accepts any username/password and returns a signed JWT token.
    """
    # Expiration time set to 2 hours from now
    expiration_time = datetime.utcnow() + timedelta(hours=2)
    
    payload = {
        "sub": credentials.username,
        "role": "employee",
        "exp": expiration_time
    }
    
    # Generate the mock JWT
    access_token = jwt.encode(payload, MOCK_JWT_SECRET, algorithm="HS256")
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "expires_in": 7200
    }

# ==========================================
# Vault Mock (Secrets Management)
# ==========================================
SECRETS_FILE_PATH = os.getenv("SECRETS_FILE_PATH", "secrets.json")

@app.get("/vault/secrets/{secret_path}", status_code=status.HTTP_200_OK)
async def retrieve_secret(secret_path: str):
    """
    Simulates a Vault service.
    Reads from a local JSON file and returns the requested secret payload.
    """
    try:
        with open(SECRETS_FILE_PATH, "r") as file:
            vault_data = json.load(file)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Vault storage file not found."
        )

    # Check if the requested path exists in our mock vault
    if secret_path not in vault_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Secret path '{secret_path}' not found in Vault."
        )

    return {"data": vault_data[secret_path]}