from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
import models
from routers import sensor, image, analysis, report, admin, plants, dream, metrics, alerts, scheduler, images
from services.scheduler import start_scheduler, shutdown_scheduler

app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def _start_scheduler():
    start_scheduler()


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
app.include_router(alerts.router)
app.include_router(scheduler.router)
app.include_router(images.router)


@app.get("/")
def root():
    return {"status": "backend ok", "db": "connected"}
