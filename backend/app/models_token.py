from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Token(Base):
    __tablename__ = 'tokens'
    user_email = Column(String, primary_key=True)
    access_token = Column(String)
    refresh_token = Column(String)
    expires_at = Column(DateTime)

    def __repr__(self):
        return f"<Token user_email={self.user_email} access_token={self.access_token} refresh_token={self.refresh_token} expires_at={self.expires_at}>"
