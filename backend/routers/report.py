from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import ImageRecord, SensorRecord, AnalysisResult, Plant, Alert
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
    plant: Optional[Plant] = db.query(Plant).filter(Plant.id == plant_id).first()

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
    }

    llm_output = llm_service.generate(analysis_payload)

    plant_type = llm_output.get("plant_type")
    alert_msg = llm_output.get("alert")

    result = AnalysisResult(
        plant_id=plant_id,
        growth_status=analysis_payload["growth_status"],
        growth_rate_3d=analysis_payload["growth_rate_3d"],
        plant_type=plant_type,
        growth_overview=llm_output.get("growth_overview"),
        environment_assessment=llm_output.get("environment_assessment"),
        suggestions=llm_output.get("suggestions"),
        full_analysis=llm_output.get("full_analysis"),
        created_at=datetime.utcnow(),
    )

    db.add(result)
    db.flush()

    # Update plant species if empty and plant_type is provided
    if plant and plant_type and (plant.species is None or plant.species == ""):
        plant.species = plant_type

    # Write alert if provided
    if alert_msg:
        db.add(
            Alert(
                plant_id=plant_id,
                analysis_result_id=result.id,
                message=alert_msg,
                created_at=datetime.utcnow(),
            )
        )

    db.add(result)
    db.commit()
    db.refresh(result)

    return {
        "plant_id": plant_id,
        "analysis": analysis_payload,
        "report": {
            "growth_overview": result.growth_overview,
            "environment_assessment": result.environment_assessment,
            "suggestions": result.suggestions,
            "full_analysis": result.full_analysis,
        },
        "analysis_result_id": result.id,
    }
