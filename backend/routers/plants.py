from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, ConfigDict

from database import get_db
from models import Plant, AnalysisResult, SensorRecord

router = APIRouter()


class PlantCreate(BaseModel):
    nickname: str | None = None


class PlantOut(BaseModel):
    id: int
    nickname: str | None
    species: str | None

    model_config = ConfigDict(from_attributes=True)


class PlantStatusOut(BaseModel):
    id: int
    nickname: str | None
    species: str | None
    growth_status: str

    model_config = ConfigDict(from_attributes=True)


@router.post("/plants", response_model=PlantOut)
def create_plant(payload: PlantCreate, db: Session = Depends(get_db)):
    plant = Plant(
        nickname=payload.nickname,
        species=None
    )
    db.add(plant)
    db.commit()
    db.refresh(plant)
    return plant


@router.get("/plants", response_model=list[PlantOut])
def list_plants(db: Session = Depends(get_db)):
    plants = db.query(Plant).all()
    return plants


@router.get("/plants/by-nickname/{nickname}", response_model=PlantOut)
def get_plant_by_nickname(nickname: str, db: Session = Depends(get_db)):
    plant = db.query(Plant).filter(Plant.nickname == nickname).first()
    if not plant:
        return None
    return plant


@router.get("/plants/by-status", response_model=list[PlantStatusOut])
def list_plants_by_status(
    status: str = Query(..., description="growth status: normal|slow|stagnant|stressed"),
    db: Session = Depends(get_db),
):
    # latest analysis per plant
    subq = (
        db.query(
            AnalysisResult.plant_id,
            func.max(AnalysisResult.created_at).label("max_ts"),
        )
        .group_by(AnalysisResult.plant_id)
        .subquery()
    )

    rows = (
        db.query(Plant, AnalysisResult.growth_status)
        .join(subq, Plant.id == subq.c.plant_id)
        .join(
            AnalysisResult,
            (AnalysisResult.plant_id == subq.c.plant_id)
            & (AnalysisResult.created_at == subq.c.max_ts),
        )
        .filter(AnalysisResult.growth_status == status)
        .all()
    )

    return [
        PlantStatusOut(
            id=plant.id,
            nickname=plant.nickname,
            species=plant.species,
            growth_status=growth_status,
        )
        for plant, growth_status in rows
    ]


@router.get("/plants/{plant_id}/raw-data")
def get_raw_sensor_data(
    plant_id: int,
    sensor_type: str = Query(..., description="temperature|light|soil_moisture"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    sensor_map = {
        "temperature": (SensorRecord.temperature, "°C"),
        "light": (SensorRecord.light, "lux"),
        "soil_moisture": (SensorRecord.soil_moisture, "raw"),
    }
    if sensor_type not in sensor_map:
        raise HTTPException(status_code=400, detail="Unsupported sensor_type")

    column, unit = sensor_map[sensor_type]

    base_q = (
        db.query(column, SensorRecord.timestamp)
        .filter(SensorRecord.plant_id == plant_id, column.isnot(None))
        .order_by(SensorRecord.timestamp.desc())
    )
    total = base_q.count()
    rows = base_q.offset((page - 1) * page_size).limit(page_size).all()

    records = [
        {
            "timestamp": ts.isoformat(),
            "time_label": ts.strftime("%H:%M"),
            "value": val,
        }
        for val, ts in rows
    ]

    date_label = rows[0][1].date().isoformat() if rows else None

    return {
        "plant_id": plant_id,
        "sensor_type": sensor_type,
        "unit": unit,
        "date": date_label,
        "page": page,
        "page_size": page_size,
        "total": total,
        "records": records,
    }
