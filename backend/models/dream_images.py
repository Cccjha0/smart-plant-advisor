from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from database import Base


class DreamImageRecord(Base):
    __tablename__ = "dream_images"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id"), nullable=False)
    file_path = Column(String, nullable=False)
    prompt = Column(String, nullable=True)
    info = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    plant = relationship("Plant", back_populates="dream_images")
