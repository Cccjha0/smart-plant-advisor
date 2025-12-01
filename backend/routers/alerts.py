from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from database import get_db
from models import Alert

router = APIRouter()


class AlertCreate(BaseModel):
    message: str
    plant_id: Optional[int] = None
    analysis_result_id: Optional[int] = None


class AlertOut(BaseModel):
    id: int
    plant_id: Optional[int]
    analysis_result_id: Optional[int]
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.post("/alerts", response_model=AlertOut)
def create_alert(payload: AlertCreate, db: Session = Depends(get_db)):
    alert = Alert(
        message=payload.message,
        plant_id=payload.plant_id,
        analysis_result_id=payload.analysis_result_id,
        created_at=datetime.utcnow(),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.get("/alerts", response_model=List[AlertOut])
def list_alerts(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=200),
    plant_id: Optional[int] = Query(None),
    analysis_result_id: Optional[int] = Query(None),
):
    query = db.query(Alert)
    if plant_id is not None:
        query = query.filter(Alert.plant_id == plant_id)
    if analysis_result_id is not None:
        query = query.filter(Alert.analysis_result_id == analysis_result_id)
    alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
    return alerts


@router.delete("/alerts/{alert_id}")
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(alert)
    db.commit()
    return {"status": "ok"}
