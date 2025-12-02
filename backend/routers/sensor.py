from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models import SensorRecord, WeightRecord, Plant

router = APIRouter()


class SensorCreate(BaseModel):
    plant_id: int
    temperature: Optional[float] = None
    light: Optional[float] = None
    soil_moisture: Optional[float] = None
    timestamp: Optional[datetime] = None


class WeightCreate(BaseModel):
    plant_id: int
    weight: float
    timestamp: Optional[datetime] = None


def _validate_limit(limit: int) -> int:
    return max(1, min(limit, 100))


@router.post("/sensor")
def create_sensor_record(payload: SensorCreate, db: Session = Depends(get_db)):
    plant = db.query(Plant).filter(Plant.id == payload.plant_id).first()
    if not plant:
        raise HTTPException(status_code=400, detail=f"Plant {payload.plant_id} does not exist.")

    ts = payload.timestamp or datetime.utcnow()

    # previous soil moisture for watering detection
    prev_soil_row = (
        db.query(SensorRecord.soil_moisture, SensorRecord.timestamp)
        .filter(SensorRecord.plant_id == payload.plant_id, SensorRecord.soil_moisture.isnot(None))
        .order_by(SensorRecord.timestamp.desc())
        .first()
    )

    record = SensorRecord(
        plant_id=payload.plant_id,
        temperature=payload.temperature,
        light=payload.light,
        soil_moisture=payload.soil_moisture,
        timestamp=ts,
    )

    db.add(record)
    db.flush()

    # Simple watering detection: soil moisture raw drops significantly (0=wet, 255=dry)
    # If current soil_moisture is provided and previous exists, detect large negative delta
    WATER_SOIL_DELTA = -20.0  # raw drop threshold (>=20 point wetter)
    watered = False
    if payload.soil_moisture is not None and prev_soil_row:
        prev_val, prev_ts = prev_soil_row
        if prev_val is not None:
            delta = payload.soil_moisture - prev_val
            if delta <= WATER_SOIL_DELTA:
                plant.last_watered_at = ts
                watered = True

    db.commit()
    db.refresh(record)

    return {
        "status": "ok",
        "record_id": record.id,
        "timestamp": record.timestamp,
        "watering_detected": watered,
    }


@router.post("/weight")
def create_weight_record(payload: WeightCreate, db: Session = Depends(get_db)):
    plant = db.query(Plant).filter(Plant.id == payload.plant_id).first()
    if not plant:
        raise HTTPException(status_code=400, detail=f"Plant {payload.plant_id} does not exist.")

    ts = payload.timestamp or datetime.utcnow()

    prev_weight_row = (
        db.query(WeightRecord.weight, WeightRecord.timestamp)
        .filter(WeightRecord.plant_id == payload.plant_id, WeightRecord.weight.isnot(None))
        .order_by(WeightRecord.timestamp.desc())
        .first()
    )

    record = WeightRecord(
        plant_id=payload.plant_id,
        weight=payload.weight,
        timestamp=ts,
    )

    db.add(record)
    db.flush()

    # Watering detection via weight jump
    WATER_WEIGHT_DELTA = 30.0  # grams
    watered = False
    if prev_weight_row:
        prev_w, _prev_ts = prev_weight_row
        if prev_w is not None:
            delta_w = payload.weight - prev_w
            if delta_w >= WATER_WEIGHT_DELTA:
                plant.last_watered_at = ts
                watered = True

    db.commit()
    db.refresh(record)

    return {"status": "ok", "id": record.id, "timestamp": record.timestamp, "watering_detected": watered}


def _soil_to_pct(raw: float | None) -> float | None:
    if raw is None:
        return None
    pct = (255.0 - raw) / 255.0 * 100.0
    return round(max(0.0, min(100.0, pct)), 2)


@router.get("/sensor/recent/soil")
def recent_soil_moisture(plant_id: int, limit: int = 10, db: Session = Depends(get_db)):
    limit = _validate_limit(limit)
    rows = (
        db.query(SensorRecord.soil_moisture, SensorRecord.timestamp)
        .filter(SensorRecord.plant_id == plant_id)
        .order_by(SensorRecord.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "soil_moisture_raw": r[0],
            "soil_moisture_pct": _soil_to_pct(r[0]),
            "timestamp": r[1],
        }
        for r in rows
    ]


@router.get("/sensor/recent/temperature")
def recent_temperature(plant_id: int, limit: int = 10, db: Session = Depends(get_db)):
    limit = _validate_limit(limit)
    rows = (
        db.query(SensorRecord.temperature, SensorRecord.timestamp)
        .filter(SensorRecord.plant_id == plant_id)
        .order_by(SensorRecord.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [{"temperature": r[0], "timestamp": r[1]} for r in rows]


@router.get("/sensor/recent/light")
def recent_light(plant_id: int, limit: int = 10, db: Session = Depends(get_db)):
    limit = _validate_limit(limit)
    rows = (
        db.query(SensorRecord.light, SensorRecord.timestamp)
        .filter(SensorRecord.plant_id == plant_id)
        .order_by(SensorRecord.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [{"light": r[0], "timestamp": r[1]} for r in rows]


@router.get("/weight/recent")
def recent_weight(plant_id: int, limit: int = 10, db: Session = Depends(get_db)):
    limit = _validate_limit(limit)
    rows = (
        db.query(WeightRecord.weight, WeightRecord.timestamp)
        .filter(WeightRecord.plant_id == plant_id)
        .order_by(WeightRecord.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [{"weight": r[0], "timestamp": r[1]} for r in rows]
