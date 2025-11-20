from fastapi import FastAPI
from database import Base, engine
import models
from routers import sensor, image

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(sensor.router)
app.include_router(image.router)


@app.get("/")
def root():
    return {"status": "backend ok", "db": "connected"}
