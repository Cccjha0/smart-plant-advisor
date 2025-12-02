from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime

from database import Base


class SchedulerJob(Base):
    __tablename__ = "scheduler_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_key = Column(String, unique=True, index=True)  # internal key, e.g. "daily_analysis"
    name = Column(String)
    description = Column(String)
    cron_expr = Column(String)  # e.g. "0 8 * * *"
    status = Column(String)  # "running" | "paused"
    next_run_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
