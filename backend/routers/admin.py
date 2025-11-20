from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import Plant, SensorRecord, WeightRecord, ImageRecord, AnalysisResult

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
