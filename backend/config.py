import os
from dotenv import load_dotenv

load_dotenv()

raw_db_url = os.getenv("DB_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_PLANT_BUCKET = os.getenv("SUPABASE_PLANT_BUCKET", "plant-images")
SUPABASE_DREAM_BUCKET = os.getenv("SUPABASE_DREAM_BUCKET", "dream-images")

if not raw_db_url:
    # Default to local SQLite for development if no DB_URL is provided
    DB_URL = "sqlite:///./local.db"
else:
    # Support Supabase-style postgres:// URLs by converting to SQLAlchemy format
    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    DB_URL = raw_db_url
