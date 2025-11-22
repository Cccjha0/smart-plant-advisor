import os
from datetime import datetime

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from database import get_db
from models import ImageRecord
from services.llm_service import LLMService

router = APIRouter()

IMAGE_DIR = "data/images"

os.makedirs(IMAGE_DIR, exist_ok=True)

llm_service = LLMService()


@router.post("/upload_image")
async def upload_image(
    plant_id: int = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    filename = f"{datetime.utcnow().timestamp()}_{image.filename}"
    filepath = os.path.join(IMAGE_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(await image.read())

    cv_result = llm_service.analyze_image(filepath)

    record = ImageRecord(
        plant_id=plant_id,
        file_path=filepath,
        captured_at=datetime.utcnow(),
        plant_type=cv_result.get("plant_type"),
        leaf_health=cv_result.get("leaf_health"),
        symptoms=cv_result.get("symptoms"),
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "status": "ok",
        "plant_id": plant_id,
        "image_id": record.id,
        "plant_type": record.plant_type,
        "leaf_health": record.leaf_health,
        "symptoms": record.symptoms,
        "file_path": filepath
    }
