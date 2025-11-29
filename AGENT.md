# AGENT.md — Backend & Cloud Data Platform Agent

## Local development instructions
- Initialize backend locally before any cloud config.
- Create `backend/` structure (`app.py`, `routers/`, `models/`, `services/`, `database.py`).
- Use venv: `python -m venv venv && source venv/bin/activate` (or `venv\Scripts\activate` on Windows).
- Install deps: `pip install -r backend/requirements.txt`.
- Run: `uvicorn app:app --reload` from `backend/`.
- Use SQLite locally; verify `/sensor`, `/weight`, `/upload_image`.

## Cloud database (Supabase)
- Set `DB_URL` in `.env` (Supabase Postgres; `config.py` converts `postgres://`).
- Tables created via `Base.metadata.create_all(bind=engine)`.
- Store sensor, weight, image, analysis data in Supabase from day one.

## Render deployment
- Push to GitHub.
- Render Web Service start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`.
- Env: `DB_URL` (Supabase).
- Update edge device to post to Render base URL.

## API usage
- `/sensor`: temp, humidity, light, soil_moisture.
- `/weight`: weight measurements.
- `/upload_image`: multipart file upload; backend stores in Supabase Storage.
- `/analysis/{plant_id}`: growth + sensor summary.
- `/report/{plant_id}`: LLM report, stores AnalysisResult.
- `/admin/stats`: verify counts/coverage.

## External modules
- `cv_service.py` -> `external_modules/cv/predictor.py` (if reintroduced; currently LLM stub + Supabase storage).
- `growth_service.py` -> `external_modules/growth/analyzer.py`.
- `llm_service.py` -> `external_modules/llm/generate_report.py`.
- Wrappers return structured JSON; backend doesn’t implement models.

## Scheduler
- APScheduler in `services/scheduler.py`.
- Daily 02:00 analysis; every 6h analysis+LLM+dream (uploads to Supabase); startup triggers one full run.
- `schedule_post_watering_job(plant_id, delay_minutes=60)` for one-off.

## One-week data requirement
- Devices upload every 5–10 minutes.
- Data goes to Supabase via API.
- Check `/admin/stats` or SQL: record count ≥7 days; earliest timestamp ≥7 days ago.
- No reliance on local storage for deliverables.

## Edge collector notes
- Folder: `edge-collector/`.
- Configure `BASE_URL`, optional `PLANT_NICKNAME` in `config.py`.
- Sends sensor + weight to `/sensor`/`/weight`; uploads photo files (multipart) to `/upload_image` so backend writes to Supabase Storage.

## PR / commit tips
- Run lint/type checks when available.
- Clear commit messages.
- Never commit secrets; use env vars.
