from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from database import Base


class Plant(Base):
    __tablename__ = "plants"

    id = Column(Integer, primary_key=True, index=True)
    species = Column(String, nullable=True)
    nickname = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_watered_at = Column(DateTime, nullable=True)

    images = relationship("ImageRecord", back_populates="plant")
    sensor_records = relationship("SensorRecord", back_populates="plant")
    weight_records = relationship("WeightRecord", back_populates="plant")
    analysis_results = relationship("AnalysisResult", back_populates="plant")
    dream_images = relationship("DreamImageRecord", back_populates="plant")
