from datetime import datetime, timedelta
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import func

from config import SUPABASE_DREAM_BUCKET
from database import SessionLocal
from models import (
    AnalysisResult,
    DreamImageRecord,
    ImageRecord,
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
        "name": "Daily plant analysis",
        "description": "Run growth analysis for all plants at 02:00 every day",
        "cron_expr": "0 2 * * *",
    },
    "periodic_llm_report": {
        "name": "6h LLM text report",
        "description": "Generate an LLM analysis report every 6 hours",
        "cron_expr": "0 */6 * * *",
    },
    "periodic_dream_image": {
        "name": "6h dream image generation",
        "description": "Generate a dream garden image every 6 hours",
        "cron_expr": "0 */6 * * *",
    },
    "weekly_data_cleanup": {
        "name": "Data cleanup task",
        "description": "Clean sensor/weight data older than 30 days every Sunday at 02:00",
        "cron_expr": "0 2 * * 0",
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
    now = datetime.utcnow()
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

    # Latest sensor & weight
    latest_sensor = (
        db.query(SensorRecord)
        .filter(SensorRecord.plant_id == plant_id)
        .order_by(SensorRecord.timestamp.desc())
        .first()
    )
    latest_weight = (
        db.query(WeightRecord)
        .filter(WeightRecord.plant_id == plant_id)
        .order_by(WeightRecord.timestamp.desc())
        .first()
    )
    latest_image = (
        db.query(ImageRecord)
        .filter(ImageRecord.plant_id == plant_id)
        .order_by(ImageRecord.captured_at.desc())
        .first()
    )

    # Aggregations for last 24h and 6h/1h
    since_24h = now - timedelta(hours=24)
    since_6h = now - timedelta(hours=6)
    since_1h = now - timedelta(hours=1)

    agg_24h = (
        db.query(
            func.min(SensorRecord.temperature),
            func.max(SensorRecord.temperature),
            func.avg(SensorRecord.temperature),
            func.min(SensorRecord.soil_moisture),
            func.max(SensorRecord.soil_moisture),
            func.avg(SensorRecord.light),
            func.sum(SensorRecord.light),
        )
        .filter(SensorRecord.plant_id == plant_id, SensorRecord.timestamp >= since_24h)
        .one()
    )
    temp_24h_min, temp_24h_max, temp_24h_avg, soil_24h_min, soil_24h_max, light_24h_avg, light_24h_sum = agg_24h

    temp_6h_avg = (
        db.query(func.avg(SensorRecord.temperature))
        .filter(SensorRecord.plant_id == plant_id, SensorRecord.timestamp >= since_6h)
        .scalar()
    )
    light_1h_avg = (
        db.query(func.avg(SensorRecord.light))
        .filter(SensorRecord.plant_id == plant_id, SensorRecord.timestamp >= since_1h)
        .scalar()
    )

    # Soil trend (24h): compare earliest vs latest in window
    soil_24h_first = (
        db.query(SensorRecord.soil_moisture)
        .filter(SensorRecord.plant_id == plant_id, SensorRecord.timestamp >= since_24h)
        .order_by(SensorRecord.timestamp.asc())
        .first()
    )
    soil_24h_last = (
        db.query(SensorRecord.soil_moisture)
        .filter(SensorRecord.plant_id == plant_id, SensorRecord.timestamp >= since_24h)
        .order_by(SensorRecord.timestamp.desc())
        .first()
    )
    soil_trend = "stable"
    if soil_24h_first and soil_24h_last and soil_24h_first[0] is not None and soil_24h_last[0] is not None:
        diff = soil_24h_last[0] - soil_24h_first[0]
        if diff <= -5:
            soil_trend = "down"
        elif diff >= 5:
            soil_trend = "up"
        else:
            soil_trend = "stable"

    # Weight deltas
    weight_24h_ref = (
        db.query(WeightRecord)
        .filter(WeightRecord.plant_id == plant_id, WeightRecord.timestamp <= since_24h)
        .order_by(WeightRecord.timestamp.desc())
        .first()
    )
    weight_now = latest_weight.weight if latest_weight else None
    weight_24h_diff = None
    water_loss_per_hour = None
    if weight_now is not None and weight_24h_ref and weight_24h_ref.weight is not None:
        weight_24h_diff = weight_now - weight_24h_ref.weight
        hours = max((now - weight_24h_ref.timestamp).total_seconds() / 3600.0, 1e-3)
        water_loss_per_hour = weight_24h_diff / hours

    hours_since_last_watering = None
    weight_drop_since_last_watering = None
    if plant and plant.last_watered_at:
        hours_since_last_watering = round((now - plant.last_watered_at).total_seconds() / 3600.0, 2)
        ref_weight = (
            db.query(WeightRecord)
            .filter(WeightRecord.plant_id == plant_id, WeightRecord.timestamp >= plant.last_watered_at)
            .order_by(WeightRecord.timestamp.asc())
            .first()
        )
        if weight_now is not None and ref_weight and ref_weight.weight is not None:
            weight_drop_since_last_watering = weight_now - ref_weight.weight

    metrics_snapshot = {
        "temperature": {
            "temp_now": latest_sensor.temperature if latest_sensor else 0,
            "temp_6h_avg": temp_6h_avg or 0,
            "temp_24h_min": temp_24h_min or 0,
            "temp_24h_max": temp_24h_max or 0,
        },
        "soil_moisture": {
            "soil_now": latest_sensor.soil_moisture if latest_sensor else 0,
            "soil_24h_min": soil_24h_min or 0,
            "soil_24h_max": soil_24h_max or 0,
            "soil_24h_trend": soil_trend,
        },
        "light": {
            "light_now": latest_sensor.light if latest_sensor else 0,
            "light_1h_avg": light_1h_avg or 0,
            "light_today_sum": light_24h_sum or 0,
        },
        "weight": {
            "weight_now": weight_now if weight_now is not None else 0,
            "weight_24h_diff": weight_24h_diff if weight_24h_diff is not None else 0,
            "water_loss_per_hour": water_loss_per_hour if water_loss_per_hour is not None else 0,
            "hours_since_last_watering": hours_since_last_watering if hours_since_last_watering is not None else 0,
            "weight_drop_since_last_watering": weight_drop_since_last_watering if weight_drop_since_last_watering is not None else 0,
        },
    }

    sensor_data_payload = {
        "temperature": latest_sensor.temperature if latest_sensor else 0,
        "light": latest_sensor.light if latest_sensor else 0,
        "soil_moisture": latest_sensor.soil_moisture if latest_sensor else 0,
        "weight": weight_now if weight_now is not None else 0,
    }

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
        "stress_factors": growth_result.get("stress_factors")
        or {
            "humidity_pressure": 0,
            "light_pressure": 0,
            "soil_dry_pressure": 0,
            "temperature_pressure": 0,
        },
        # Fields expected by LLM workflow (align with manual /report)
        "plant_id": plant_id,
        "nickname": plant.nickname or "",
        "image_url": latest_image.file_path if latest_image else None,
        "metrics_snapshot": metrics_snapshot,
        "sensor_data": sensor_data_payload,
    }

    llm_short = None
    llm_long = None
    plant_type = None
    alert_msg = None
    growth_overview = None
    environment_assessment = None
    suggestions_val = None
    if include_llm:
        llm_output = llm_service.generate(analysis_payload)
        merged_output = {}
        merged_output.update(llm_output or {})
        analysis_json_raw = merged_output.get("analysis_json")
        if analysis_json_raw:
            try:
                import json

                parsed = json.loads(analysis_json_raw)
                if isinstance(parsed, dict):
                    merged_output.update(parsed)
            except Exception:
                pass

        plant_type = merged_output.get("plant_type")
        if (plant_type is None or plant_type == "" or plant_type == "unknown") and plant.species:
            plant_type = plant.species
        alert_msg = merged_output.get("alert")
        growth_overview = merged_output.get("growth_overview") or merged_output.get("short_report")
        environment_assessment = merged_output.get("environment_assessment")
        suggestions_val = merged_output.get("suggestions")
        if isinstance(suggestions_val, list):
            suggestions_val = "\n".join([str(s) for s in suggestions_val])
        llm_short = growth_overview
        llm_long = merged_output.get("full_analysis") or merged_output.get("long_report")

    analysis_record = AnalysisResult(
        plant_id=plant_id,
        growth_status=analysis_payload["growth_status"],
        growth_rate_3d=analysis_payload["growth_rate_3d"],
        plant_type=plant_type,
        trigger=trigger,
        growth_overview=growth_overview,
        environment_assessment=environment_assessment,
        suggestions=suggestions_val,
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
        latest_sensor_row = (
            db.query(SensorRecord)
            .filter(SensorRecord.plant_id == plant_id)
            .order_by(SensorRecord.timestamp.desc())
            .first()
        )
        latest_weight_row = (
            db.query(WeightRecord)
            .filter(WeightRecord.plant_id == plant_id, WeightRecord.weight.isnot(None))
            .order_by(WeightRecord.timestamp.desc())
            .first()
        )
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
                    sensor_record_id=latest_sensor_row.id if latest_sensor_row else None,
                    weight_record_id=latest_weight_row.id if latest_weight_row else None,
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
        started_at = datetime.utcnow()
        try:
            fn()
            _log_job_run(job_key, "success", "manual run completed", started_at, datetime.utcnow())
        except Exception as exc:
            _log_job_run(job_key, "failed", f"manual run error: {exc}", started_at, datetime.utcnow())
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
