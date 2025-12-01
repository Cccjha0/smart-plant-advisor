from datetime import datetime, timedelta
from typing import Optional
import json
import logging

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import ImageRecord, SensorRecord, AnalysisResult, Plant, Alert, DreamImageRecord, WeightRecord
from services.growth_service import GrowthService
from services.llm_service import LLMService

router = APIRouter()

growth_service = GrowthService()
llm_service = LLMService()
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


@router.get("/report/{plant_id}")
def generate_report(plant_id: int, db: Session = Depends(get_db)):
    logger.info("[report] start generate_report plant_id=%s", plant_id)
    latest_image: Optional[ImageRecord] = (
        db.query(ImageRecord)
        .filter(ImageRecord.plant_id == plant_id)
        .order_by(ImageRecord.captured_at.desc())
        .first()
    )
    plant: Optional[Plant] = db.query(Plant).filter(Plant.id == plant_id).first()

    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    now = datetime.utcnow()

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

    # Aggregations for last 24h and 6h/1h
    since_24h = now - timedelta(hours=24)
    since_6h = now - timedelta(hours=6)
    since_1h = now - timedelta(hours=1)
    today_start = datetime.combine(now.date(), datetime.min.time())

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

    growth_result = growth_service.analyze(plant_id, db)

    # 基础分析结果（用于返回和存库）
    analysis_payload = {
        "growth_status": growth_result.get("growth_status"),
        "growth_rate_3d": growth_result.get("growth_rate_3d"),
        "sensor_summary_7d": sensor_summary_7d,
    }

    # 给 LLM 的输入（不包含 sensor_summary_7d），部分字段转字符串以匹配工作流要求
    growth_status_val = str(growth_result.get("growth_status") or "normal_growth")
    growth_rate_val = growth_result.get("growth_rate_3d")
    growth_rate_str = "0" if growth_rate_val is None else str(growth_rate_val)
    plant_id_str = str(plant_id)
    image_url_val = latest_image.file_path if latest_image else "https://example.com/placeholder.png"

    llm_input = {
        "growth_status": growth_status_val,
        "growth_rate_3d": growth_rate_str,
        "plant_id": plant_id_str,
        "nickname": plant.nickname if plant else "",
        "image_url": image_url_val,
        "metrics_snapshot": metrics_snapshot,
        "sensor_data": sensor_data_payload,
        "stress_factors": growth_result.get("stress_factors") or {
            "humidity_pressure": 0,
            "light_pressure": 0,
            "soil_dry_pressure": 0,
            "temperature_pressure": 0,
        },
    }
    logger.info("[report] llm_input keys=%s", list(llm_input.keys()))

    llm_output = llm_service.generate(llm_input)

    # Merge analysis_json if workflow returns it
    merged_output = {}
    merged_output.update(llm_output or {})
    analysis_json_raw = merged_output.get("analysis_json")
    if analysis_json_raw:
        try:
            parsed = json.loads(analysis_json_raw)
            if isinstance(parsed, dict):
                merged_output.update(parsed)
        except Exception:
            pass

    plant_type = merged_output.get("plant_type")
    if (plant_type is None or plant_type == "" or plant_type == "unknown") and plant.species:
        plant_type = plant.species
    alert_msg = merged_output.get("alert")
    growth_overview = merged_output.get("growth_overview")
    environment_assessment = merged_output.get("environment_assessment")
    suggestions_val = merged_output.get("suggestions")
    if isinstance(suggestions_val, list):
        suggestions_val = "\n".join([str(s) for s in suggestions_val])
    full_analysis = merged_output.get("full_analysis")
    logger.info(
        "[report] llm_output parsed plant_type=%s alert=%s growth_overview=%s",
        plant_type,
        bool(alert_msg),
        bool(growth_overview),
    )

    result = AnalysisResult(
        plant_id=plant_id,
        growth_status=analysis_payload["growth_status"],
        growth_rate_3d=analysis_payload["growth_rate_3d"],
        plant_type=plant_type,
        growth_overview=growth_overview,
        environment_assessment=environment_assessment,
        suggestions=suggestions_val,
        full_analysis=full_analysis,
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


@router.get("/reports/{plant_id}")
def list_reports(plant_id: int, limit: int = 20, db: Session = Depends(get_db)):
    """List recent analysis reports for a plant."""
    limit = max(1, min(limit, 100))
    rows = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.plant_id == plant_id)
        .order_by(AnalysisResult.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "growth_overview": r.growth_overview,
            "environment_assessment": r.environment_assessment,
            "suggestions": r.suggestions,
            "full_analysis": r.full_analysis,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
