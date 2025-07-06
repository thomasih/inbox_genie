from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models_token import Base
import os

# Use SQLite for dev, can switch to Postgres/MySQL for prod
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./tokens.db")
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    """Get a new database session."""
    return SessionLocal()

def get_engine():
    """Get the current database engine."""
    return engine

# Ensure tables are created at import time (safe for SQLite, but for production use migrations)
Base.metadata.create_all(bind=engine)
