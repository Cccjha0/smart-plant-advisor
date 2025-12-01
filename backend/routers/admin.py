from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import Plant, SensorRecord, WeightRecord, ImageRecord, AnalysisResult, DreamImageRecord

router = APIRouter()


@router.get("/admin/stats")
def get_stats(db: Session = Depends(get_db)):
    total_plants = db.query(func.count(Plant.id)).scalar() or 0
    total_sensor_records = db.query(func.count(SensorRecord.id)).scalar() or 0
    total_weight_records = db.query(func.count(WeightRecord.id)).scalar() or 0
    total_images = db.query(func.count(ImageRecord.id)).scalar() or 0
    total_analysis_results = db.query(func.count(AnalysisResult.id)).scalar() or 0

    first_last = db.query(
        func.min(SensorRecord.timestamp),
        func.max(SensorRecord.timestamp),
    ).one()

    first_ts: Optional[datetime] = first_last[0]
    last_ts: Optional[datetime] = first_last[1]

    return {
        "total_plants": total_plants,
        "total_sensor_records": total_sensor_records,
        "total_weight_records": total_weight_records,
        "total_images": total_images,
        "total_analysis_results": total_analysis_results,
        "sensor_first_timestamp": first_ts.isoformat() if first_ts else None,
        "sensor_last_timestamp": last_ts.isoformat() if last_ts else None,
    }


@router.get("/system/overview")
def system_overview(db: Session = Depends(get_db)):
    return {
        "total_plants": db.query(func.count(Plant.id)).scalar() or 0,
        "total_images": db.query(func.count(ImageRecord.id)).scalar() or 0,
        "total_sensor_records": db.query(func.count(SensorRecord.id)).scalar() or 0,
        "total_analysis_results": db.query(func.count(AnalysisResult.id)).scalar() or 0,
        "total_dream_images": db.query(func.count(DreamImageRecord.id)).scalar() or 0,
    }


@router.get("/dashboard/system-overview")
def dashboard_system_overview(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    today_start = datetime.combine(now.date(), datetime.min.time())

    total_plants = db.query(func.count(Plant.id)).scalar() or 0

    # Active: has sensor OR image in last 24h
    active_sensor = (
        db.query(SensorRecord.plant_id)
        .filter(SensorRecord.timestamp >= last_24h)
        .distinct()
        .subquery()
    )
    active_images = (
        db.query(ImageRecord.plant_id)
        .filter(ImageRecord.captured_at >= last_24h)
        .distinct()
        .subquery()
    )
    active_last_24h = (
        db.query(func.count(func.distinct(func.coalesce(active_sensor.c.plant_id, active_images.c.plant_id))))
        .select_from(active_sensor.join(active_images, active_sensor.c.plant_id == active_images.c.plant_id, isouter=True))
        .scalar()
    ) or 0

    # Abnormal: latest analysis with growth_status == stressed (serious pressure)
    subq = (
        db.query(
            AnalysisResult.plant_id,
            func.max(AnalysisResult.created_at).label("max_ts"),
        )
        .group_by(AnalysisResult.plant_id)
        .subquery()
    )
    abnormal_plants = (
        db.query(func.count(AnalysisResult.plant_id))
        .join(subq, (AnalysisResult.plant_id == subq.c.plant_id) & (AnalysisResult.created_at == subq.c.max_ts))
        .filter(AnalysisResult.growth_status == "stressed")
        .scalar()
    ) or 0

    # Dreams generated today
    dreams_generated_today = (
        db.query(func.count(DreamImageRecord.id))
        .filter(DreamImageRecord.created_at >= today_start)
        .scalar()
    ) or 0

    return {
        "total_plants": total_plants,
        "active_last_24h": active_last_24h,
        "abnormal_plants": abnormal_plants,
        "dreams_generated_today": dreams_generated_today,
    }
