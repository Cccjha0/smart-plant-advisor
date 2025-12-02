import os
from dotenv import load_dotenv

load_dotenv()

raw_db_url = os.getenv("DB_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_PLANT_BUCKET = os.getenv("SUPABASE_PLANT_BUCKET", "plant-images")
SUPABASE_DREAM_BUCKET = os.getenv("SUPABASE_DREAM_BUCKET", "dream-images")

# Require DB_URL; convert Supabase-style postgres:// to SQLAlchemy format
if not raw_db_url:
    raise RuntimeError("DB_URL is required; SQLite fallback has been removed.")
if raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql+psycopg2://", 1)
DB_URL = raw_db_url
