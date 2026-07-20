import jwt
import pytest
from fastapi import HTTPException
from backend.app.core.auth import get_current_user
from backend.app.core.config import settings

def test_get_current_user_valid_token():
    payload = {"sub": "test_employee"}
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    user = get_current_user(token=token)
    assert user == "test_employee"

def test_get_current_user_missing_sub():
    payload = {"role": "employee"}
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token=token)
    assert exc_info.value.status_code == 401

def test_get_current_user_expired_token():
    payload = {"sub": "test", "exp": 100000000} # Expired timestamp
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token=token)
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()

def test_get_current_user_invalid_token():
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token="invalid.token.here")
    assert exc_info.value.status_code == 401
