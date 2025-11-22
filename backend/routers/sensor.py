from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models import SensorRecord, Plant

router = APIRouter()


class SensorCreate(BaseModel):
    plant_id: int
    temperature: Optional[float] = None
    light: Optional[float] = None
    soil_moisture: Optional[float] = None
    timestamp: Optional[datetime] = None


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
