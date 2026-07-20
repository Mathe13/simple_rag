import pytest
from unittest.mock import patch, MagicMock
from backend.app.core.config import Settings

def test_load_secrets_from_vault_success():
    settings = Settings(OPENAI_BASE_URL="", OPENAI_API_KEY="", EMBEDDING_MODEL="test-model")
    with patch("httpx.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": {"OPENAI_API_KEY": "vault-key", "EMBEDDING_MODEL": "vault-model"}}
        mock_get.return_value = mock_resp
        
        settings.load_secrets_from_vault()
        
        assert settings.OPENAI_API_KEY == "vault-key"
        assert settings.EMBEDDING_MODEL == "vault-model"

def test_load_secrets_from_vault_failure():
    settings = Settings(OPENAI_BASE_URL="", OPENAI_API_KEY="", EMBEDDING_MODEL="test-model")
    with patch("httpx.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_get.return_value = mock_resp
        
        settings.load_secrets_from_vault()
        
        assert settings.OPENAI_API_KEY == ""
        assert settings.EMBEDDING_MODEL == "test-model"

def test_load_secrets_from_vault_exception():
    settings = Settings(OPENAI_BASE_URL="", OPENAI_API_KEY="", EMBEDDING_MODEL="test-model")
    with patch("httpx.get") as mock_get:
        mock_get.side_effect = Exception("Connection Error")
        
        settings.load_secrets_from_vault()
        
        assert settings.OPENAI_API_KEY == ""
        assert settings.EMBEDDING_MODEL == "test-model"

def test_load_secrets_from_vault_local_override():
    settings = Settings(OPENAI_BASE_URL="http://local", OPENAI_API_KEY="local-key", EMBEDDING_MODEL="test-model")
    with patch("httpx.get") as mock_get:
        settings.load_secrets_from_vault()
        
        # httpx should not be called if local override is active
        mock_get.assert_not_called()
        assert settings.OPENAI_API_KEY == "local-key"
