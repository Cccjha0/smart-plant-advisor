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

    record = SensorRecord(
        plant_id=payload.plant_id,
        temperature=payload.temperature,
        light=payload.light,
        soil_moisture=payload.soil_moisture,
        timestamp=ts,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "status": "ok",
        "record_id": record.id,
        "timestamp": record.timestamp,
    }


@router.post("/weight")
def create_weight_record(payload: WeightCreate, db: Session = Depends(get_db)):
    plant = db.query(Plant).filter(Plant.id == payload.plant_id).first()
    if not plant:
        raise HTTPException(status_code=400, detail=f"Plant {payload.plant_id} does not exist.")

    ts = payload.timestamp or datetime.utcnow()

    record = WeightRecord(
        plant_id=payload.plant_id,
        weight=payload.weight,
        timestamp=ts,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return {"status": "ok", "id": record.id, "timestamp": record.timestamp}


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
    return [{"soil_moisture": r[0], "timestamp": r[1]} for r in rows]


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
