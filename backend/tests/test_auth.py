import pytest
from app.auth import store_token, get_token
from app.db import get_session
from datetime import datetime

def test_store_and_get_token():
    session = get_session()
    user_email = "testuser@example.com"
    access_token = "tok"
    refresh_token = "rtok"
    expires_at = datetime.utcnow()
    # Store
    store_token(session, user_email, access_token, refresh_token, expires_at)
    # Get
    token = get_token(session, user_email)
    assert token is not None
    assert token.user_email == user_email
    assert token.access_token == access_token
    # Cleanup
    session.delete(token)
    session.commit()
    session.close()

def test_store_token_overwrites():
    session = get_session()
    user_email = "overwrite@example.com"
    # Store first token
    store_token(session, user_email, "tok1", "rtok1", datetime.utcnow())
    # Store again (should overwrite)
    store_token(session, user_email, "tok2", "rtok2", datetime.utcnow())
    token = get_token(session, user_email)
    assert token.access_token == "tok2"
    assert token.refresh_token == "rtok2"
    assert token.expires_at is not None
    session.delete(token)
    session.commit()
    session.close()

def test_get_token_not_found():
    session = get_session()
    token = get_token(session, "notfound@example.com")
    assert token is None
    session.close()
