from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from config import SUPABASE_DREAM_BUCKET
from database import get_db
from models import DreamImageRecord, Plant
from services.llm_service import LLMService
from services.storage import upload_bytes

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
    info: Optional[dict]
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
    dream_bytes = dream_result.get("data")
    ext = dream_result.get("ext", "png")

    if not dream_bytes:
        raise HTTPException(status_code=500, detail="dream image generation failed")

    ts = int(datetime.utcnow().timestamp())
    ext_clean = ext.lstrip(".") or "png"
    storage_path = f"{payload.plant_id}/{ts}.{ext_clean}"

    try:
        public_url = upload_bytes(
            SUPABASE_DREAM_BUCKET,
            storage_path,
            dream_bytes,
            f"image/{ext_clean}",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"upload failed: {exc}") from exc

    record = DreamImageRecord(
        plant_id=payload.plant_id,
        file_path=public_url,
        info=sensor_payload,
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
