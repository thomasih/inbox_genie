from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models_token import Base
import os

# Use SQLite for dev, can switch to Postgres/MySQL for prod
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./tokens.db")
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables if not exist
Base.metadata.create_all(bind=engine)
