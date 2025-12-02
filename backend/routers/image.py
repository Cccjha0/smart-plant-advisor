from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from config import SUPABASE_PLANT_BUCKET
from database import get_db
from models import ImageRecord
from services.storage import upload_bytes

router = APIRouter()


@router.post("/upload_image")
async def upload_image(
    plant_id: int = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="empty file")

    ts = int(datetime.utcnow().timestamp())
    ext = Path(image.filename).suffix or ".jpg"
    storage_path = f"{plant_id}/{ts}{ext}"

    try:
        public_url = upload_bytes(
            SUPABASE_PLANT_BUCKET, storage_path, contents, image.content_type or "image/jpeg"
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"upload failed: {exc}") from exc

    record = ImageRecord(
        plant_id=plant_id,
        file_path=public_url,
        captured_at=datetime.utcnow(),
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "status": "ok",
        "plant_id": plant_id,
        "image_id": record.id,
        "file_path": public_url,
    }
