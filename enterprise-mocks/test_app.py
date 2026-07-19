import os
import json
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

@pytest.fixture
def mock_secrets_file(tmp_path, monkeypatch):
    secrets_file = tmp_path / "secrets.json"
    secrets_data = {
        "db-credentials": {
            "username": "admin",
            "password": "secretpassword"
        }
    }
    with open(secrets_file, "w") as f:
        json.dump(secrets_data, f)
    
    monkeypatch.setattr("app.SECRETS_FILE_PATH", str(secrets_file))
    return secrets_file

def test_sso_token():
    response = client.post("/sso/token", json={
        "username": "testuser",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 7200

def test_vault_secret_found(mock_secrets_file):
    response = client.get("/vault/secrets/db-credentials")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["data"]["username"] == "admin"

def test_vault_secret_not_found(mock_secrets_file):
    response = client.get("/vault/secrets/non-existent")
    assert response.status_code == 404
    data = response.json()
    assert "not found in Vault" in data["detail"]

def test_vault_file_not_found(monkeypatch):
    monkeypatch.setattr("app.SECRETS_FILE_PATH", "does_not_exist.json")
    response = client.get("/vault/secrets/db-credentials")
    assert response.status_code == 500
    data = response.json()
    assert data["detail"] == "Vault storage file not found."
