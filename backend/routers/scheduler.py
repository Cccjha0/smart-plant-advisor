from fastapi import APIRouter

from services.scheduler import get_scheduler_jobs_snapshot

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
    return cron_expr


@router.get("/scheduler/jobs")
def list_scheduler_jobs():
    jobs = get_scheduler_jobs_snapshot()
    results = []
    for job in jobs:
        next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M") if job.next_run_time else None
        results.append(
            {
                "id": str(job.id),
                "name": job.name,
                "description": job.description,
                "schedule": _human_readable_schedule(job.cron_expr),
                "status": job.status or "paused",
                "nextRun": next_run,
            }
        )
    return results
