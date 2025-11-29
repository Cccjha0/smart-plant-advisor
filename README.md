# Smart Plant Advisor

Backend: FastAPI + SQLAlchemy + APScheduler + Supabase  
Frontend: React (Vite) + Tailwind + shadcn/ui (`frontend-web/`)

## Backend Quickstart
- Python 3.10+; `cd backend && pip install -r requirements.txt`
- Env: copy `backend.env.example` → `backend/.env`, set:
  - `DB_URL` (Supabase Postgres or falls back to SQLite)
  - `SUPABASE_URL`, `SUPABASE_KEY`, optional `SUPABASE_PLANT_BUCKET`, `SUPABASE_DREAM_BUCKET` (defaults: `plant-images`, `dream-images`)
- Run: `cd backend && uvicorn app:app --reload`
- CORS enabled for `http://localhost:5173`.

## Key Endpoints
- Plants: `GET/POST /plants`, `GET /plants/by-nickname/{nickname}`, `GET /plants/by-status`
- Raw data: `GET /plants/{id}/raw-data`, `GET /plants/{id}/raw-data/export` (CSV, paginated)
- Growth analytics: `GET /plants/{id}/growth-analytics` (daily reference weight, growth rates, stress scores)
- Sensor/Weight ingest: `POST /sensor`, `POST /weight`
- Metrics (soil moisture already in %): `GET /metrics/{id}`, `GET /metrics/{id}/daily-7d`, `GET /metrics/{id}/hourly-24h`
- Images: `POST /upload_image` (multipart file → Supabase Storage, stores public URL)
- Analysis/Report: `GET /analysis/{id}`, `GET /report/{id}` (persists AnalysisResult text fields)
- Dreams: `POST /dreams`, `GET /dreams/{plant_id}` (Supabase Storage URLs)
- Alerts: `GET/POST /alerts`, `DELETE /alerts/{id}`
- System stats: `GET /admin/stats`, `GET /system/overview`, `GET /dashboard/system-overview`
- Dashboard data: `GET /metrics/{plant_id}` (live), plus the above analytics and overview endpoints.

## Data Model Highlights
- `AnalysisResult`: `growth_status`, `growth_rate_3d`, `growth_overview`, `environment_assessment`, `suggestions`, `full_analysis` (removed: leaf_health, symptoms, stress_factors, llm_report_*).
- `DreamImage`: `file_path`, `description`, `created_at` (removed: info).
- `Alert`: `id`, `message`, `created_at`.
- Images store Supabase public URLs (no local paths).

## Scheduler (`services/scheduler.py`)
- Daily analysis for plants with data in last 24h.
- Every 6h: analysis + LLM report + dream image (if recent data).
- Post-watering one-off full pipeline (1h delay) when invoked.
- Startup triggers one immediate full pipeline run.

## Supabase Storage
- Buckets: `plant-images` (original photos), `dream-images` (dream garden).
- Naming: `{bucket}/{plant_id}/{timestamp}.jpg` suggested; stored public URL is written to DB.

## LLM Inputs/Outputs (vision + report)
- Provide: `image_url`, `plant_id`, `nickname`, `sensor_data` (temp, light lux, soil_moisture %, weight), `growth_status`, `growth_rate_3d`, `stress_factors`, `metrics_snapshot` (from `/metrics/{plant_id}`).
- Expect: `plant_type`, `growth_overview`, `environment_assessment`, `suggestions`, `full_analysis`, `alert`.

## Frontend
- Location: `frontend-web`; run `npm install` then `npm run dev` (Node >=22.12 recommended).
- Vite + React + Tailwind + shadcn/ui + lucide-react + recharts; routes for dashboard, plants detail, dreams gallery, admin.

## Edge Collector (Pi)
- Location: `edge-collector/`
- Configure `BASE_URL`, `PLANT_NICKNAME` (optional) in `config.py`.
- Sends `/sensor`, `/weight`, uploads photo files via `/upload_image` (multipart) which the backend stores in Supabase.
