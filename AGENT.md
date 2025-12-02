# AGENT.md — Backend & Cloud Data Platform Agent

## Local development
- Python 3.10+ with venv.
- Install: `pip install -r backend/requirements.txt`.
- Env: copy `backend.env.example` → `backend/.env`; set `DB_URL`, `SUPABASE_URL`, `SUPABASE_KEY`, optional bucket names.
- Run: `cd backend && uvicorn app:app --reload`.
- CORS: enabled for `http://localhost:5173`.

## Cloud (Supabase + Render)
- `DB_URL` points to Supabase Postgres (`config.py` converts `postgres://`).
- Tables auto-created via `Base.metadata.create_all(bind=engine)`.
- Render command: `uvicorn app:app --host 0.0.0.0 --port $PORT`.
- Edge devices should POST to the Render base URL when deployed.

## Core API surface
- Plants: `GET/POST /plants`, `GET /plants/by-nickname/{nickname}`, `GET /plants/by-status`.
- Raw data: `GET /plants/{id}/raw-data`, `GET /plants/{id}/raw-data/export` (CSV).
- Growth analytics: `GET /plants/{id}/growth-analytics`.
- Ingest: `POST /sensor`, `POST /weight` (plant validation required).
- Metrics (soil moisture in %): `GET /metrics/{id}`, `/metrics/{id}/daily-7d`, `/metrics/{id}/hourly-24h`.
- Images: `POST /upload_image` (multipart file → Supabase Storage; stores public URL).
- Analysis/Report: `GET /analysis/{id}`, `GET /report/{id}` (writes AnalysisResult text fields).
- Dreams: `POST /dreams`, `GET /dreams/{plant_id}` (Supabase URLs).
- Alerts: `GET/POST /alerts`, `DELETE /alerts/{id}` (supports `plant_id`, `analysis_result_id`).
- Scheduler: `GET /scheduler/jobs`, `POST /scheduler/jobs/{id}/pause|resume|run-now`, `GET /scheduler/logs`.
- System: `GET /admin/stats`, `GET /system/overview`, `GET /dashboard/system-overview`.

## Supabase Storage
- Buckets: `plant-images` (original), `dream-images` (dream garden). Public URL persisted in DB.
- Suggested object path: `{bucket}/{plant_id}/{timestamp}.jpg`.

## Scheduler (services/scheduler.py)
- Daily analysis (recent data only).
- Every 6h: split LLM report and dream image jobs; startup also triggers one full LLM+dream run.
- Weekly cleanup of sensor/weight older than 30 days.
- Post-watering one-off via `schedule_post_watering_job(plant_id, delay_minutes=60)`.
- Jobs metadata in `scheduler_jobs`; run history in `scheduler_job_runs`; pause/resume/run-now via API.

## Data model deltas
- `AnalysisResult`: `growth_status`, `growth_rate_3d`, `plant_type`, `growth_overview`, `environment_assessment`, `suggestions`, `full_analysis`.
- `DreamImage`: `file_path`, `description`, `created_at`.
- `Alert`: `id`, `plant_id`, `analysis_result_id`, `message`, `created_at`.
- Scheduler tables: `scheduler_jobs`, `scheduler_job_runs`.

## LLM inputs/outputs
- Provide: `image_url`, `plant_id`, `nickname`, `sensor_data` (temp, light lux, soil_moisture %, weight), `growth_status`, `growth_rate_3d`, `stress_factors`, `metrics_snapshot` (from `/metrics/{plant_id}`).
- Expect: `plant_type`, `growth_overview`, `environment_assessment`, `suggestions`, `full_analysis`, `alert`.

## Edge collector notes
- Folder: `edge-collector/`.
- Config: `BASE_URL`, optional `PLANT_NICKNAME` in `config.py`.
- Sends `/sensor`, `/weight`; uploads photo files via multipart to `/upload_image` so backend writes to Supabase.

## PR / commit tips
- Keep secrets out of repo; use env vars.
- Prefer small, focused commits; run tests/checks when available.
