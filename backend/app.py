from fastapi import FastAPI
from database import Base, engine
import models  # ensure models are imported so tables are created

app = FastAPI()

Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"status": "backend ok", "db": "connected"}
