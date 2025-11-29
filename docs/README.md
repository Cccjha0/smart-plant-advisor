# Dev Notes (Backend)

## Setup
- Ensure `python 3.10+`.
- Install deps: `pip install -r backend/requirements.txt` (includes `supabase` client; `python-multipart` is needed for `/upload_image`).
- Env file: copy `backend.env.example` to `.env` in `backend/` and set:
  - `DB_URL` (SQLite fallback or Supabase URL; `config.py` converts `postgres://` to `postgresql+psycopg2://`)
  - `SUPABASE_URL`, `SUPABASE_KEY`, optional `SUPABASE_PLANT_BUCKET`, `SUPABASE_DREAM_BUCKET`
- Run: `uvicorn app:app --reload` from `backend/` with venv activated.

## Routers
- Plants: `/plants` (create/list), `/plants/by-nickname/{nickname}`
- Sensor/weight: `/sensor`, `/weight` (requires valid `plant_id`)
- Images: `/upload_image` (multipart file upload; stored in Supabase Storage, public URL persisted)
- Analysis: `/analysis/{plant_id}`
- Report: `/report/{plant_id}` (creates AnalysisResult with LLM text)
- Dream garden: `/dreams` (create), `/dreams/{plant_id}` (list)
- Metrics: `/metrics/{plant_id}` (recent temp/soil/light/weight, watering heuristic)
- Admin stats: `/admin/stats`

## Scheduler (apscheduler)
Located at `services/scheduler.py`:
- Daily job: analysis only for plants with data in last 24h.
- Every 6h: analysis + LLM report + dream image for plants with data in last 24h (dream image uploaded to Supabase).
- Startup: triggers one immediate full pipeline run.
- `schedule_post_watering_job(plant_id, delay_minutes=60)`: schedules one-off full pipeline 1h after watering if recent data exists.

Scheduler auto-starts in `app.py` and stops cleanly on shutdown.

## Edge Collector (Pi)
- Folder: `edge-collector/`
- Config: set `BASE_URL`, `PLANT_NICKNAME` (optional) in `config.py`.
- Sends sensor + weight to `/sensor` and `/weight`.
- Captures hourly photo and uploads the **file** (multipart) to `/upload_image` so backend stores it in Supabase Storage.

## LLM input/output expectations (vision + report)
- Provide: `image_url`, `plant_id`, `nickname`, `sensor_data` (temp, light lux, soil_moisture %, weight), `growth_status`, `growth_rate_3d`, `stress_factors`, `metrics_snapshot` (from `/metrics/{plant_id}` key fields).
- Expect: `plant_type`, `growth_overview`, `environment_assessment`, `suggestions`, `full_analysis`, `alert`.
