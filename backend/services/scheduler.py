from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import func

from database import SessionLocal
from config import SUPABASE_DREAM_BUCKET
from models import Plant, SensorRecord, AnalysisResult, WeightRecord, DreamImageRecord
from services.growth_service import GrowthService
from services.llm_service import LLMService
from services.storage import upload_bytes

scheduler = BackgroundScheduler()
growth_service = GrowthService()
llm_service = LLMService()


def _get_last_data_timestamp(db, plant_id: int) -> datetime | None:
    """
    Return the most recent timestamp from sensor_records or weight_records for a given plant.
    If there is no data at all, return None.
    """
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
    """
    Check whether the plant has any sensor or weight data within the last `days` days.
    """
    last_ts = _get_last_data_timestamp(db, plant_id)
    if not last_ts:
        return False
    return last_ts >= datetime.utcnow() - timedelta(days=days)


def _run_single_analysis_and_optionals(
    plant: Plant,
    db,
    include_llm: bool,
    include_dream: bool,
) -> None:
    """
    Core logic to:
    - Aggregate last 7 days of sensor data
    - Run growth analysis
    - Create an AnalysisResult (optionally with LLM text)
    - Optionally create a DreamImage
    """
    plant_id = plant.id
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    # Aggregate 7-day sensor summary
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

    # Growth analysis
    growth_result = growth_service.analyze(plant_id, db)

    # Build payload for potential LLM usage
    analysis_payload = {
        "growth_status": growth_result.get("growth_status"),
        "growth_rate_3d": growth_result.get("growth_rate_3d"),
        "sensor_summary_7d": sensor_summary_7d,
        "stress_factors": growth_result.get("stress_factors", []),
    }

    # Optionally generate LLM text report
    llm_short = None
    llm_long = None
    if include_llm:
        llm_output = llm_service.generate(analysis_payload)
        llm_short = llm_output.get("short_report")
        llm_long = llm_output.get("long_report")

    # Insert AnalysisResult (always)
    analysis_record = AnalysisResult(
        plant_id=plant_id,
        growth_status=analysis_payload["growth_status"],
        growth_rate_3d=analysis_payload["growth_rate_3d"],
        growth_overview=llm_short,
        environment_assessment=None,
        suggestions=None,
        full_analysis=llm_long,
        created_at=datetime.utcnow(),
    )
    db.add(analysis_record)
    db.flush()  # ensure ID is assigned if needed

    # Optionally generate dream garden image
    if include_dream:
        dream_result = llm_service.generate_dream_image(plant_id, analysis_payload)
        dream_bytes = dream_result.get("data")
        ext = dream_result.get("ext", "png")
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

            db.add(
                DreamImageRecord(
                    plant_id=plant_id,
                    file_path=public_url or storage_path,
                    info=analysis_payload,
                    created_at=datetime.utcnow(),
                )
            )


def run_daily_analysis():
    """
    Daily job:
    - For each plant with data in the last 24 hours:
    - Run analysis and store AnalysisResult WITHOUT LLM report or dream image.
    """
    db = SessionLocal()
    try:
        plants = db.query(Plant).all()
        if not plants:
            return

        for plant in plants:
            if not _has_recent_data(db, plant.id, days=1):
                continue

            _run_single_analysis_and_optionals(
                plant=plant,
                db=db,
                include_llm=False,
                include_dream=False,
            )

        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def run_periodic_llm_and_dream():
    """
    6-hour job:
    - For each plant with data in the last 24 hours:
    - Run analysis + LLM report + dream garden image.
    """
    db = SessionLocal()
    try:
        plants = db.query(Plant).all()
        if not plants:
            return

        for plant in plants:
            if not _has_recent_data(db, plant.id, days=1):
                continue

            _run_single_analysis_and_optionals(
                plant=plant,
                db=db,
                include_llm=True,
                include_dream=True,
            )

        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def run_post_watering_job(plant_id: int):
    """
    One-off job scheduled after a watering event.
    Runs the full pipeline (analysis + LLM + dream image) for a single plant,
    but only if it has data in the last 24 hours.
    """
    db = SessionLocal()
    try:
        plant = db.query(Plant).filter(Plant.id == plant_id).first()
        if not plant:
            return

        if not _has_recent_data(db, plant_id, days=1):
            return

        _run_single_analysis_and_optionals(
            plant=plant,
            db=db,
            include_llm=True,
            include_dream=True,
        )

        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def schedule_post_watering_job(plant_id: int, delay_minutes: int = 60):
    """
    Public function to be called when a watering event is detected.
    Schedules a single run of run_post_watering_job(plant_id) delay_minutes later.
    """
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


def start_scheduler():
    """
    Start the background scheduler with:
    - A daily analysis job (once per day)
    - A 6-hour LLM + dream image job
    """
    if not scheduler.get_jobs():
        scheduler.add_job(run_daily_analysis, "cron", hour=2, minute=0)
        scheduler.add_job(run_periodic_llm_and_dream, "cron", hour="0,6,12,18", minute=0)

    scheduler.start()


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
