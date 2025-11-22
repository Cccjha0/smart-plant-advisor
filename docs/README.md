# Dev Notes (Backend)

## Setup
- Ensure `python 3.10+`.
- Install deps: `pip install -r backend/requirements.txt` (note: `python-multipart` needed for `/upload_image`).
- Env file: copy `backend.env.example` to `.env` in `backend/` and set `DB_URL` (SQLite fallback or Supabase URL; `config.py` converts `postgres://` ¡ú `postgresql+psycopg2://`).
- Run: `uvicorn app:app --reload` from `backend/` with venv activated.

## Routers
- Plants: `/plants` (create/list)
- Sensor/weight: `/sensor`, `/weight` (requires valid `plant_id`)
- Images: `/upload_image` (LLM vision stub)
- Analysis: `/analysis/{plant_id}`
- Report: `/report/{plant_id}` (creates AnalysisResult with LLM text)
- Dream garden: `/dreams` (create), `/dreams/{plant_id}` (list)
- Admin stats: `/admin/stats`

## Scheduler (apscheduler)
Located at `services/scheduler.py`:
- Daily job: analysis only for plants with data in last 24h.
- Every 6h: analysis + LLM report + dream image for plants with data in last 24h.
- `schedule_post_watering_job(plant_id, delay_minutes=60)`: schedules one-off full pipeline 1h after watering if recent data exists.

> Scheduler is not auto-started in `app.py`; call `start_scheduler()` at app startup if desired.
