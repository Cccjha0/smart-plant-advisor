# Smart Plant Advisor

Backend: FastAPI + SQLAlchemy + APScheduler + Supabase Storage  
Frontend: React (Vite) + Tailwind + shadcn/ui (under `frontend-web/`)

## Backend
- Run: `cd backend && uvicorn app:app --reload`
- DB: Supabase Postgres (`DB_URL` in `.env`, converts `postgres://` to `postgresql+psycopg2://`) or local SQLite fallback.
- Storage: Supabase buckets (`SUPABASE_URL`, `SUPABASE_KEY`, optional `SUPABASE_PLANT_BUCKET` / `SUPABASE_DREAM_BUCKET` envs; defaults: `plant-images`, `dream-images`).
- Key endpoints:
  - Plants: `GET/POST /plants`, `GET /plants/by-nickname/{nickname}`
  - Sensor/Weight: `POST /sensor`, `POST /weight`
  - Images: `POST /upload_image` (multipart file; uploads to Supabase Storage, stores public URL)
  - Analysis/Report: `GET /analysis/{id}`, `GET /report/{id}` (writes AnalysisResult)
  - Dreams: `POST /dreams`, `GET /dreams/{plant_id}` (stores dream image in Supabase Storage)
  - Metrics: `GET /metrics/{plant_id}` (recent temp/soil/light/weight, watering heuristic)
  - Admin: `GET /admin/stats`
- Scheduler (`services/scheduler.py`):
  - Daily analysis; every 6h full pipeline (analysis+LLM+dream); post-watering one-off; startup triggers one full run.

## Frontend
- Location: `frontend-web`
- Setup: `npm install` then `npm run dev` (Node >=22.12+ recommended)
- Tech: Vite + React + TS + Tailwind + shadcn/ui + lucide-react + recharts
- Routes:
  - `/dashboard` overview
  - `/plants/:id` detail (tabs)
  - `/dreams` gallery
  - `/admin` admin & scheduler view

## Edge Collector (Raspberry Pi)
- Location: `edge-collector/`
- Configure `BASE_URL`, `PLANT_NICKNAME` (optional) in `config.py`.
- Sends sensor + weight to `/sensor` and `/weight`; captures hourly photos and uploads the **file** via multipart to `/upload_image` (backend stores in Supabase Storage).
- Ignore local artifacts (`edge-collector/photo/`, `edge-collector/logs/`) by default.

## Dev Notes
- CORS enabled in backend for `http://localhost:5173`.
- Tailwind configured with custom dark theme; see `frontend-web/tailwind.config.js`.
- Edge collector (Raspberry Pi) scripts in `edge/` (sensor read, weight, photo capture, upload).
