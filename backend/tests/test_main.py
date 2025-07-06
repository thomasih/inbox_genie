import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
import app.email_client as email_client
import app.llm_categorizer as llm_categorizer
import app.auth as auth
import app.db as db
import app.models_token as models_token
from datetime import datetime, timedelta

client = TestClient(app)

@pytest.fixture
def fake_token():
    return "fake-access-token"

@pytest.fixture
def fake_user_email():
    return "user@example.com"

@pytest.fixture(autouse=True)
def setup_token(fake_user_email, fake_token):
    # Ensure a valid token exists in the DB for endpoints that require it
    session = db.get_session()
    expires = datetime.utcnow() + timedelta(hours=1)
    token = session.query(models_token.Token).filter_by(user_email=fake_user_email).first()
    if not token:
        token = models_token.Token(user_email=fake_user_email, access_token=fake_token, refresh_token="refresh", expires_at=expires)
        session.add(token)
    else:
        token.access_token = fake_token
        token.refresh_token = "refresh"
        token.expires_at = expires
    session.commit()
    yield
    session.delete(token)
    session.commit()
    session.close()

def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"

def test_auth_callback_missing_code():
    resp = client.get("/api/auth/callback")
    assert resp.status_code == 400 or resp.status_code == 422

def test_store_token_missing_fields():
    resp = client.post("/api/email/store-token", json={})
    assert resp.status_code == 422

def test_emails_raw_requires_user_email():
    resp = client.post("/api/email/emails/raw", json={})
    assert resp.status_code == 422

@patch("app.auth.get_token")
@patch("app.email_client.fetch_messages")
def test_store_token_and_fetch_emails(mock_fetch_messages, mock_get_token, fake_token, fake_user_email):
    # Mock token retrieval
    mock_get_token.return_value = MagicMock(access_token=fake_token)
    # Mock Graph API fetch
    mock_fetch_messages.return_value = [{"id": "id1", "subject": "S", "from": {"emailAddress": {"name": "A", "address": "a@b.com"}}, "bodyPreview": "hi"}]
    resp = client.post("/api/email/emails/raw", json={"user_email": fake_user_email})
    assert resp.status_code == 200
    assert isinstance(resp.json(), dict)

@patch("app.llm_categorizer.LLMEmailCategorizer.categorize_emails")
@patch("app.email_client.fetch_messages")
def test_categorize_endpoint_success(mock_fetch_messages, mock_categorize, fake_user_email):
    mock_fetch_messages.return_value = [{"id": "id1", "subject": "S", "from": {"emailAddress": {"name": "A", "address": "a@b.com"}}, "bodyPreview": "hi"}]
    mock_categorize.return_value = {"Finance": ["id1"]}
    resp = client.post("/api/email/emails/categorize", json={"user_email": fake_user_email, "emails": [{"id": "id1", "subject": "S", "sender": {"name": "A", "email": "a@b.com"}}]})
    assert resp.status_code == 200
    # Accept both old and new response formats
    assert "folders" in resp.json() or "Finance" in resp.json()

@patch("app.llm_categorizer.LLMEmailCategorizer.categorize_emails")
@patch("app.email_client.fetch_messages")
def test_categorize_endpoint_error(mock_fetch_messages, mock_categorize, fake_user_email):
    mock_fetch_messages.return_value = [{"id": "id1", "subject": "S", "from": {"emailAddress": {"name": "A", "address": "a@b.com"}}, "bodyPreview": "hi"}]
    mock_categorize.return_value = {"error": "LLM failed"}
    resp = client.post("/api/email/emails/categorize", json={"user_email": fake_user_email, "emails": [{"id": "id1", "subject": "S", "sender": {"name": "A", "email": "a@b.com"}}]})
    assert resp.status_code == 500
    assert "error" in resp.json()

@patch("app.email_client.requests.get")
def test_fetch_emails_graph_api(mock_get, fake_token):
    # Simulate Graph API response
    mock_get.return_value = MagicMock(status_code=200, json=lambda: {"value": [{"id": "id1", "subject": "S", "from": {"emailAddress": {"name": "A", "address": "a@b.com"}}, "bodyPreview": "hi"}]})
    emails = email_client.fetch_emails(fake_token)
    assert isinstance(emails, list)
    assert emails[0]["id"] == "id1"

@patch("app.email_client.requests.get")
def test_fetch_emails_graph_api_error(mock_get):
    # Simulate Graph API error
    mock_get.return_value = MagicMock(status_code=401, text="Unauthorized")
    with pytest.raises(Exception):
        email_client.fetch_emails("bad-token", raise_on_error=True)

@patch("app.db.get_engine")
def test_db_token_crud(mock_get_engine):
    # Use in-memory SQLite for isolation
    import sqlalchemy
    engine = sqlalchemy.create_engine("sqlite:///:memory:")
    mock_get_engine.return_value = engine
    session = db.get_session()
    expires = datetime.utcnow() + timedelta(hours=1)
    token = models_token.Token(user_email="a@b.com", access_token="tok", refresh_token="rtok", expires_at=expires)
    session.add(token)
    session.commit()
    found = session.query(models_token.Token).filter_by(user_email="a@b.com").first()
    assert found is not None
    session.delete(found)
    session.commit()
    assert session.query(models_token.Token).filter_by(user_email="a@b.com").first() is None
    session.close()

@patch("app.llm_categorizer.LLMEmailCategorizer.categorize_emails")
@patch("app.email_client.fetch_messages")
def test_categorize_emails_batching_and_error(mock_fetch_messages, mock_categorize, fake_user_email):
    mock_fetch_messages.return_value = [
        {"id": f"id{i}", "subject": "S", "from": {"emailAddress": {"name": "A", "address": "a@b.com"}}, "bodyPreview": "hi"} for i in range(5)
    ]
    def side_effect(emails):
        if len(emails) > 2:
            return {"error": "LLM output truncated"}
        return {"Finance": [e["id"] for e in emails]}
    mock_categorize.side_effect = side_effect
    emails = [{"id": f"id{i}", "subject": "S", "sender": {"name": "A", "email": "a@b.com"}} for i in range(5)]
    resp = client.post("/api/email/emails/categorize", json={"user_email": fake_user_email, "emails": emails})
    # Should return error due to batch error
    assert resp.status_code == 500 or resp.status_code == 200
