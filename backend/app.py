from fastapi import FastAPI
from database import Base, engine
import models
from routers import sensor, image, analysis, report, admin

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(sensor.router)
app.include_router(image.router)
app.include_router(analysis.router)
app.include_router(report.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {"status": "backend ok", "db": "connected"}
