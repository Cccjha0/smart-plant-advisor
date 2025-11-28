from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import SensorRecord, WeightRecord

router = APIRouter()

LIGHT_SAMPLE_INTERVAL_MIN = 10.0  # assumed sampling interval for light aggregation


def _latest_value(db: Session, plant_id: int, column):
    row = (
        db.query(column, SensorRecord.timestamp)
        .filter(SensorRecord.plant_id == plant_id, column.isnot(None))
        .order_by(SensorRecord.timestamp.desc())
        .first()
    )
    return row[0] if row else None


def _agg_sensor(db: Session, plant_id: int, column, since: datetime, agg_func):
    row = (
        db.query(agg_func(column))
        .filter(SensorRecord.plant_id == plant_id, column.isnot(None), SensorRecord.timestamp >= since)
        .one()
    )
    return row[0]


def _value_at_or_before(db: Session, plant_id: int, column, target: datetime):
    row = (
        db.query(column, SensorRecord.timestamp)
        .filter(SensorRecord.plant_id == plant_id, column.isnot(None), SensorRecord.timestamp <= target)
        .order_by(SensorRecord.timestamp.desc())
        .first()
    )
    return row[0] if row else None


def _latest_weight(db: Session, plant_id: int):
    row = (
        db.query(WeightRecord.weight, WeightRecord.timestamp)
        .filter(WeightRecord.plant_id == plant_id, WeightRecord.weight.isnot(None))
        .order_by(WeightRecord.timestamp.desc())
        .first()
    )
    return row


def _weight_first_in_window(db: Session, plant_id: int, since: datetime):
    row = (
        db.query(WeightRecord.weight, WeightRecord.timestamp)
        .filter(WeightRecord.plant_id == plant_id, WeightRecord.weight.isnot(None), WeightRecord.timestamp >= since)
        .order_by(WeightRecord.timestamp.asc())
        .first()
    )
    return row


@router.get("/metrics/{plant_id}")
def get_metrics(plant_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    now = datetime.utcnow()

    # Temperature
    temp_now = _latest_value(db, plant_id, SensorRecord.temperature)
    temp_6h_avg = _agg_sensor(db, plant_id, SensorRecord.temperature, now - timedelta(hours=6), func.avg)
    temp_24h_min = _agg_sensor(db, plant_id, SensorRecord.temperature, now - timedelta(hours=24), func.min)
    temp_24h_max = _agg_sensor(db, plant_id, SensorRecord.temperature, now - timedelta(hours=24), func.max)

    # Soil moisture (0 wet, 255 dry raw scale)
    soil_now = _latest_value(db, plant_id, SensorRecord.soil_moisture)
    soil_24h_min = _agg_sensor(db, plant_id, SensorRecord.soil_moisture, now - timedelta(hours=24), func.min)
    soil_24h_max = _agg_sensor(db, plant_id, SensorRecord.soil_moisture, now - timedelta(hours=24), func.max)
    soil_24h_before = _value_at_or_before(db, plant_id, SensorRecord.soil_moisture, now - timedelta(hours=24))
    soil_trend = None
    if soil_now is not None and soil_24h_before is not None:
        soil_trend = soil_now - soil_24h_before

    # Light (lux)
    light_now = _latest_value(db, plant_id, SensorRecord.light)
    light_1h_avg = _agg_sensor(db, plant_id, SensorRecord.light, now - timedelta(hours=1), func.avg)
    light_today_sum = None
    today_start = datetime.combine(now.date(), datetime.min.time())
    rows_light = (
        db.query(SensorRecord.light)
        .filter(
            SensorRecord.plant_id == plant_id,
            SensorRecord.light.isnot(None),
            SensorRecord.timestamp >= today_start,
        )
        .all()
    )
    if rows_light:
        # Lux-hours approximation: sum(lux * (interval_minutes/60))
        factor = LIGHT_SAMPLE_INTERVAL_MIN / 60.0
        light_today_sum = sum(v[0] * factor for v in rows_light if v[0] is not None)

    # Weight (grams)
    latest_weight = _latest_weight(db, plant_id)
    weight_now = latest_weight[0] if latest_weight else None
    first_24h = _weight_first_in_window(db, plant_id, now - timedelta(hours=24))
    weight_24h_diff = None
    if latest_weight and first_24h:
        weight_24h_diff = latest_weight[0] - first_24h[0]
        hours_span = max(1.0, (latest_weight[1] - first_24h[1]).total_seconds() / 3600.0)
        water_loss_per_hour = weight_24h_diff / hours_span
    else:
        water_loss_per_hour = None

    metrics = {
        "temperature": {
            "temp_now": temp_now,
            "temp_6h_avg": temp_6h_avg,
            "temp_24h_min": temp_24h_min,
            "temp_24h_max": temp_24h_max,
        },
        "soil_moisture": {
            "soil_now": soil_now,
            "soil_24h_min": soil_24h_min,
            "soil_24h_max": soil_24h_max,
            "soil_24h_trend": soil_trend,
        },
        "light": {
            "light_now": light_now,
            "light_1h_avg": light_1h_avg,
            "light_today_sum": light_today_sum,
        },
        "weight": {
            "weight_now": weight_now,
            "weight_24h_diff": weight_24h_diff,
            "water_loss_per_hour": water_loss_per_hour,
            "hours_since_last_watering": None,
            "weight_drop_since_last_watering": None,
        },
    }
    return metrics
