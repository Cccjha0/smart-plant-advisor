from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import ImageRecord, SensorRecord, AnalysisResult
from services.growth_service import GrowthService
from services.llm_service import LLMService

router = APIRouter()

growth_service = GrowthService()
llm_service = LLMService()


@router.get("/report/{plant_id}")
def generate_report(plant_id: int, db: Session = Depends(get_db)):
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

    analysis_payload = {
        "growth_status": growth_result.get("growth_status"),
        "growth_rate_3d": growth_result.get("growth_rate_3d"),
        "sensor_summary_7d": sensor_summary_7d,
        "stress_factors": growth_result.get("stress_factors", []),
    }

    llm_output = llm_service.generate(analysis_payload)

    result = AnalysisResult(
        plant_id=plant_id,
        growth_status=analysis_payload["growth_status"],
        growth_rate_3d=analysis_payload["growth_rate_3d"],
        stress_factors=analysis_payload["stress_factors"],
        llm_report_short=llm_output.get("short_report"),
        llm_report_long=llm_output.get("long_report"),
        created_at=datetime.utcnow(),
    )

    db.add(result)
    db.commit()
    db.refresh(result)

    return {
        "plant_id": plant_id,
        "analysis": analysis_payload,
        "report": {
            "short": result.llm_report_short,
            "long": result.llm_report_long,
        },
        "analysis_result_id": result.id,
    }
