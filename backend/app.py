from fastapi import FastAPI
from database import Base, engine

app = FastAPI()

# Automatically create tables for SQLite development
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"status": "backend ok", "db": "connected"}
