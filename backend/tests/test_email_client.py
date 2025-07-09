import pytest
from app.email_client import condense_email, fetch_emails, get_folder_map, create_folder_if_missing
from unittest.mock import patch, MagicMock
import asyncio

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

def test_get_folder_map_recurses_and_handles_duplicates():
    # Simulate Graph API with subfolders and duplicate names
    def fake_get(url, headers=None):
        if url.endswith('/mailFolders?$top=100'):
            return MagicMock(status_code=200, json=lambda: {"value": [
                {"displayName": "Root", "id": "root", "childFolderCount": 1},
                {"displayName": "Utilities", "id": "util1", "childFolderCount": 0},
            ]})
        elif url.endswith('/mailFolders/root/childFolders?$top=100'):
            return MagicMock(status_code=200, json=lambda: {"value": [
                {"displayName": "Utilities", "id": "util2", "childFolderCount": 0},
            ]})
        else:
            return MagicMock(status_code=200, json=lambda: {"value": []})
    with patch("app.email_client.requests.get", side_effect=fake_get), \
         patch("app.email_client.get_access_token", return_value="fake-token"):
        folder_map = get_folder_map("user@example.com")
        # Should map the first 'Utilities' found
        assert folder_map["Utilities"] in ("util1", "util2")
        assert folder_map["Root"] == "root"

@patch("app.email_client.requests.post")
@patch("app.email_client.get_folder_map")
@patch("app.email_client.get_access_token", return_value="fake-token")
def test_create_folder_if_missing_handles_409(mock_token, mock_get_folder_map, mock_post):
    # Simulate folder not in map, then 409 error, then found after refresh
    folder_name_to_id = {}
    mock_post.return_value = MagicMock(status_code=409)
    mock_get_folder_map.return_value = {"Utilities": "util1"}
    folder_id = create_folder_if_missing("user@example.com", "Utilities", folder_name_to_id)
    assert folder_id == "util1"
    assert folder_name_to_id["Utilities"] == "util1"

@patch("app.email_client.move_email")
@patch("app.email_client.requests.get")
@patch("app.email_client.requests.delete")
@patch("app.email_client.get_access_token", return_value="fake-token")
def test_undo_deletes_empty_folders(mock_token, mock_delete, mock_get, mock_move):
    # Simulate undo logic: folder is empty, delete returns 204
    from app.email_client import undo_last_sort, EmailActionLog, SessionLocal
    class DummyReq: user_email = "user@example.com"
    # Patch DB session and EmailActionLog
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = ("batch1",)
    db.query.return_value.filter.return_value.all.return_value = [
        MagicMock(email_id="eid", from_folder="fid", to_folder="tid", undone=False)
    ]
    mock_move.return_value = {"id": "eid2"}
    def get_side_effect(url, *args, **kwargs):
        if "/mailFolders" in url:
            # Return a folder list with an Inbox
            return MagicMock(status_code=200, json=lambda: {"value": [{"displayName": "Inbox", "id": "inbox_id"}]})
        return MagicMock(status_code=200, json=lambda: {"value": []})
    mock_get.side_effect = get_side_effect
    mock_delete.return_value = MagicMock(status_code=204)
    with patch("app.email_client.SessionLocal", return_value=db):
        # undo_last_sort is async, so run it in event loop
        resp = asyncio.run(undo_last_sort(DummyReq()))
        assert resp.status_code == 200
        assert b"Undo complete" in resp.body
