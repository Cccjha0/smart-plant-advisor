from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, ConfigDict

from database import get_db
from models import Plant, AnalysisResult, SensorRecord
from external_modules.growth import analyzer as growth_analyzer

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


@router.get("/plants/{plant_id}/raw-data/export")
def export_raw_sensor_data(
    plant_id: int,
    sensor_type: str = Query(..., description="temperature|light|soil_moisture"),
    date: Optional[str] = Query(None, description="ISO date YYYY-MM-DD"),
    start_time: Optional[str] = Query(None, description="ISO datetime start"),
    end_time: Optional[str] = Query(None, description="ISO datetime end"),
    db: Session = Depends(get_db),
):
    sensor_map = {
        "temperature": (SensorRecord.temperature, "Temperature", "°C"),
        "light": (SensorRecord.light, "Light", "lux"),
        "soil_moisture": (SensorRecord.soil_moisture, "SoilMoisture", "raw"),
    }
    if sensor_type not in sensor_map:
        raise HTTPException(status_code=400, detail="Unsupported sensor_type")

    column, label, unit = sensor_map[sensor_type]

    # Time range
    if date:
        from datetime import date as date_cls
        try:
            d = date_cls.fromisoformat(date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")
        start_dt = datetime.combine(d, datetime.min.time())
        end_dt = datetime.combine(d, datetime.max.time())
    else:
        try:
            start_dt = datetime.fromisoformat(start_time) if start_time else None
            end_dt = datetime.fromisoformat(end_time) if end_time else None
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid datetime format")

    q = (
        db.query(column, SensorRecord.timestamp)
        .filter(SensorRecord.plant_id == plant_id, column.isnot(None))
        .order_by(SensorRecord.timestamp.asc())
    )
    if start_dt:
        q = q.filter(SensorRecord.timestamp >= start_dt)
    if end_dt:
        q = q.filter(SensorRecord.timestamp <= end_dt)

    rows = q.all()

    def _iter_csv():
        yield "time,sensor_type,value,unit\n"
        for val, ts in rows:
            time_label = ts.strftime("%H:%M")
            yield f"{time_label},{label},{val},{unit}\n"

    return StreamingResponse(_iter_csv(), media_type="text/csv")


@router.get("/plants/{plant_id}/growth-analytics")
def get_growth_analytics(plant_id: int, days: int = 7, db: Session = Depends(get_db)):
    """
    Growth analytics visualization data for last N days (default 7).
    """
    days = max(1, min(days, 14))
    now = datetime.utcnow().date()
    start_date = now - timedelta(days=days - 1)
    ref_points, _ = growth_analyzer._compute_daily_reference_points(plant_id, db, days=days)

    # Daily weights: actual (avg) and reference (from ref_points)
    # Build map date -> reference weight
    ref_map = {p["date"]: p["weight"] for p in ref_points}

    # Actual daily avg weight
    weight_rows = (
        db.query(WeightRecord.timestamp, WeightRecord.weight)
        .filter(
            WeightRecord.plant_id == plant_id,
            WeightRecord.timestamp >= datetime.combine(start_date, datetime.min.time()),
            WeightRecord.weight.isnot(None),
        )
        .order_by(WeightRecord.timestamp.asc())
        .all()
    )
    daily_actual: dict[datetime.date, list[float]] = {}
    for ts, w in weight_rows:
        d = ts.date()
        if d not in daily_actual:
            daily_actual[d] = []
        daily_actual[d].append(w)

    daily_weight = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        actual_vals = daily_actual.get(d, [])
        actual_avg = sum(actual_vals) / len(actual_vals) if actual_vals else None
        daily_weight.append(
            {
                "date": d.isoformat(),
                "actual_weight": actual_avg,
                "reference_weight": ref_map.get(d),
            }
        )

    # Growth rate 3d series: reuse reference points to compute rolling 3-day slope
    growth_rate_series = []
    ref_sorted = sorted(ref_points, key=lambda p: p["date"])
    for idx in range(len(ref_sorted)):
        window = ref_sorted[max(0, idx - 2): idx + 1]
        if len(window) >= 2:
            first = window[0]
            last = window[-1]
            span_days = (last["date"] - first["date"]).days or 1
            rate = (last["weight"] - first["weight"]) / span_days
            growth_rate_series.append(
                {
                    "date": ref_sorted[idx]["date"].isoformat(),
                    "growth_rate_pct": rate,  # grams/day; front-end can scale if needed
                }
            )
        else:
            growth_rate_series.append(
                {
                    "date": ref_sorted[idx]["date"].isoformat(),
                    "growth_rate_pct": None,
                }
            )

    # Stress scores: derive from latest analysis debug (24h averages)
    analysis = growth_analyzer.analyze_growth(plant_id, db)
    stress_factors = set(analysis.get("stress_factors") or [])

    def score_for(name: str) -> float:
        # Simple mapping: present -> 7/10, absent -> 1/10
        return 7.0 if name in stress_factors else 1.0

    stress_scores = {
        "temperature": score_for("temp_out_of_range"),
        "humidity": score_for("humidity"),  # placeholder if humidity stress added
        "light": score_for("low_light"),
        "growth": score_for("growth"),  # placeholder, not in factors; kept for UI slot
    }

    return {
        "plant_id": plant_id,
        "days": days,
        "start_date": start_date.isoformat(),
        "end_date": now.isoformat(),
        "daily_weight": daily_weight,
        "growth_rate_3d": growth_rate_series,
        "stress_scores": stress_scores,
    }
