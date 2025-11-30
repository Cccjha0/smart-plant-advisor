from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey

from database import Base


class SchedulerJobRun(Base):
    __tablename__ = "scheduler_job_runs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("scheduler_jobs.id"), nullable=True)
    job_key = Column(String, index=True)
    status = Column(String(20), nullable=False)  # success | warning | failed
    message = Column(Text)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
