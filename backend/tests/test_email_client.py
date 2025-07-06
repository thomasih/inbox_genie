import pytest
from app.email_client import condense_email, fetch_emails
from unittest.mock import patch, MagicMock

def test_condense_email_minimal():
    email = {
        "id": "abc",
        "subject": "Test",
        "from": {"emailAddress": {"name": "A", "address": "a@b.com"}},
        "bodyPreview": "Hello world"
    }
    result = condense_email(email)
    assert result["id"] == "abc"
    assert result["subject"] == "Test"
    assert result["snippet"] == "Hello world"
    assert result["sender"]["email"] == "a@b.com"
    assert result["sender"]["name"] == "A"

def test_condense_email_handles_missing_fields():
    # Missing sender email/name
    email = {"id": "id1", "subject": "S", "from": {"emailAddress": {}}, "bodyPreview": "hi"}
    result = condense_email(email)
    assert result["sender"]["email"] == ""
    assert result["sender"]["name"] == ""

@patch("app.email_client.requests.get")
def test_fetch_emails_graph_api(mock_get):
    # Simulate Graph API response
    mock_get.return_value = MagicMock(status_code=200, json=lambda: {"value": [{"id": "id1", "subject": "S", "from": {"emailAddress": {"name": "A", "address": "a@b.com"}}, "bodyPreview": "hi"}]})
    emails = fetch_emails("fake-token")
    assert isinstance(emails, list)
    assert emails[0]["id"] == "id1"

def test_fetch_emails_graph_api_error():
    with pytest.raises(Exception):
        fetch_emails("fake-token", raise_on_error=True)
