from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from database import Base


class ImageRecord(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id"), nullable=False)
    file_path = Column(String, nullable=False)
    captured_at = Column(DateTime, default=datetime.utcnow)

    plant_type = Column(String, nullable=True)
    leaf_health = Column(String, nullable=True)
    symptoms = Column(JSON, nullable=True)

    plant = relationship("Plant", back_populates="images")
