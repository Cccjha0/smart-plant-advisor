from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from database import get_db
from models import DreamImageRecord, Plant
from services.llm_service import LLMService

router = APIRouter()

llm_service = LLMService()


class DreamCreate(BaseModel):
    plant_id: int
    temperature: Optional[float] = None
    light: Optional[float] = None
    soil_moisture: Optional[float] = None
    health_status: Optional[str] = None


class DreamOut(BaseModel):
    id: int
    plant_id: int
    file_path: str
    prompt: Optional[str]
    metadata: Optional[dict]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.post("/dreams", response_model=DreamOut)
def create_dream_image(payload: DreamCreate, db: Session = Depends(get_db)):
    plant = db.query(Plant).filter(Plant.id == payload.plant_id).first()
    if not plant:
        raise HTTPException(status_code=400, detail=f"Plant {payload.plant_id} does not exist.")

    sensor_payload = {
        "temperature": payload.temperature,
        "light": payload.light,
        "soil_moisture": payload.soil_moisture,
        "health_status": payload.health_status,
    }

    dream_result = llm_service.generate_dream_image(payload.plant_id, sensor_payload)

    record = DreamImageRecord(
        plant_id=payload.plant_id,
        file_path=dream_result["file_path"],
        prompt=dream_result.get("prompt"),
        metadata=sensor_payload,
        created_at=datetime.utcnow(),
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@router.get("/dreams/{plant_id}", response_model=list[DreamOut])
def list_dream_images(plant_id: int, db: Session = Depends(get_db)):
    records = (
        db.query(DreamImageRecord)
        .filter(DreamImageRecord.plant_id == plant_id)
        .order_by(DreamImageRecord.created_at.desc())
        .all()
    )
    return records
