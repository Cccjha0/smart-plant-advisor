from fastapi import FastAPI
from database import Base, engine
import models
from routers import sensor, image, analysis, report, admin, plants, dream, metrics
from services.scheduler import start_scheduler, shutdown_scheduler, run_periodic_llm_and_dream

app = FastAPI()

Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def _start_scheduler():
    start_scheduler()
    # Trigger one immediate full pipeline run on startup
    try:
        run_periodic_llm_and_dream()
    except Exception:
        pass


@app.on_event("shutdown")
def _stop_scheduler():
    shutdown_scheduler()

app.include_router(sensor.router)
app.include_router(image.router)
app.include_router(analysis.router)
app.include_router(report.router)
app.include_router(admin.router)
app.include_router(plants.router)
app.include_router(dream.router)
app.include_router(metrics.router)


@app.get("/")
def root():
    return {"status": "backend ok", "db": "connected"}
