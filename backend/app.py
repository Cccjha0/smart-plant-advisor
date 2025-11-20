from fastapi import FastAPI
from database import Base, engine
import models
from routers import sensor, image, analysis

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(sensor.router)
app.include_router(image.router)
app.include_router(analysis.router)


@app.get("/")
def root():
    return {"status": "backend ok", "db": "connected"}
