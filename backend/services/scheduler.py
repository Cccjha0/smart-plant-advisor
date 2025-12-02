from datetime import datetime, timedelta
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import func

from config import SUPABASE_DREAM_BUCKET
from database import SessionLocal
from models import (
    AnalysisResult,
    DreamImageRecord,
    Plant,
    Alert,
    SchedulerJob,
    SchedulerJobRun,
    SensorRecord,
    WeightRecord,
)
from services.growth_service import GrowthService
from services.llm_service import LLMService
from services.storage import upload_bytes

scheduler = BackgroundScheduler()
growth_service = GrowthService()
llm_service = LLMService()

JOB_METADATA = {
    "daily_analysis": {
        "name": "每日植物分析",
        "description": "每天 02:00 对所有植物进行生长分析",
        "cron_expr": "0 2 * * *",
    },
    "periodic_llm_report": {
        "name": "6小时LLM文字报告",
        "description": "每6小时生成一次 LLM 分析报告",
        "cron_expr": "0 */6 * * *",
    },
    "periodic_dream_image": {
        "name": "6小时梦境图生成",
        "description": "每6小时生成一次梦境花园图像",
        "cron_expr": "0 */6 * * *",
    },
    "weekly_data_cleanup": {
        "name": "数据清理任务",
        "description": "每周清理30天前的旧传感器数据",
        "cron_expr": "0 2 * * 0",
    },
    "post_watering": {
        "name": "浇水后一次性任务",
        "description": "浇水后 1 小时运行一次完整管线",
        "cron_expr": None,
    },
}


def _get_last_data_timestamp(db, plant_id: int) -> datetime | None:
    last_sensor_ts = (
        db.query(func.max(SensorRecord.timestamp))
        .filter(SensorRecord.plant_id == plant_id)
        .scalar()
    )
    last_weight_ts = (
        db.query(func.max(WeightRecord.timestamp))
        .filter(WeightRecord.plant_id == plant_id)
        .scalar()
    )
    candidates = [ts for ts in (last_sensor_ts, last_weight_ts) if ts is not None]
    if not candidates:
        return None
    return max(candidates)


def _has_recent_data(db, plant_id: int, days: int = 1) -> bool:
    last_ts = _get_last_data_timestamp(db, plant_id)
    if not last_ts:
        return False
    return last_ts >= datetime.utcnow() - timedelta(days=days)


def _log_job_run(job_key: str, status: str, message: str | None, started_at: datetime, finished_at: datetime | None):
    db = SessionLocal()
    try:
        job_record = db.query(SchedulerJob).filter(SchedulerJob.job_key == job_key).first()
        duration = None
        if finished_at:
            duration = int((finished_at - started_at).total_seconds())
        run = SchedulerJobRun(
            job_id=job_record.id if job_record else None,
            job_key=job_key,
            status=status,
            message=message,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=duration,
        )
        db.add(run)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def _run_single_analysis_and_optionals(
    plant: Plant,
    db,
    include_llm: bool,
    include_dream: bool,
    trigger: str = "default",
) -> None:
    plant_id = plant.id
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    agg = (
        db.query(
            func.avg(SensorRecord.temperature),
            func.avg(SensorRecord.light),
            func.avg(SensorRecord.soil_moisture),
        )
        .filter(
            SensorRecord.plant_id == plant_id,
            SensorRecord.timestamp >= seven_days_ago,
        )
        .one()
    )

    sensor_summary_7d = {
        "avg_temperature": agg[0],
        "avg_light": agg[1],
        "avg_soil_moisture": agg[2],
    }

    growth_result = growth_service.analyze(plant_id, db)

    analysis_payload = {
        "growth_status": growth_result.get("growth_status"),
        "growth_rate_3d": growth_result.get("growth_rate_3d"),
        "sensor_summary_7d": sensor_summary_7d,
        "stress_factors": growth_result.get("stress_factors", []),
    }

    llm_short = None
    llm_long = None
    plant_type = None
    alert_msg = None
    if include_llm:
        llm_output = llm_service.generate(analysis_payload)
        llm_short = llm_output.get("growth_overview") or llm_output.get("short_report")
        llm_long = llm_output.get("full_analysis") or llm_output.get("long_report")
        plant_type = llm_output.get("plant_type")
        if (plant_type is None or plant_type == "" or plant_type == "unknown") and plant.species:
            plant_type = plant.species
        alert_msg = llm_output.get("alert")

    analysis_record = AnalysisResult(
        plant_id=plant_id,
        growth_status=analysis_payload["growth_status"],
        growth_rate_3d=analysis_payload["growth_rate_3d"],
        plant_type=plant_type,
        trigger=trigger,
        growth_overview=llm_short,
        environment_assessment=None,
        suggestions=None,
        full_analysis=llm_long,
        created_at=datetime.utcnow(),
    )
    db.add(analysis_record)
    db.flush()

    # If plant species is empty and LLM provided plant_type, update species
    if plant_type and (plant.species is None or plant.species == ""):
        plant.species = plant_type

    # If alert exists, store it
    if alert_msg:
            db.add(
                Alert(
                    plant_id=plant_id,
                    analysis_result_id=analysis_record.id,
                    message=alert_msg,
                    created_at=datetime.utcnow(),
                )
            )

    if include_dream:
        dream_result = llm_service.generate_dream_image(plant_id, analysis_payload)
        dream_bytes = dream_result.get("data")
        ext = dream_result.get("ext", "png")
        description = dream_result.get("describe") or dream_result.get("description") or None
        url = dream_result.get("url")
        file_path = None
        if dream_bytes:
            ts = int(datetime.utcnow().timestamp())
            ext_clean = ext.lstrip(".") or "png"
            storage_path = f"{plant_id}/{ts}.{ext_clean}"
            try:
                public_url = upload_bytes(
                    SUPABASE_DREAM_BUCKET,
                    storage_path,
                    dream_bytes,
                    f"image/{ext_clean}",
                )
            except Exception:
                public_url = None
            file_path = public_url or storage_path
        elif url:
            # download Coze URL and re-upload to Supabase
            import requests

            try:
                resp = requests.get(url, timeout=10)
                resp.raise_for_status()
                content = resp.content
                if not content:
                    raise Exception("empty image content from Coze URL")
                ct = resp.headers.get("Content-Type", "")
                ext_guess = "png"
                if "jpeg" in ct:
                    ext_guess = "jpg"
                elif "png" in ct:
                    ext_guess = "png"
                elif "webp" in ct:
                    ext_guess = "webp"
                elif "gif" in ct:
                    ext_guess = "gif"
                ts = int(datetime.utcnow().timestamp())
                storage_path = f"{plant_id}/{ts}.{ext_guess}"
                public_url = upload_bytes(
                    SUPABASE_DREAM_BUCKET,
                    storage_path,
                    content,
                    f"image/{ext_guess}",
                )
                file_path = public_url or storage_path
            except Exception:
                # as a last resort, store the Coze URL
                file_path = url

        if file_path:
            db.add(
                DreamImageRecord(
                    plant_id=plant_id,
                    sensor_record_id=None,
                    weight_record_id=None,
                    file_path=file_path,
                    description=description,
                    created_at=datetime.utcnow(),
                )
            )


def _wrap_job(job_key: str, fn: Callable, *args, **kwargs):
    started = datetime.utcnow()
    try:
        fn(*args, **kwargs)
        _log_job_run(job_key, "success", f"{job_key} completed", started, datetime.utcnow())
    except Exception as exc:
        _log_job_run(job_key, "failed", f"Error: {exc}", started, datetime.utcnow())


def run_daily_analysis():
    started_at = datetime.utcnow()
    db = SessionLocal()
    try:
        plants = db.query(Plant).all()
        if not plants:
            _log_job_run("daily_analysis", "warning", "No plants to process", started_at, datetime.utcnow())
            return

        for plant in plants:
            if not _has_recent_data(db, plant.id, days=1):
                continue
            _run_single_analysis_and_optionals(
                plant=plant,
                db=db,
                include_llm=False,
                include_dream=False,
                trigger="scheduled",
            )

        db.commit()
        _log_job_run("daily_analysis", "success", "Daily analysis completed", started_at, datetime.utcnow())
    except Exception as exc:
        db.rollback()
        _log_job_run("daily_analysis", "failed", f"Error: {exc}", started_at, datetime.utcnow())
    finally:
        db.close()


def run_periodic_llm_and_dream():
    started_at = datetime.utcnow()
    db = SessionLocal()
    try:
        plants = db.query(Plant).all()
        if not plants:
            _log_job_run("periodic_llm_and_dream", "warning", "No plants to process", started_at, datetime.utcnow())
            return

        for plant in plants:
            if not _has_recent_data(db, plant.id, days=1):
                continue

            _run_single_analysis_and_optionals(
                plant=plant,
                db=db,
                include_llm=True,
                include_dream=True,
                trigger="scheduled",
            )

        db.commit()
        _log_job_run("periodic_llm_and_dream", "success", "LLM+Dream pipeline completed", started_at, datetime.utcnow())
    except Exception as exc:
        db.rollback()
        _log_job_run("periodic_llm_and_dream", "failed", f"Error: {exc}", started_at, datetime.utcnow())
    finally:
        db.close()


def run_periodic_llm_report():
    started_at = datetime.utcnow()
    db = SessionLocal()
    try:
        plants = db.query(Plant).all()
        if not plants:
            _log_job_run("periodic_llm_report", "warning", "No plants to process", started_at, datetime.utcnow())
            return

        for plant in plants:
            if not _has_recent_data(db, plant.id, days=1):
                continue

            _run_single_analysis_and_optionals(
                plant=plant,
                db=db,
                include_llm=True,
                include_dream=False,
            )

        db.commit()
        _log_job_run("periodic_llm_report", "success", "LLM report job completed", started_at, datetime.utcnow())
    except Exception as exc:
        db.rollback()
        _log_job_run("periodic_llm_report", "failed", f"Error: {exc}", started_at, datetime.utcnow())
    finally:
        db.close()


def run_periodic_dream_image():
    started_at = datetime.utcnow()
    db = SessionLocal()
    try:
        plants = db.query(Plant).all()
        if not plants:
            _log_job_run("periodic_dream_image", "warning", "No plants to process", started_at, datetime.utcnow())
            return

        for plant in plants:
            if not _has_recent_data(db, plant.id, days=1):
                continue

            _run_single_analysis_and_optionals(
                plant=plant,
                db=db,
                include_llm=False,
                include_dream=True,
            )

        db.commit()
        _log_job_run("periodic_dream_image", "success", "Dream image job completed", started_at, datetime.utcnow())
    except Exception as exc:
        db.rollback()
        _log_job_run("periodic_dream_image", "failed", f"Error: {exc}", started_at, datetime.utcnow())
    finally:
        db.close()


def run_weekly_data_cleanup(retention_days: int = 30):
    started_at = datetime.utcnow()
    cutoff = datetime.utcnow() - timedelta(days=retention_days)
    db = SessionLocal()
    try:
        db.query(SensorRecord).filter(SensorRecord.timestamp < cutoff).delete(synchronize_session=False)
        db.query(WeightRecord).filter(WeightRecord.timestamp < cutoff).delete(synchronize_session=False)
        db.commit()
        _log_job_run(
            "weekly_data_cleanup",
            "success",
            f"Cleaned data older than {retention_days} days",
            started_at,
            datetime.utcnow(),
        )
    except Exception as exc:
        db.rollback()
        _log_job_run("weekly_data_cleanup", "failed", f"Error: {exc}", started_at, datetime.utcnow())
    finally:
        db.close()


def run_post_watering_job(plant_id: int):
    started_at = datetime.utcnow()
    db = SessionLocal()
    try:
        plant = db.query(Plant).filter(Plant.id == plant_id).first()
        if not plant:
            _log_job_run("post_watering", "warning", f"Plant {plant_id} not found", started_at, datetime.utcnow())
            return

        if not _has_recent_data(db, plant_id, days=1):
            _log_job_run("post_watering", "warning", f"No recent data for plant {plant_id}", started_at, datetime.utcnow())
            return

        _run_single_analysis_and_optionals(
            plant=plant,
            db=db,
            include_llm=True,
            include_dream=True,
            trigger="watering",
        )

        db.commit()
        _log_job_run("post_watering", "success", f"Post-watering pipeline for plant {plant_id}", started_at, datetime.utcnow())
    except Exception as exc:
        db.rollback()
        _log_job_run("post_watering", "failed", f"Error: {exc}", started_at, datetime.utcnow())
    finally:
        db.close()


def schedule_post_watering_job(plant_id: int, delay_minutes: int = 60):
    run_date = datetime.utcnow() + timedelta(minutes=delay_minutes)
    job_id = f"post_watering_{plant_id}_{int(run_date.timestamp())}"

    scheduler.add_job(
        run_post_watering_job,
        "date",
        run_date=run_date,
        args=[plant_id],
        id=job_id,
        replace_existing=False,
    )
    _sync_jobs_table()


def _sync_jobs_table():
    db = SessionLocal()
    try:
        for job in scheduler.get_jobs():
            meta = JOB_METADATA.get(job.id)
            if not meta:
                continue
            next_run = job.next_run_time
            status = "running" if next_run else "paused"

            record = db.query(SchedulerJob).filter_by(job_key=job.id).first()
            if not record:
                record = SchedulerJob(
                    job_key=job.id,
                    name=meta.get("name"),
                    description=meta.get("description"),
                    cron_expr=meta.get("cron_expr"),
                    status=status,
                    next_run_time=next_run,
                )
                db.add(record)
            else:
                record.name = meta.get("name")
                record.description = meta.get("description")
                record.cron_expr = meta.get("cron_expr")
                record.status = status
                record.next_run_time = next_run
        db.query(SchedulerJob).filter(~SchedulerJob.job_key.in_(JOB_METADATA.keys())).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def get_scheduler_jobs_snapshot():
    _sync_jobs_table()
    db = SessionLocal()
    try:
        return db.query(SchedulerJob).all()
    finally:
        db.close()


def pause_job(job_key: str):
    try:
        scheduler.pause_job(job_key)
    except Exception:
        pass
    _sync_jobs_table()


def resume_job(job_key: str):
    try:
        scheduler.resume_job(job_key)
    except Exception:
        pass
    _sync_jobs_table()


def run_job_now(job_key: str):
    fn_map = {
        "daily_analysis": run_daily_analysis,
        "periodic_llm_report": run_periodic_llm_report,
        "periodic_dream_image": run_periodic_dream_image,
        "weekly_data_cleanup": run_weekly_data_cleanup,
    }
    fn = fn_map.get(job_key)
    if fn:
        try:
            fn()
        except Exception:
            pass
    _sync_jobs_table()


def start_scheduler():
    if not scheduler.get_jobs():
        scheduler.add_job(
            run_daily_analysis, "cron", hour=2, minute=0, id="daily_analysis"
        )
        scheduler.add_job(
            run_periodic_llm_report,
            "cron",
            hour="0,6,12,18",
            minute=0,
            id="periodic_llm_report",
        )
        scheduler.add_job(
            run_periodic_dream_image,
            "cron",
            hour="0,6,12,18",
            minute=0,
            id="periodic_dream_image",
        )
        scheduler.add_job(
            run_weekly_data_cleanup,
            "cron",
            day_of_week="sun",
            hour=2,
            minute=0,
            id="weekly_data_cleanup",
        )

    scheduler.start()
    _sync_jobs_table()


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
