from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import SensorRecord, WeightRecord

router = APIRouter()

LIGHT_SAMPLE_INTERVAL_MIN = 10.0  # assumed sampling interval for light aggregation
SOIL_SCALE = 255.0  # raw scale: 0 wet, 255 dry


def _iso_utc(ts: Optional[datetime]) -> Optional[str]:
    if ts is None:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    else:
        ts = ts.astimezone(timezone.utc)
    return ts.isoformat()


def _latest_value(db: Session, plant_id: int, column):
    row = (
        db.query(column, SensorRecord.timestamp)
        .filter(SensorRecord.plant_id == plant_id, column.isnot(None))
        .order_by(SensorRecord.timestamp.desc())
        .first()
    )
    return row if row else (None, None)


def _agg_sensor(db: Session, plant_id: int, column, since: datetime, agg_func):
    row = (
        db.query(agg_func(column))
        .filter(SensorRecord.plant_id == plant_id, column.isnot(None), SensorRecord.timestamp >= since)
        .one()
    )
    return row[0]


def _value_at_or_before(db: Session, plant_id: int, column, target: datetime):
    row = (
        db.query(column, SensorRecord.timestamp)
        .filter(SensorRecord.plant_id == plant_id, column.isnot(None), SensorRecord.timestamp <= target)
        .order_by(SensorRecord.timestamp.desc())
        .first()
    )
    return row[0] if row else None


def _latest_weight(db: Session, plant_id: int):
    row = (
        db.query(WeightRecord.weight, WeightRecord.timestamp)
        .filter(WeightRecord.plant_id == plant_id, WeightRecord.weight.isnot(None))
        .order_by(WeightRecord.timestamp.desc())
        .first()
    )
    return row


def _weight_first_in_window(db: Session, plant_id: int, since: datetime):
    row = (
        db.query(WeightRecord.weight, WeightRecord.timestamp)
        .filter(WeightRecord.plant_id == plant_id, WeightRecord.weight.isnot(None), WeightRecord.timestamp >= since)
        .order_by(WeightRecord.timestamp.asc())
        .first()
    )
    return row


def _watering_signature(moist_before: Optional[float], moist_after: Optional[float]) -> bool:
    if moist_before is None or moist_after is None:
        return False
    # Heuristic: moisture drop of -20 or more (raw scale 0 wet, 255 dry)
    return (moist_after - moist_before) <= -20


def _last_watering(db: Session, plant_id: int) -> Optional[datetime]:
    latest = (
        db.query(SensorRecord.soil_moisture, SensorRecord.timestamp)
        .filter(SensorRecord.plant_id == plant_id, SensorRecord.soil_moisture.isnot(None))
        .order_by(SensorRecord.timestamp.desc())
        .limit(50)
        .all()
    )
    if len(latest) < 2:
        return None
    for i in range(len(latest) - 1):
        m_after, t_after = latest[i]
        m_before, t_before = latest[i + 1]
        if _watering_signature(m_before, m_after):
            return t_after
    return None


def _soil_pct(raw: Optional[float]) -> Optional[float]:
    if raw is None:
        return None
    pct = (SOIL_SCALE - raw) / SOIL_SCALE * 100.0
    return round(max(0.0, min(100.0, pct)), 2)


@router.get("/metrics/{plant_id}")
def get_metrics(plant_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    now = datetime.utcnow()
    last_watering_ts = _last_watering(db, plant_id)

    # Temperature
    temp_now, temp_ts = _latest_value(db, plant_id, SensorRecord.temperature)
    temp_6h_avg = _agg_sensor(db, plant_id, SensorRecord.temperature, now - timedelta(hours=6), func.avg)
    temp_24h_min = _agg_sensor(db, plant_id, SensorRecord.temperature, now - timedelta(hours=24), func.min)
    temp_24h_max = _agg_sensor(db, plant_id, SensorRecord.temperature, now - timedelta(hours=24), func.max)

    # Soil moisture (0 wet, 255 dry raw scale)
    soil_now, soil_ts = _latest_value(db, plant_id, SensorRecord.soil_moisture)
    soil_24h_min = _agg_sensor(db, plant_id, SensorRecord.soil_moisture, now - timedelta(hours=24), func.min)
    soil_24h_max = _agg_sensor(db, plant_id, SensorRecord.soil_moisture, now - timedelta(hours=24), func.max)
    soil_24h_before = _value_at_or_before(db, plant_id, SensorRecord.soil_moisture, now - timedelta(hours=24))
    soil_trend = None
    if soil_now is not None and soil_24h_before is not None:
        soil_trend = _soil_pct(soil_now) - _soil_pct(soil_24h_before)

    # Light (lux)
    light_now, light_ts = _latest_value(db, plant_id, SensorRecord.light)
    light_1h_avg = _agg_sensor(db, plant_id, SensorRecord.light, now - timedelta(hours=1), func.avg)
    light_today_sum = None
    today_start = datetime.combine(now.date(), datetime.min.time())
    rows_light = (
        db.query(SensorRecord.light)
        .filter(
            SensorRecord.plant_id == plant_id,
            SensorRecord.light.isnot(None),
            SensorRecord.timestamp >= today_start,
        )
        .all()
    )
    if rows_light:
        # Lux-hours approximation: sum(lux * (interval_minutes/60))
        factor = LIGHT_SAMPLE_INTERVAL_MIN / 60.0
        light_today_sum = sum(v[0] * factor for v in rows_light if v[0] is not None)

    # Weight (grams)
    latest_weight = _latest_weight(db, plant_id)
    weight_now = latest_weight[0] if latest_weight else None
    weight_ts = latest_weight[1] if latest_weight else None
    first_24h = _weight_first_in_window(db, plant_id, now - timedelta(hours=24))
    weight_24h_diff = None
    water_loss_per_hour = None
    if latest_weight and first_24h:
        weight_24h_diff = latest_weight[0] - first_24h[0]
        hours_span = max(1.0, (latest_weight[1] - first_24h[1]).total_seconds() / 3600.0)
        water_loss_per_hour = weight_24h_diff / hours_span

    hours_since_last_watering = None
    weight_drop_since_last_watering = None
    if last_watering_ts and latest_weight:
        hours_since_last_watering = (now - last_watering_ts).total_seconds() / 3600.0
        weight_before = (
            db.query(WeightRecord.weight)
            .filter(WeightRecord.plant_id == plant_id, WeightRecord.timestamp <= last_watering_ts, WeightRecord.weight.isnot(None))
            .order_by(WeightRecord.timestamp.desc())
            .first()
        )
        if weight_before:
            weight_drop_since_last_watering = latest_weight[0] - weight_before[0]
            # Recompute water loss per hour using post-watering window to avoid watering spikes
            hours_span = max(1.0, hours_since_last_watering)
            water_loss_per_hour = weight_drop_since_last_watering / hours_span

    # determine latest sensor timestamp across streams
    ts_candidates = [temp_ts, soil_ts, light_ts, weight_ts]
    latest_ts = max([t for t in ts_candidates if t is not None], default=None)

    metrics = {
        "temperature": {
            "temp_now": temp_now,
            "temp_6h_avg": temp_6h_avg,
            "temp_24h_min": temp_24h_min,
            "temp_24h_max": temp_24h_max,
            "temp_at": _iso_utc(temp_ts),
        },
        "soil_moisture": {
            "soil_now": _soil_pct(soil_now),
            "soil_24h_min": _soil_pct(soil_24h_min),
            "soil_24h_max": _soil_pct(soil_24h_max),
            "soil_24h_trend": soil_trend,
            "soil_at": _iso_utc(soil_ts),
        },
        "light": {
            "light_now": light_now,
            "light_1h_avg": light_1h_avg,
            "light_today_sum": light_today_sum,
            "light_at": _iso_utc(light_ts),
        },
        "weight": {
            "weight_now": weight_now,
            "weight_24h_diff": weight_24h_diff,
            "water_loss_per_hour": water_loss_per_hour,
            "hours_since_last_watering": hours_since_last_watering,
            "weight_drop_since_last_watering": weight_drop_since_last_watering,
            "weight_at": _iso_utc(weight_ts),
        },
        "meta": {
            "last_sensor_timestamp": _iso_utc(latest_ts),
        },
    }
    return metrics


def _iterate_buckets(start: datetime, end: datetime, bucket: timedelta):
    cursor = start
    while cursor < end:
        nxt = cursor + bucket
        yield cursor, nxt
        cursor = nxt


@router.get("/metrics/{plant_id}/daily-7d")
def get_metrics_daily_7d(plant_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Last 7 days daily aggregates (UTC) for weight, soil_moisture, temperature, light.
    """
    end = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    start = end - timedelta(days=7)
    bucket = timedelta(days=1)

    sensor_rows = (
        db.query(
            SensorRecord.timestamp,
            SensorRecord.temperature,
            SensorRecord.light,
            SensorRecord.soil_moisture,
        )
        .filter(
            SensorRecord.plant_id == plant_id,
            SensorRecord.timestamp >= start,
            SensorRecord.timestamp < end,
        )
        .all()
    )
    weight_rows = (
        db.query(WeightRecord.timestamp, WeightRecord.weight)
        .filter(
            WeightRecord.plant_id == plant_id,
            WeightRecord.timestamp >= start,
            WeightRecord.timestamp < end,
            WeightRecord.weight.isnot(None),
        )
        .all()
    )

    def _avg(seq, idx, convert=None):
        vals = [convert(x[idx]) if convert else x[idx] for x in seq if x[idx] is not None]
        vals = [v for v in vals if v is not None]
        return sum(vals) / len(vals) if vals else None

    metrics = []
    for b_start, b_end in _iterate_buckets(start, end, bucket):
        s_filtered = [r for r in sensor_rows if b_start <= r[0] < b_end]
        w_filtered = [r for r in weight_rows if b_start <= r[0] < b_end]
        metrics.append(
            {
                "date": b_start.date().isoformat(),
                "weight": _avg(w_filtered, 1),
                "soil_moisture": _avg(s_filtered, 3, _soil_pct),
                "temperature": _avg(s_filtered, 1),
                "light": _avg(s_filtered, 2),
            }
        )

    return {
        "plant_id": plant_id,
        "granularity": "day",
        "start_date": start.date().isoformat(),
        "end_date": (end - timedelta(days=1)).date().isoformat(),
        "metrics": metrics,
    }


@router.get("/metrics/{plant_id}/hourly-24h")
def get_metrics_hourly_24h(plant_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Last 24h hourly aggregates (UTC) for weight, soil_moisture, temperature, light.
    """
    end = datetime.utcnow().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    start = end - timedelta(hours=24)
    bucket = timedelta(hours=1)

    sensor_rows = (
        db.query(
            SensorRecord.timestamp,
            SensorRecord.temperature,
            SensorRecord.light,
            SensorRecord.soil_moisture,
        )
        .filter(
            SensorRecord.plant_id == plant_id,
            SensorRecord.timestamp >= start,
            SensorRecord.timestamp < end,
        )
        .all()
    )
    weight_rows = (
        db.query(WeightRecord.timestamp, WeightRecord.weight)
        .filter(
            WeightRecord.plant_id == plant_id,
            WeightRecord.timestamp >= start,
            WeightRecord.timestamp < end,
            WeightRecord.weight.isnot(None),
        )
        .all()
    )

    def _avg(seq, idx, convert=None):
        vals = [convert(x[idx]) if convert else x[idx] for x in seq if x[idx] is not None]
        vals = [v for v in vals if v is not None]
        return sum(vals) / len(vals) if vals else None

    metrics = []
    for b_start, b_end in _iterate_buckets(start, end, bucket):
        s_filtered = [r for r in sensor_rows if b_start <= r[0] < b_end]
        w_filtered = [r for r in weight_rows if b_start <= r[0] < b_end]
        metrics.append(
            {
                "hour": b_start.strftime("%Y-%m-%d %H:00"),
                "weight": _avg(w_filtered, 1),
                "soil_moisture": _avg(s_filtered, 3, _soil_pct),
                "temperature": _avg(s_filtered, 1),
                "light": _avg(s_filtered, 2),
            }
        )

    return {
        "plant_id": plant_id,
        "granularity": "hour",
        "start_time": start.isoformat(),
        "end_time": (end - timedelta(hours=1)).isoformat(),
        "metrics": metrics,
    }
