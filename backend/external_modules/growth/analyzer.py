from collections import defaultdict
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import SensorRecord, WeightRecord

# Thresholds for growth rate classification (grams per day)
MIN_NORMAL_GROWTH = 0.2   # >= this: normal
MIN_SLOW_GROWTH = 0.05    # 0 < rate < MIN_SLOW_GROWTH -> slow

# Temperature range (°C) considered acceptable
TEMP_OPT_LOW = 18.0
TEMP_OPT_HIGH = 30.0

# Light threshold (arbitrary units, depends on sensor calibration)
LIGHT_OPT_MIN = 200.0

# Soil moisture thresholds (normalized 0–1; sensor gives 0=wet, 255=dry)
SOIL_SCALE = 255.0
SOIL_MOIST_LOW = 0.25
SOIL_MOIST_HIGH = 0.75

# Reference moisture window for fixed humidity reference weight (normalized)
M_REF_LOW = 0.4
M_REF_HIGH = 0.6

# Heuristic thresholds for detecting fertilizer events
FERT_WEIGHT_JUMP_MIN = 10.0      # grams; adjust based on real data
FERT_MOISTURE_DELTA_MAX = 0.05   # |Δsoil_moisture| <= this => moisture considered "unchanged"


def analyze_growth(plant_id: int, db: Session) -> Dict:
    """
    Main entry point used by services and schedulers.

    Returns:
    {
      "growth_status": "normal" | "slow" | "stagnant" | "stressed",
      "growth_rate_3d": float or None,
      "stress_factors": list[str],
      "debug": {...}
    }
    """
    ref_points, fertilizer_events = _compute_daily_reference_points(plant_id, db, days=7)
    growth_rate_3d, delta_weight_1d = _compute_growth_rates(ref_points)

    sensor_24h = _compute_sensor_average(plant_id, db, hours=24)
    sensor_7d = _compute_sensor_average(plant_id, db, days=7)

    stress_factors = _infer_stress_factors(sensor_24h)
    day_count = len(ref_points)
    short_term_mode = day_count < 3

    if short_term_mode:
        growth_status = _classify_short_term_status(delta_weight_1d, stress_factors)
    else:
        growth_status = _classify_growth_status(growth_rate_3d, stress_factors)

    debug_ref_points: List[Dict] = []
    for p in ref_points:
        debug_ref_points.append(
            {
                "date": p["date"].isoformat(),
                "weight": p["weight"],
                "avg_soil_moisture": p.get("avg_soil_moisture"),
                "num_candidates": p.get("num_candidates"),
                "fallback_used": p.get("fallback_used", False),
            }
        )

    debug_fertilizer_events: List[Dict] = []
    for ev in fertilizer_events:
        debug_fertilizer_events.append(
            {
                "timestamp": ev["timestamp"].isoformat(),
                "delta_weight": ev["delta_weight"],
                "delta_moisture": ev["delta_moisture"],
            }
        )

    debug_info = {
        "ref_points": debug_ref_points,
        "delta_weight_1d": delta_weight_1d,
        "sensor_24h": sensor_24h,
        "sensor_7d": sensor_7d,
        "fertilizer_events": debug_fertilizer_events,
    }

    return {
        "growth_status": growth_status,
        "growth_rate_3d": growth_rate_3d,
        "stress_factors": stress_factors,
        "debug": debug_info,
    }


# ------------------------------------------------------------------
# 1) Daily reference weights with fertilizer filtering
# ------------------------------------------------------------------
def _compute_daily_reference_points(
    plant_id: int,
    db: Session,
    days: int = 7,
) -> Tuple[List[Dict], List[Dict]]:
    since = datetime.utcnow() - timedelta(days=days)

    rows = (
        db.query(
            WeightRecord.timestamp,
            WeightRecord.weight,
            SensorRecord.soil_moisture,
        )
        .join(
            SensorRecord,
            (SensorRecord.plant_id == WeightRecord.plant_id)
            & (SensorRecord.timestamp == WeightRecord.timestamp),
        )
        .filter(
            WeightRecord.plant_id == plant_id,
            WeightRecord.timestamp >= since,
        )
        .order_by(WeightRecord.timestamp.asc())
        .all()
    )

    if not rows:
        return [], []

    fertilizer_offset = 0.0
    corrected_samples: List[Tuple[datetime, float, Optional[float]]] = []
    fertilizer_events: List[Dict] = []

    prev_w: Optional[float] = None
    prev_m_norm: Optional[float] = None

    for ts, w, moist_raw in rows:
        moist_norm = None
        if moist_raw is not None:
            moist_norm = max(0.0, min(1.0, moist_raw / SOIL_SCALE))

        if w is None:
            prev_w = w
            prev_m_norm = moist_norm
            continue

        if prev_w is not None:
            delta_w = w - prev_w
            delta_m = 0.0
            if prev_m_norm is not None and moist_norm is not None:
                delta_m = moist_norm - prev_m_norm

            if delta_w >= FERT_WEIGHT_JUMP_MIN and abs(delta_m) <= FERT_MOISTURE_DELTA_MAX:
                fertilizer_offset += delta_w
                fertilizer_events.append(
                    {
                        "timestamp": ts,
                        "delta_weight": float(delta_w),
                        "delta_moisture": float(delta_m),
                    }
                )

        corrected_weight = w - fertilizer_offset
        corrected_samples.append((ts, corrected_weight, moist_norm))

        prev_w = w
        prev_m_norm = moist_norm

    day_candidates: Dict[date, List[Tuple[float, float]]] = defaultdict(list)
    day_all_weights: Dict[date, List[float]] = defaultdict(list)

    for ts, corrected_w, moist_norm in corrected_samples:
        day_key = ts.date()
        day_all_weights[day_key].append(corrected_w)
        if moist_norm is not None and M_REF_LOW <= moist_norm <= M_REF_HIGH:
            day_candidates[day_key].append((corrected_w, moist_norm))

    ref_points: List[Dict] = []

    for day_key in sorted(day_all_weights.keys()):
        candidates = day_candidates.get(day_key, [])
        fallback_used = False

        if candidates:
            total_w = 0.0
            total_m = 0.0
            for w, m in candidates:
                total_w += w
                total_m += m
            avg_w = total_w / len(candidates)
            avg_m = total_m / len(candidates)
            num_candidates = len(candidates)
        else:
            fallback_used = True
            weights = day_all_weights[day_key]
            if not weights:
                continue
            avg_w = sum(weights) / len(weights)
            avg_m = None
            num_candidates = 0

        ref_points.append(
            {
                "date": day_key,
                "weight": avg_w,
                "avg_soil_moisture": avg_m,
                "num_candidates": num_candidates,
                "fallback_used": fallback_used,
            }
        )

    return ref_points, fertilizer_events


def _compute_growth_rates(
    ref_points: List[Dict],
) -> Tuple[Optional[float], Optional[float]]:
    if len(ref_points) < 2:
        return None, None

    ref_points_sorted = sorted(ref_points, key=lambda p: p["date"])
    last = ref_points_sorted[-1]
    prev = ref_points_sorted[-2]
    delta_weight_1d = last["weight"] - prev["weight"]

    subset = ref_points_sorted[-3:] if len(ref_points_sorted) >= 3 else ref_points_sorted
    first = subset[0]
    last = subset[-1]

    days_span = (last["date"] - first["date"]).days
    if days_span < 1:
        days_span = 1

    growth_rate_3d = (last["weight"] - first["weight"]) / days_span

    return growth_rate_3d, delta_weight_1d


def _compute_sensor_average(
    plant_id: int,
    db: Session,
    hours: Optional[int] = None,
    days: Optional[int] = None,
) -> Dict[str, Optional[float]]:
    if hours is None and days is None:
        hours = 24

    since = datetime.utcnow() - timedelta(days=days) if days is not None else datetime.utcnow() - timedelta(hours=hours)

    agg = (
        db.query(
            func.avg(SensorRecord.temperature),
            func.avg(SensorRecord.light),
            func.avg(SensorRecord.soil_moisture),
        )
        .filter(
            SensorRecord.plant_id == plant_id,
            SensorRecord.timestamp >= since,
        )
        .one()
    )

    soil_raw = agg[2]
    soil_norm = None
    if soil_raw is not None:
        soil_norm = max(0.0, min(1.0, soil_raw / SOIL_SCALE))

    return {
        "avg_temperature": agg[0],
        "avg_light": agg[1],
        "avg_soil_moisture": soil_norm,
    }


def _infer_stress_factors(
    sensor_avg: Dict[str, Optional[float]],
) -> List[str]:
    stress_factors: List[str] = []

    avg_temp = sensor_avg.get("avg_temperature")
    avg_light = sensor_avg.get("avg_light")
    avg_soil = sensor_avg.get("avg_soil_moisture")

    if avg_light is not None and avg_light < LIGHT_OPT_MIN:
        stress_factors.append("low_light")

    if avg_soil is not None:
        if avg_soil < SOIL_MOIST_LOW:
            stress_factors.append("soil_too_dry")
        elif avg_soil > SOIL_MOIST_HIGH:
            stress_factors.append("soil_too_wet")

    if avg_temp is not None and (avg_temp < TEMP_OPT_LOW or avg_temp > TEMP_OPT_HIGH):
        stress_factors.append("temp_out_of_range")

    return stress_factors


def _classify_growth_status(
    growth_rate_3d: Optional[float],
    stress_factors: List[str],
) -> str:
    if growth_rate_3d is None:
        return "stressed" if stress_factors else "normal"

    if growth_rate_3d <= 0:
        base_status = "stagnant"
    elif growth_rate_3d < MIN_SLOW_GROWTH:
        base_status = "slow"
    elif growth_rate_3d < MIN_NORMAL_GROWTH:
        base_status = "slow"
    else:
        base_status = "normal"

    if stress_factors and growth_rate_3d <= MIN_SLOW_GROWTH:
        return "stressed"

    return base_status


def _classify_short_term_status(
    delta_weight_1d: Optional[float],
    stress_factors: List[str],
) -> str:
    """
    Demo-friendly short-term classification when data < 3 days.
    - Uses 1-day weight delta and stress.
    - Thresholds are slightly lenient to show state changes.
    """
    if delta_weight_1d is None:
        return "stressed" if stress_factors else "normal"

    if delta_weight_1d <= 0:
        return "stressed" if stress_factors else "stagnant"
    elif delta_weight_1d < 0.05:
        return "stressed" if stress_factors else "slow"
    else:
        return "stressed" if stress_factors else "normal"
