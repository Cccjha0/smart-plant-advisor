from datetime import datetime
from typing import Optional

import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from config import SUPABASE_DREAM_BUCKET
from database import get_db
from models import DreamImageRecord, Plant, SensorRecord, WeightRecord, AnalysisResult
from services.llm_service import LLMService
from services.storage import upload_bytes

router = APIRouter()

llm_service = LLMService()


class DreamCreate(BaseModel):
    plant_id: int


class DreamOut(BaseModel):
    id: int
    plant_id: int
    file_path: str
    description: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.post("/dreams", response_model=DreamOut)
def create_dream_image(payload: DreamCreate, db: Session = Depends(get_db)):
    plant = db.query(Plant).filter(Plant.id == payload.plant_id).first()
    if not plant:
        raise HTTPException(status_code=400, detail=f"Plant {payload.plant_id} does not exist.")

    # Gather latest sensor/weight rows and analysis as defaults
    latest_sensor_row = (
        db.query(SensorRecord)
        .filter(SensorRecord.plant_id == payload.plant_id)
        .order_by(SensorRecord.timestamp.desc())
        .first()
    )
    latest_weight_row = (
        db.query(WeightRecord)
        .filter(WeightRecord.plant_id == payload.plant_id, WeightRecord.weight.isnot(None))
        .order_by(WeightRecord.timestamp.desc())
        .first()
    )
    latest_analysis = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.plant_id == payload.plant_id)
        .order_by(AnalysisResult.created_at.desc())
        .first()
    )
    sensor_payload = {
        "temperature": latest_sensor_row.temperature if latest_sensor_row else None,
        "light": latest_sensor_row.light if latest_sensor_row else None,
        "soil_moisture": latest_sensor_row.soil_moisture if latest_sensor_row else None,
        "weight": latest_weight_row.weight if latest_weight_row else None,
        "health_status": latest_analysis.full_analysis if latest_analysis else None,
    }

    dream_result = llm_service.generate_dream_image(payload.plant_id, sensor_payload)
    dream_bytes = dream_result.get("data")
    ext = dream_result.get("ext", "png")
    description = dream_result.get("describe") or dream_result.get("description")
    url = dream_result.get("url")

    if not dream_bytes and not url:
        raise HTTPException(status_code=500, detail="dream image generation failed")

    def _upload_bytes(bytes_data: bytes, ext_hint: str) -> str:
        ts = int(datetime.utcnow().timestamp())
        ext_clean = ext_hint.lstrip(".") or "png"
        storage_path = f"{payload.plant_id}/{ts}.{ext_clean}"
        public_url = upload_bytes(
            SUPABASE_DREAM_BUCKET,
            storage_path,
            bytes_data,
            f"image/{ext_clean}",
        )
        return public_url

    file_path = url
    if dream_bytes:
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
            file_path = public_url
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"upload failed: {exc}") from exc

    elif url:
        # Download Coze URL and re-upload to Supabase
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            content = resp.content
            if not content:
                raise HTTPException(status_code=500, detail="empty image content from Coze URL")
            # guess ext
            ct = resp.headers.get("Content-Type", "")
            ext_guess = "png"
            if "jpeg" in ct:
                ext_guess = "jpg"
            elif "png" in ct:
                ext_guess = "png"
            elif "webp" in ct:
                ext_guess = "webp"
            elif "gif" in ct:
                ext_guess = "gif"
            file_path = _upload_bytes(content, ext_guess)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"download/upload failed: {exc}") from exc

    record = DreamImageRecord(
        plant_id=payload.plant_id,
        sensor_record_id=latest_sensor_row.id if latest_sensor_row else None,
        weight_record_id=latest_weight_row.id if latest_weight_row else None,
        file_path=file_path,
        description=description,
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
