from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime

from database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
