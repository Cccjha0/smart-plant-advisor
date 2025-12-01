from fastapi import APIRouter, Depends, HTTPException, Query

from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session

from sqlalchemy import func

from pydantic import BaseModel, ConfigDict

from typing import Optional, Dict, Any

from datetime import datetime, timedelta



from database import get_db

from models import Plant, AnalysisResult, SensorRecord, WeightRecord

from external_modules.growth import analyzer as growth_analyzer



router = APIRouter()



def _latest_sensor_value(db: Session, plant_id: int, column):
    row = (
        db.query(column, SensorRecord.timestamp)
        .filter(SensorRecord.plant_id == plant_id, column.isnot(None))
        .order_by(SensorRecord.timestamp.desc())
        .first()
    )
    return (row[0], row[1]) if row else (None, None)


def _latest_weight_value(db: Session, plant_id: int):
    row = (
        db.query(WeightRecord.weight, WeightRecord.timestamp)
        .filter(WeightRecord.plant_id == plant_id, WeightRecord.weight.isnot(None))
        .order_by(WeightRecord.timestamp.desc())
        .first()
    )
    return (row[0], row[1]) if row else (None, None)


def _soil_pct(raw: Optional[float]) -> Optional[float]:
    if raw is None:
        return None
    pct = (255.0 - raw) / 255.0 * 100.0
    return round(max(0.0, min(100.0, pct)), 2)




class PlantCreate(BaseModel):

    nickname: str | None = None





class PlantOut(BaseModel):

    id: int

    nickname: str | None

    species: str | None

    created_at: datetime

    last_watered_at: Optional[datetime] = None



    model_config = ConfigDict(from_attributes=True)





class PlantStatusOut(BaseModel):

    id: int

    nickname: str | None

    species: str | None

    created_at: datetime

    growth_status: str

    last_watered_at: Optional[datetime] = None



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





@router.get("/plants/{plant_id}/latest-summary")
def get_latest_summary(plant_id: int, db: Session = Depends(get_db)):
    """
    Latest sensor snapshot (temperature, light, soil_moisture %, weight) and latest suggestions.
    """
    temp_val, temp_ts = _latest_sensor_value(db, plant_id, SensorRecord.temperature)
    light_val, light_ts = _latest_sensor_value(db, plant_id, SensorRecord.light)
    soil_raw, soil_ts = _latest_sensor_value(db, plant_id, SensorRecord.soil_moisture)
    weight_val, weight_ts = _latest_weight_value(db, plant_id)

    latest_analysis = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.plant_id == plant_id)
        .order_by(AnalysisResult.created_at.desc())
        .first()
    )

    def _entry(value, ts):
        return {"value": value, "timestamp": ts.isoformat() if ts else None}

    return {
        "plant_id": plant_id,
        "sensors": {
            "temperature": _entry(temp_val, temp_ts),
            "light": _entry(light_val, light_ts),
            "soil_moisture": _entry(_soil_pct(soil_raw), soil_ts),
            "weight": _entry(weight_val, weight_ts),
        },
        "suggestions": latest_analysis.suggestions if latest_analysis else None,
    }


@router.get("/plants/{plant_id}/raw-data")

def get_raw_sensor_data(

    plant_id: int,

    sensor_type: str = Query(..., description="temperature|light|soil_moisture|weight"),

    page: int = Query(1, ge=1),

    page_size: int = Query(25, ge=1, le=100),

    db: Session = Depends(get_db),

):

    sensor_map = {

        "temperature": (SensorRecord, SensorRecord.temperature, SensorRecord.timestamp, "Â°C"),

        "light": (SensorRecord, SensorRecord.light, SensorRecord.timestamp, "lux"),

        "soil_moisture": (SensorRecord, SensorRecord.soil_moisture, SensorRecord.timestamp, "raw"),

        "weight": (WeightRecord, WeightRecord.weight, WeightRecord.timestamp, "g"),

    }

    if sensor_type not in sensor_map:

        raise HTTPException(status_code=400, detail="Unsupported sensor_type")



    model_cls, column, ts_col, unit = sensor_map[sensor_type]



    base_q = (

        db.query(column, ts_col)

        .filter(model_cls.plant_id == plant_id, column.isnot(None))

        .order_by(ts_col.desc())

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

    sensor_type: str = Query(..., description="temperature|light|soil_moisture|weight"),

    date: Optional[str] = Query(None, description="ISO date YYYY-MM-DD"),

    start_time: Optional[str] = Query(None, description="ISO datetime start"),

    end_time: Optional[str] = Query(None, description="ISO datetime end"),

    db: Session = Depends(get_db),

):

    sensor_map = {

        "temperature": (SensorRecord, SensorRecord.temperature, SensorRecord.timestamp, "Temperature", "Â°C"),

        "light": (SensorRecord, SensorRecord.light, SensorRecord.timestamp, "Light", "lux"),

        "soil_moisture": (SensorRecord, SensorRecord.soil_moisture, SensorRecord.timestamp, "SoilMoisture", "raw"),

        "weight": (WeightRecord, WeightRecord.weight, WeightRecord.timestamp, "Weight", "g"),

    }

    if sensor_type not in sensor_map:

        raise HTTPException(status_code=400, detail="Unsupported sensor_type")



    model_cls, column, ts_col, label, unit = sensor_map[sensor_type]



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

        db.query(column, ts_col)

        .filter(model_cls.plant_id == plant_id, column.isnot(None))

        .order_by(ts_col.asc())

    )

    if start_dt:

        q = q.filter(ts_col >= start_dt)

    if end_dt:

        q = q.filter(ts_col <= end_dt)



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
    now_dt = datetime.utcnow()
    now_date = now_dt.date()
    start_date = now_date - timedelta(days=days - 1)
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

    try:

        g_norm = growth_analyzer.MIN_NORMAL_GROWTH

        g_slow = growth_analyzer.MIN_SLOW_GROWTH

    except Exception:

        g_norm, g_slow = 0.2, 0.05



    def _rate_to_score(rate: Optional[float]) -> float:

        if rate is None:

            return 5.0

        if rate <= 0:

            return 9.0

        if rate < g_slow:

            return 7.0

        if rate < g_norm:

            return 5.0

        return 1.0



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



    # Stress scores: numeric scores based on 24h averages + growth rate

    analysis = growth_analyzer.analyze_growth(plant_id, db)

    debug = analysis.get("debug") or {}

    sensor_24h = debug.get("sensor_24h") or {}

    avg_temp = sensor_24h.get("avg_temperature")

    avg_light = sensor_24h.get("avg_light")

    avg_soil_norm = sensor_24h.get("avg_soil_moisture")  # normalized 0-1

    growth_rate_3d = analysis.get("growth_rate_3d")



    try:

        ideal_light = growth_analyzer.LIGHT_OPT_MIN

    except Exception:

        ideal_light = 200.0



    try:

        t_low = growth_analyzer.TEMP_OPT_LOW

        t_high = growth_analyzer.TEMP_OPT_HIGH

    except Exception:

        t_low, t_high = 18.0, 30.0



    try:

        s_low = growth_analyzer.SOIL_MOIST_LOW

        s_high = growth_analyzer.SOIL_MOIST_HIGH

    except Exception:

        s_low, s_high = 0.25, 0.75



    # Helper: z-score based stress (|z| scaled to 0-10)

    def _z_score(val: Optional[float], samples: list[float]) -> float:

        if val is None or not samples:

            return 5.0

        mean = sum(samples) / len(samples)

        var = sum((x - mean) ** 2 for x in samples) / max(len(samples), 1)

        std = (var ** 0.5) or 1e-6

        z = abs(val - mean) / std

        return round(min(10.0, z * 2.0), 2)  # z=5 -> 10å?

    # Collect last 7d samples for z-score
    since_7d = datetime.combine(now_date - timedelta(days=6), datetime.min.time())
    temp_samples = [

        t for (t,) in db.query(SensorRecord.temperature).filter(

            SensorRecord.plant_id == plant_id,

            SensorRecord.timestamp >= since_7d,

            SensorRecord.temperature.isnot(None),

        ).all()

    ]

    light_samples = [

        l for (l,) in db.query(SensorRecord.light).filter(

            SensorRecord.plant_id == plant_id,

            SensorRecord.timestamp >= since_7d,

            SensorRecord.light.isnot(None),

        ).all()

    ]

    soil_samples = [

        s for (s,) in db.query(SensorRecord.soil_moisture).filter(

            SensorRecord.plant_id == plant_id,

            SensorRecord.timestamp >= since_7d,

            SensorRecord.soil_moisture.isnot(None),

        ).all()

    ]

    # Normalize soil to 0-1 for scoring

    soil_samples_norm = [(255.0 - s) / 255.0 for s in soil_samples] if soil_samples else []

    avg_soil_norm_for_score = avg_soil_norm  # already normalized 0-1



    light_score = max(0.5, _z_score(avg_light, light_samples))

    temp_score = max(0.5, _z_score(avg_temp, temp_samples))

    soil_score = max(0.5, _z_score(avg_soil_norm_for_score, soil_samples_norm))



    def _score_growth(rate: Optional[float]) -> float:

        if rate is None:

            return 5.0

        try:

            g_norm = growth_analyzer.MIN_NORMAL_GROWTH

            g_slow = growth_analyzer.MIN_SLOW_GROWTH

        except Exception:

            g_norm, g_slow = 0.2, 0.05

        if rate >= g_norm:

            return 0.5

        if rate <= 0:

            return 10.0

        if rate < g_slow:

            return round(6 + (1 - rate / g_slow) * 4, 2)

        return round((1 - (rate - g_slow) / (g_norm - g_slow)) * 5.5 + 0.5, 2)



    growth_score = max(0.5, _score_growth(growth_rate_3d))



    stress_scores = {

        "temperature": round(temp_score, 2),

        "humidity": round(soil_score, 2),

        "light": round(light_score, 2),

        "growth": round(growth_score, 2),

    }



    return {

        "plant_id": plant_id,

        "days": days,

        "start_date": start_date.isoformat(),

        "end_date": now_date.isoformat(),

        "daily_weight": daily_weight,

        "growth_rate_3d": growth_rate_series,

        "stress_scores": stress_scores,

    }





