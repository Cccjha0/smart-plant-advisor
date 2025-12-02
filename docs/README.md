# Dev Notes (Backend)

## Setup
- Python 3.10+.
- `pip install -r backend/requirements.txt`
- `.env` in `backend/` (copy `backend.env.example`):
  - `DB_URL` (Supabase Postgres; SQLite fallback removed; `config.py` still normalizes `postgres://` → `postgresql+psycopg2://`)
  - `SUPABASE_URL`, `SUPABASE_KEY`, optional `SUPABASE_PLANT_BUCKET`, `SUPABASE_DREAM_BUCKET`
  - Coze Intl: `COZE_API_TOKEN`, `COZE_WORKFLOW_ID`, optional `COZE_API_BASE`, `COZE_BOT_ID`, `COZE_APP_ID`
  - Coze CN Dream: `COZE_API_TOKEN_CN`, `COZE_WORKFLOW_ID_CN`, optional `COZE_API_BASE_CN`
- Run: `cd backend && uvicorn app:app --reload`

## Routers (high level)
- Plants: `/plants` (create/list), `/plants/by-nickname/{nickname}`, `/plants/by-status`
- Raw data: `/plants/{id}/raw-data` (paged), `/plants/{id}/raw-data/export` (CSV)
- Growth analytics: `/plants/{id}/growth-analytics`
- Sensor/weight ingest: `/sensor`, `/weight` (validates plant)
- Images: `/upload_image` (multipart; uploads to Supabase Storage and stores public URL; no vision side-effects)
- Analysis/Report: `/analysis/{id}`, `/report/{id}` (persists AnalysisResult), `/watering-trigger/{id}` (manual LLM + dream with `trigger="watering"`)
- Dream garden: `/dreams` (auto-uses latest sensor/weight/analysis; re-uploads Coze image to Supabase), `/dreams/{plant_id}` (list)
- Metrics: `/metrics/{id}`, `/metrics/{id}/daily-7d`, `/metrics/{id}/hourly-24h` (soil moisture returned as %)
- Alerts: `/alerts` (GET/POST), `/alerts/{id}` (DELETE) — supports `plant_id`, `analysis_result_id`
- Scheduler: `/scheduler/jobs`, `/scheduler/logs`, `/scheduler/jobs/{id}/pause|resume|run-now`
- Admin/System: `/admin/stats`, `/system/overview`, `/dashboard/system-overview`

## Scheduler (apscheduler, `services/scheduler.py`)
- Daily: growth analysis only (recent data required).
- Every 6h: separate jobs for LLM report and dream image (no forced run on startup).
- Weekly: cleanup sensor/weight older than 30 days.
- Manual watering pipeline: call `/watering-trigger/{plant_id}` to run LLM report + dream with `trigger="watering"`.
- Job metadata persisted in `scheduler_jobs`; runs logged in `scheduler_job_runs`; `run_job_now` also logs.

## Supabase Storage
- Buckets: `plant-images` (original photos), `dream-images` (dream garden).
- Stored value in DB is the public URL; Coze dream URLs are downloaded and re-uploaded to Supabase.

## Data model notes
- `AnalysisResult`: `growth_status`, `growth_rate_3d`, `plant_type`, `growth_overview`, `environment_assessment`, `suggestions`, `full_analysis`, `trigger`.
- `DreamImage`: `file_path`, `description`, `created_at`, `sensor_record_id`, `weight_record_id`.
- `Alert`: `id`, `plant_id`, `analysis_result_id`, `message`, `created_at`.
- Scheduler tables: `scheduler_jobs`, `scheduler_job_runs`.

## LLM I/O (report workflow)
- Input: `image_url` (latest), `plant_id`, `nickname`, `sensor_data` (temp, light, soil_moisture raw, weight), `growth_status`, `growth_rate_3d`, `stress_factors`, `metrics_snapshot` (recent stats). Object fields are JSON-serialized strings for Coze.
- Output: `plant_type`, `growth_overview`, `environment_assessment`, `suggestions`, `full_analysis`, `alert`; optional `analysis_json` merged if present.

## Dream workflow (Coze CN)
- Call: `generate_dream_image_cn` with `.env` `COZE_API_TOKEN_CN` / `COZE_WORKFLOW_ID_CN` (optional `COZE_API_BASE_CN`).
- Input (strings): `plant_id`, `temperature`, `light`, `soil_moisture`, `health_status` (uses latest `analysis_results.full_analysis` if available).
- Output: `output` (image string/URL per workflow), `msg`, `describe`; backend downloads URL/base64, re-uploads to Supabase `dream-images`, stores Supabase URL + description, links latest sensor/weight rows.

## Edge Collector (Pi)
- Folder: `edge-collector/`
- Config: set `BASE_URL`, `PLANT_NICKNAME` (optional) in `config.py`.
- Sends sensor + weight to `/sensor` and `/weight`.
- Captures hourly photo and uploads the file via multipart to `/upload_image` (backend uploads to Supabase Storage).
