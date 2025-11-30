from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class DreamImageRecord(Base):
    __tablename__ = "dream_images"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id"), nullable=False)
    sensor_record_id = Column(Integer, ForeignKey("sensor_records.id"), nullable=True)
    weight_record_id = Column(Integer, ForeignKey("weight_records.id"), nullable=True)
    file_path = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    plant = relationship("Plant", back_populates="dream_images")
