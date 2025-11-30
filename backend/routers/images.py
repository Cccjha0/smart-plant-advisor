from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from database import get_db
from models import ImageRecord, Plant

router = APIRouter()


class ImageOut(BaseModel):
    id: int
    plant_id: int
    file_path: str
    captured_at: datetime
    plant_type: str | None = None
    leaf_health: str | None = None
    symptoms: dict | None = None

    model_config = ConfigDict(from_attributes=True)


@router.get("/images", response_model=List[ImageOut])
def list_images(
    plant_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    plant = db.query(Plant).filter(Plant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    records = (
        db.query(ImageRecord)
        .filter(ImageRecord.plant_id == plant_id)
        .order_by(ImageRecord.captured_at.desc())
        .limit(limit)
        .all()
    )
    return records
