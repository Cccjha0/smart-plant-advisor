from datetime import datetime

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class SensorRecord(Base):
    __tablename__ = "sensor_records"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id"), nullable=False)

    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    light = Column(Float, nullable=True)
    soil_moisture = Column(Float, nullable=True)

    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    plant = relationship("Plant", back_populates="sensor_records")
