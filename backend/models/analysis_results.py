from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from database import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id"), nullable=False)

    growth_status = Column(String, nullable=True)
    growth_rate_3d = Column(Float, nullable=True)
    growth_overview = Column(String, nullable=True)
    environment_assessment = Column(String, nullable=True)
    suggestions = Column(String, nullable=True)
    full_analysis = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    plant = relationship("Plant", back_populates="analysis_results")
