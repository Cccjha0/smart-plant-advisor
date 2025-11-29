from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import ImageRecord, SensorRecord
from services.growth_service import GrowthService

router = APIRouter()

growth_service = GrowthService()


@router.get("/analysis/{plant_id}")
def get_analysis(plant_id: int, db: Session = Depends(get_db)):
    latest_image: Optional[ImageRecord] = (
        db.query(ImageRecord)
        .filter(ImageRecord.plant_id == plant_id)
        .order_by(ImageRecord.captured_at.desc())
        .first()
    )

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

    return {
        "plant_id": plant_id,
        "growth_status": growth_result.get("growth_status"),
        "growth_rate_3d": growth_result.get("growth_rate_3d"),
        "sensor_summary_7d": sensor_summary_7d,
        "stress_factors": growth_result.get("stress_factors", []),
    }
