import pytest
from app.db import get_engine, get_session
from app.models_token import Token
from sqlalchemy.orm import sessionmaker
from datetime import datetime

def test_db_token_crud():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    # Create
    token = Token(user_email="test@example.com", access_token="tok", refresh_token="rtok", expires_at=datetime.utcnow())
    session.add(token)
    session.commit()
    # Read
    found = session.query(Token).filter_by(user_email="test@example.com").first()
    assert found is not None
    assert found.access_token == "tok"
    # Update
    found.access_token = "tok2"
    session.commit()
    found2 = session.query(Token).filter_by(user_email="test@example.com").first()
    assert found2.access_token == "tok2"
    # Delete
    session.delete(found2)
    session.commit()
    found3 = session.query(Token).filter_by(user_email="test@example.com").first()
    assert found3 is None
    session.close()
