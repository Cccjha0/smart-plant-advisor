# Dev Notes (Backend)

## Setup
- Python 3.10+.
- `pip install -r backend/requirements.txt` (includes Supabase client and `python-multipart`).
- `.env` in `backend/` (copy `backend.env.example`):
  - `DB_URL` (Supabase Postgres URL or falls back to SQLite; `config.py` converts `postgres://` → `postgresql+psycopg2://`)
  - `SUPABASE_URL`, `SUPABASE_KEY`, optional `SUPABASE_PLANT_BUCKET`, `SUPABASE_DREAM_BUCKET`
- Run: `cd backend && uvicorn app:app --reload`

## Routers (high level)
- Plants: `/plants` (create/list), `/plants/by-nickname/{nickname}`, `/plants/by-status`
- Raw data: `/plants/{id}/raw-data` (paged), `/plants/{id}/raw-data/export` (CSV)
- Growth analytics: `/plants/{id}/growth-analytics`
- Sensor/weight ingest: `/sensor`, `/weight` (validates plant)
- Images: `/upload_image` (multipart; uploads to Supabase Storage and stores public URL)
- Analysis/Report: `/analysis/{id}`, `/report/{id}` (persists AnalysisResult text fields)
- Dream garden: `/dreams` (create), `/dreams/{plant_id}` (list)
- Metrics: `/metrics/{id}`, `/metrics/{id}/daily-7d`, `/metrics/{id}/hourly-24h` (soil moisture returned as %)
- Alerts: `/alerts` (GET/POST), `/alerts/{id}` (DELETE)
- Admin/System: `/admin/stats`, `/system/overview`, `/dashboard/system-overview`

## Scheduler (apscheduler, `services/scheduler.py`)
- Daily: growth analysis only (if recent data in last 24h).
- Every 6h: analysis + LLM report + dream image (if recent data).
- Post-watering: one-off full pipeline 1h later via `schedule_post_watering_job(plant_id)`.
- Startup: triggers one immediate full pipeline run.
- Scheduler starts in `app.py` and stops on shutdown.

## Supabase Storage
- Buckets: `plant-images` (original photos), `dream-images` (dream garden).
- Stored value in DB is the public URL; no local file paths are persisted.

## Data model deltas
- `AnalysisResult`: `growth_status`, `growth_rate_3d`, `growth_overview`, `environment_assessment`, `suggestions`, `full_analysis` (removed: leaf_health, symptoms, stress_factors, llm_report_*).
- `DreamImage`: `file_path`, `description`, `created_at` (removed: info).
- `Alert`: `id`, `message`, `created_at`.

## LLM I/O (vision + report)
- Provide: `image_url`, `plant_id`, `nickname`, `sensor_data` (temp, light lux, soil_moisture %, weight), `growth_status`, `growth_rate_3d`, `stress_factors`, `metrics_snapshot` (from `/metrics/{plant_id}` key fields).
- Expect: `plant_type`, `growth_overview`, `environment_assessment`, `suggestions`, `full_analysis`, `alert`.

## Edge Collector (Pi)
- Folder: `edge-collector/`
- Config: set `BASE_URL`, `PLANT_NICKNAME` (optional) in `config.py`.
- Sends sensor + weight to `/sensor` and `/weight`.
- Captures hourly photo and uploads the **file** via multipart to `/upload_image` (backend uploads to Supabase Storage).
