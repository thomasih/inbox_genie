import pytest
from app.models_token import Token
from datetime import datetime

def test_token_model_fields():
    t = Token(user_email="a@b.com", access_token="tok", refresh_token="rtok", expires_at=datetime.utcnow())
    assert t.user_email == "a@b.com"
    assert t.access_token == "tok"
    assert t.refresh_token == "rtok"
    assert t.expires_at is not None

def test_token_model_repr():
    t = Token(user_email="a@b.com", access_token="tok", refresh_token="rtok", expires_at=datetime(2025, 7, 6, 12, 0, 0))
    r = repr(t)
    assert "a@b.com" in r
    assert "tok" in r
    assert "rtok" in r
    assert "2025" in r
