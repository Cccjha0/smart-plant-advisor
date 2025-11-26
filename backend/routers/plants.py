from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from database import get_db
from models import Plant

router = APIRouter()


class PlantCreate(BaseModel):
    nickname: str | None = None


class PlantOut(BaseModel):
    id: int
    nickname: str | None
    species: str | None

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
