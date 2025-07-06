from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)
    user_id = Column(String)
    timestamp = Column(DateTime)
    details = Column(String)  # JSON blob of moves for undo

class EmailActionLog(Base):
    __tablename__ = 'email_action_log'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(String, index=True, nullable=False)
    email_id = Column(String, nullable=False)
    from_folder = Column(String, nullable=False)
    to_folder = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    batch_id = Column(String, index=True, nullable=False)  # For grouping actions per sort
    undone = Column(Boolean, default=False)
