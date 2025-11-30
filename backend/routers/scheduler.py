from fastapi import APIRouter, HTTPException

from database import SessionLocal
from models import SchedulerJob
from services.scheduler import (
    get_scheduler_jobs_snapshot,
    pause_job,
    resume_job,
    run_job_now,
)

router = APIRouter()


def _human_readable_schedule(cron_expr: str | None) -> str:
    if not cron_expr:
        return "未配置"
    parts = cron_expr.split()
    if len(parts) >= 5:
        minute, hour = parts[0], parts[1]
        if hour not in ("*", "*/") and minute.isdigit():
            try:
                return f"每天 {int(hour):02d}:{int(minute):02d}"
            except ValueError:
                pass
        if hour.startswith("*/"):
            try:
                hours = int(hour.replace("*/", ""))
                return f"每{hours}小时"
            except ValueError:
                pass
        if parts[4] == "0" and hour.isdigit() and minute.isdigit():
            # Sunday 02:00 style
            return f"每周日 {int(hour):02d}:{int(minute):02d}"
    return cron_expr


def _build_response(job: SchedulerJob):
    next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M") if job.next_run_time else None
    return {
        "id": str(job.id),
        "name": job.name,
        "description": job.description,
        "schedule": _human_readable_schedule(job.cron_expr),
        "status": job.status or "paused",
        "nextRun": next_run,
    }


@router.get("/scheduler/jobs")
def list_scheduler_jobs():
    jobs = get_scheduler_jobs_snapshot()
    return [_build_response(job) for job in jobs]


def _get_job_or_404(job_id: int) -> SchedulerJob:
    db = SessionLocal()
    try:
        job = db.query(SchedulerJob).filter(SchedulerJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job
    finally:
        db.close()


@router.post("/scheduler/jobs/{job_id}/pause")
def pause_scheduler_job(job_id: int):
    job = _get_job_or_404(job_id)
    pause_job(job.job_key)
    updated = _get_job_or_404(job_id)
    return {"status": "paused", "job": _build_response(updated)}


@router.post("/scheduler/jobs/{job_id}/resume")
def resume_scheduler_job(job_id: int):
    job = _get_job_or_404(job_id)
    resume_job(job.job_key)
    updated = _get_job_or_404(job_id)
    return {"status": "running", "job": _build_response(updated)}


@router.post("/scheduler/jobs/{job_id}/run-now")
def run_scheduler_job_now(job_id: int):
    job = _get_job_or_404(job_id)
    run_job_now(job.job_key)
    updated = _get_job_or_404(job_id)
    return {"status": "triggered", "job": _build_response(updated)}
