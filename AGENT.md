# AGENT.md – Backend & Cloud Data Platform Agent

## Local development instructions
- Initialize the backend locally **before** any cloud configuration.
- Create the project structure under `backend/` including `app.py`, `routers/`, `models/`, `services/`, and `database.py`.
- Use a virtual environment: `python3 -m venv venv && source venv/bin/activate`.
- Install dependencies:  
  `pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv apscheduler`.
- Run the backend locally with:  
  `uvicorn app:app --reload`.
- Use SQLite locally during early development to simplify testing.
- Verify that all routes (`/sensor`, `/weight`, `/upload_image`) work before cloud deployment.

## Cloud database (Supabase) instructions
- Create a Supabase project and obtain the PostgreSQL connection string.
- Add the DB URL to `.env` as `DB_URL=<your_supabase_connection_string>`.
- Update `config.py` to load `DB_URL` using environment variables.
- Use SQLAlchemy’s `Base.metadata.create_all(bind=engine)` to create tables in Supabase.
- Confirm table creation using Supabase’s SQL Editor or Dashboard.
- All sensor, weight, image, and analysis data must be stored in Supabase from day one.

## Render deployment instructions
- Push the project to GitHub before deployment.
- Create a new **Render Web Service**, connect your repo, and set:
  - Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
  - Environment variable: `DB_URL` (Supabase connection string)
- After deployment, confirm API endpoints work at the public URL.
- Update IoT device scripts to POST to your Render base URL.

## API usage instructions
- `/sensor`: Receives temperature, humidity, light, soil moisture.
- `/weight`: Receives plant weight measurements.
- `/upload_image`: Receives multipart/form-data images (file upload), stores in Supabase Storage.
- `/analysis/{plant_id}`: Aggregates CV + growth + sensor summary.
- `/report/{plant_id}`: Calls the LLM module for bilingual reports.
- `/admin/stats`: Used to verify one-week cloud data existence.

## External module integration instructions
- `cv_service.py` should wrap calls to `external_modules/cv/predictor.py` (if reintroduced); currently vision is handled via LLM stub and Supabase Storage.
- `growth_service.py` should wrap calls to `external_modules/growth/analyzer.py`.
- `llm_service.py` should wrap calls to `external_modules/llm/generate_report.py`.
- All wrappers must expose clean async/sync functions that return structured JSON.
- The backend must not implement ML/AI models—only call the modules.

## Scheduled task instructions
- Use APScheduler as a background scheduler inside FastAPI.
- Add a daily cron job at 02:00:
  - Load latest images
  - Run CV prediction
  - Run growth analysis
  - Summarize sensor data for the past 7 days
  - Generate LLM weekly report
  - Insert records into `analysis_results`
- Ensure the scheduler starts from `app.py` using FastAPI startup events.

## One-week data requirement instructions
- IoT devices must upload data continuously (recommended every 5–10 minutes).
- All data must go directly into Supabase via the Render API.
- Use `/admin/stats` or Supabase SQL queries to verify:
  - Record count ≥ 7 days
  - Earliest timestamp is at least one week old
- Do not rely on local storage for final deliverables—cloud data is required.

## PR / commit tips
- Always run all linting & type checks before pushing.
- Include clear commit messages describing backend changes.
- Avoid committing secrets—always use environment variables.
